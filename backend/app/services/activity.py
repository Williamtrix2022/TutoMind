"""Collects what is known about each student of a course, for the risk model.

A fixed number of grouped queries, whatever the class size (no per-student queries).
"""

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Enrollment, Message, StudentEvent, SupportTicket, User
from app.services.frustration import DETECTION_THRESHOLD
from app.services.risk import Grade, StudentActivity

GRADES_WINDOW = timedelta(days=90)
WORK_WINDOW = timedelta(days=30)
TUTOR_WINDOW = timedelta(days=14)
_ACTIVITY_EVENTS = ("login", "submission")  # grades and missed deadlines are not the student acting


def _later(a: datetime | None, b: datetime | None) -> datetime | None:
    return max((d for d in (a, b) if d is not None), default=None)


def load_activity(session: Session, course_id: str, now: datetime) -> list[StudentActivity]:
    students = session.execute(
        select(User.id, User.name)
        .join(Enrollment, Enrollment.user_id == User.id)
        .where(Enrollment.course_id == course_id, User.role == "student")
        .order_by(User.name, User.id)
    ).all()
    if not students:
        return []

    last_event = dict(
        session.execute(
            select(StudentEvent.user_id, func.max(StudentEvent.occurred_at))
            .where(StudentEvent.course_id == course_id, StudentEvent.type.in_(_ACTIVITY_EVENTS))
            .group_by(StudentEvent.user_id)
        ).all()
    )

    grades: dict[str, list[Grade]] = defaultdict(list)
    for user_id, value, scale in session.execute(
        select(StudentEvent.user_id, StudentEvent.value, StudentEvent.scale).where(
            StudentEvent.course_id == course_id,
            StudentEvent.type == "grade",
            StudentEvent.value.is_not(None),
            StudentEvent.scale.is_not(None),
            StudentEvent.occurred_at >= now - GRADES_WINDOW,
        )
    ):
        grades[user_id].append(Grade(value=value, scale=scale))

    work: dict[tuple[str, str], int] = {
        (user_id, kind): count
        for user_id, kind, count in session.execute(
            select(StudentEvent.user_id, StudentEvent.type, func.count())
            .where(
                StudentEvent.course_id == course_id,
                StudentEvent.type.in_(("missed_deadline", "submission")),
                StudentEvent.occurred_at >= now - WORK_WINDOW,
            )
            .group_by(StudentEvent.user_id, StudentEvent.type)
        )
    }

    tutor_window_start = now - TUTOR_WINDOW
    in_window = Message.created_at >= tutor_window_start
    tutor = {
        row.student_id: row
        for row in session.execute(
            select(
                Conversation.student_id,
                func.max(Message.created_at).label("last_message"),
                func.count().filter(in_window).label("questions"),
                func.count(Message.frustration_score).filter(in_window).label("scored"),
                func.sum(case((Message.frustration_score >= DETECTION_THRESHOLD, 1), else_=0))
                .filter(in_window)
                .label("frustrated"),
            )
            .join(Message, Message.conversation_id == Conversation.id)
            .where(Conversation.course_id == course_id, Message.role == "user")
            .group_by(Conversation.student_id)
        )
    }

    tickets = dict(
        session.execute(
            select(SupportTicket.student_id, func.count())
            .where(SupportTicket.course_id == course_id, SupportTicket.status == "open")
            .group_by(SupportTicket.student_id)
        ).all()
    )

    activities = []
    for user_id, name in students:
        row = tutor.get(user_id)
        activities.append(
            StudentActivity(
                student_id=user_id,
                name=name,
                last_activity_at=_later(last_event.get(user_id), row.last_message if row else None),
                grades=grades.get(user_id, []),
                missed_deadlines=work.get((user_id, "missed_deadline"), 0),
                submissions=work.get((user_id, "submission"), 0),
                questions=int(row.questions or 0) if row else 0,
                scored_messages=int(row.scored or 0) if row else 0,
                frustrated_messages=int(row.frustrated or 0) if row else 0,
                open_tickets=tickets.get(user_id, 0),
            )
        )
    return activities
