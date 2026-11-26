"""One tutor turn: persist the question, retrieve material, assess frustration, build the prompt.

`prepare_turn` is synchronous database work done before streaming starts; `stream_events` is the
async generator that turns the model's output into contract `TutorStreamEvent`s.
"""

import json
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.errors import ApiError
from app.db.models import Conversation, Message, User
from app.db.session import SessionFactory
from app.schemas import (
    DoneEvent,
    ErrorEvent,
    EscalationEvent,
    EscalationSignal,
    FrustrationEvent,
    SourceCitation,
    SourcesEvent,
    TokenEvent,
    TutorChatRequest,
)
from app.services.frustration import Assessment, assess
from app.services.llm import LLMClient
from app.services.retrieval import RetrievedChunk, retrieve_chunks
from app.services.tickets import open_ticket
from app.services.topics import topic_for
from app.services.tutor_prompt import (
    asks_for_full_solution,
    build_prompt,
    build_system_prompt,
)

logger = logging.getLogger(__name__)

MAX_MESSAGES = 40
MAX_MESSAGE_CHARS = 8000
HUMAN_HELP_REPLY = (
    "Listo, avisé a tu docente. Mientras tanto, puedo seguir contigo con un ejemplo más sencillo."
)
LLM_ERROR_MESSAGE = "No pude generar la respuesta. Inténtalo de nuevo."


@dataclass(frozen=True)
class Turn:
    conversation_id: str
    chunks: list[RetrievedChunk]
    assessment: Assessment
    ticket_id: str | None
    prompt: str
    system: str

    @property
    def canned_reply(self) -> str | None:
        """A human was asked for: acknowledge it without spending a model call."""
        return (
            HUMAN_HELP_REPLY if self.assessment.escalation_reason == "student_requested" else None
        )


def validate_request(body: TutorChatRequest) -> str:
    """Return the student's current question or raise a 422. Cheap checks first."""
    if len(body.messages) > MAX_MESSAGES:
        raise ApiError(422, "invalid_request", f"Demasiados mensajes (máximo {MAX_MESSAGES}).")
    if any(len(m.content) > MAX_MESSAGE_CHARS for m in body.messages):
        raise ApiError(
            422, "invalid_request", f"Un mensaje supera los {MAX_MESSAGE_CHARS} caracteres."
        )
    if body.messages[-1].role != "user":
        raise ApiError(422, "invalid_request", "El último mensaje debe ser del estudiante.")
    return body.messages[-1].content


def _conversation_for(session: Session, user: User, body: TutorChatRequest) -> Conversation:
    if body.conversation_id is None:
        conversation = Conversation(course_id=body.course_id, student_id=user.id)
        session.add(conversation)
        session.flush()
        return conversation
    conversation = session.get(Conversation, body.conversation_id)
    # Same answer for "missing" and "someone else's": never confirm that an id exists.
    if conversation is None or (conversation.student_id, conversation.course_id) != (
        user.id,
        body.course_id,
    ):
        raise ApiError(404, "not_found", "La conversación no existe.")
    return conversation


def prepare_turn(
    session: Session, user: User, body: TutorChatRequest, query_vector: list[float] | None
) -> Turn:
    question = body.messages[-1].content
    conversation = _conversation_for(session, user, body)
    assessment = assess(body.messages, body.request_human_help)
    chunks = (
        retrieve_chunks(session, body.course_id, query_vector) if query_vector is not None else []
    )
    session.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=question,
            frustration_score=assessment.frustration.score,
            # Asking for a human is not a subject of study; so is a question we could not search.
            topic=topic_for(question, chunks) if query_vector is not None else None,
        )
    )

    ticket_id = None
    if assessment.escalation_reason is not None:
        ticket = open_ticket(
            session, body.course_id, user.id, conversation.id, assessment.escalation_reason
        )
        ticket_id = ticket.id

    system = build_system_prompt(
        level=body.student_level.value,
        chunks=chunks,
        empathetic=bool(assessment.frustration.adapted_tone),
        solution_requested=asks_for_full_solution(question),
    )
    session.commit()
    return Turn(
        conversation_id=conversation.id,
        chunks=chunks,
        assessment=assessment,
        ticket_id=ticket_id,
        prompt=build_prompt(body.messages),
        system=system,
    )


def _save_reply(session_factory: SessionFactory, conversation_id: str, reply: str) -> None:
    with session_factory() as session:
        session.add(Message(conversation_id=conversation_id, role="assistant", content=reply))
        session.commit()


def _frame(event: BaseModel) -> str:
    # Optional fields the contract does not declare nullable must be absent, not `null`.
    return f"data: {json.dumps(event.model_dump(mode='json', exclude_none=True))}\n\n"


def _words(text: str) -> list[str]:
    return [piece for piece in re.split(r"(\s+)", text) if piece]


async def stream_events(
    turn: Turn, llm: LLMClient, session_factory: SessionFactory
) -> AsyncIterator[str]:
    frustration = turn.assessment.frustration
    if frustration.detected:
        yield _frame(FrustrationEvent(type="frustration", frustration=frustration))

    pieces: list[str] = []
    try:
        source: AsyncIterator[str] | list[str]
        source = (
            _words(turn.canned_reply)
            if turn.canned_reply is not None
            else llm.generate_stream(turn.prompt, system=turn.system)
        )
        if isinstance(source, list):
            for piece in source:
                pieces.append(piece)
                yield _frame(TokenEvent(type="token", content=piece))
        else:
            async for piece in source:
                pieces.append(piece)
                yield _frame(TokenEvent(type="token", content=piece))
    except Exception:
        # The provider's message may contain keys or internals: log it, never send it.
        logger.exception("Tutor generation failed")
        yield _frame(ErrorEvent(type="error", code="llm_error", message=LLM_ERROR_MESSAGE))
        return

    await run_in_threadpool(_save_reply, session_factory, turn.conversation_id, "".join(pieces))

    if turn.chunks:
        cited: dict[str, SourceCitation] = {}
        for chunk in turn.chunks:
            cited.setdefault(
                chunk.document_id,
                SourceCitation(document_id=chunk.document_id, title=chunk.title, page=chunk.page),
            )
        yield _frame(SourcesEvent(type="sources", sources=list(cited.values())))

    reason: Literal["student_requested", "persistent_frustration"] | None
    reason = turn.assessment.escalation_reason
    if reason is not None:
        signal = EscalationSignal(suggested=True, reason=reason, ticket_id=turn.ticket_id)
        yield _frame(EscalationEvent(type="escalation", escalation=signal))

    yield _frame(DoneEvent(type="done", conversation_id=turn.conversation_id))
