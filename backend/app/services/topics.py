"""Topics students ask about, and how confused the class is about each one.

Topic of a question: the *title of the course material that talks about it* (the nearest retrieved
chunk that really shares vocabulary with the question), or "Otros temas" when nothing does. It is
coarse on purpose (one document = one topic), free, and needs no model; the extraction sits behind
`topic_for`, so a finer one (for example with Gemini) can replace it later.

Confusion of a topic, from 0 to 1:

    confusion_score = 0.6 * (frustrated questions / questions)
                    + 0.4 * (students who asked more than once / students who asked)

A topic raises an **alert** when `confusion_score >= 0.5` and it has at least 3 questions (one
upset student is not group confusion). Window: the last 7 days. Both numbers are a first
calibration to adjust with real classes.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message
from app.schemas import TopicStat
from app.services.embeddings import tokenize
from app.services.frustration import DETECTION_THRESHOLD
from app.services.retrieval import RetrievedChunk

OTHER_TOPIC = "Otros temas"
WINDOW = timedelta(days=7)
MAX_QUESTIONS_LOADED = 5000
MIN_QUESTIONS_FOR_ALERT = 3
ALERT_THRESHOLD = 0.5
FRUSTRATION_WEIGHT = 0.6
REPEAT_WEIGHT = 0.4
MAX_SAMPLES = 3
SAMPLE_CHARS = 200
_MIN_SHARED_WORD = 4  # ignore tiny words when deciding that a chunk "talks about" the question
_FILE_EXTENSION = re.compile(r"\.(pdf|docx|pptx)$", re.IGNORECASE)


@dataclass(frozen=True)
class TopicQuestion:
    student_id: str
    topic: str
    content: str
    score: float | None  # frustration score of the question, if it was measured
    asked_at: datetime


def _clean_title(title: str) -> str:
    return _FILE_EXTENSION.sub("", title).strip()[:120] or OTHER_TOPIC


def _stem(word: str) -> str:
    """Spanish plural to singular ("funciones" -> "funcion", "derivadas" -> "derivada")."""
    if word.endswith("es") and len(word) > 5:
        return word[:-2]
    if word.endswith("s") and len(word) > 4:
        return word[:-1]
    return word


def _vocabulary(text: str) -> set[str]:
    return {_stem(t) for t in tokenize(text) if len(t) >= _MIN_SHARED_WORD}


def topic_for(question: str, chunks: list[RetrievedChunk]) -> str:
    asked = _vocabulary(question)
    for chunk in chunks:  # nearest first
        if asked & _vocabulary(chunk.content):
            return _clean_title(chunk.title)
    return OTHER_TOPIC


def _is_frustrated(question: TopicQuestion) -> bool:
    return question.score is not None and question.score >= DETECTION_THRESHOLD


def _samples(questions: list[TopicQuestion]) -> list[str]:
    # Frustrated ones first (what the teacher most needs to read), newest first within each group.
    ordered = sorted(questions, key=lambda q: (not _is_frustrated(q), -q.asked_at.timestamp()))
    samples: list[str] = []
    for question in ordered:
        text = question.content.strip()[:SAMPLE_CHARS]
        if text and text not in samples:
            samples.append(text)
        if len(samples) == MAX_SAMPLES:
            break
    return samples


def compute_topics(questions: list[TopicQuestion]) -> list[TopicStat]:
    by_topic: dict[str, list[TopicQuestion]] = {}
    for question in questions:
        by_topic.setdefault(question.topic, []).append(question)

    stats = []
    for topic, items in by_topic.items():
        per_student: dict[str, int] = {}
        for item in items:
            per_student[item.student_id] = per_student.get(item.student_id, 0) + 1
        frustrated_ratio = sum(_is_frustrated(i) for i in items) / len(items)
        repeat_ratio = sum(n > 1 for n in per_student.values()) / len(per_student)
        score = round(
            min(1.0, FRUSTRATION_WEIGHT * frustrated_ratio + REPEAT_WEIGHT * repeat_ratio), 4
        )
        stats.append(
            TopicStat(
                topic=topic,
                question_count=len(items),
                unique_students=len(per_student),
                confusion_score=score,
                confusion_alert=len(items) >= MIN_QUESTIONS_FOR_ALERT and score >= ALERT_THRESHOLD,
                sample_questions=_samples(items),
            )
        )
    stats.sort(
        key=lambda s: (not s.confusion_alert, -s.confusion_score, -s.question_count, s.topic)
    )
    return stats


def load_topic_questions(session: Session, course_id: str, now: datetime) -> list[TopicQuestion]:
    """Student questions of the last `WINDOW` that were assigned a topic (newest first)."""
    rows = session.execute(
        select(
            Conversation.student_id,
            Message.topic,
            Message.content,
            Message.frustration_score,
            Message.created_at,
        )
        .join(Message, Message.conversation_id == Conversation.id)
        .where(
            Conversation.course_id == course_id,
            Message.role == "user",
            Message.topic.is_not(None),
            Message.created_at >= now - WINDOW,
        )
        .order_by(Message.created_at.desc())
        .limit(MAX_QUESTIONS_LOADED)
    ).all()
    return [TopicQuestion(*row) for row in rows]
