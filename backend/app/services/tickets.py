"""Support tickets: a student asks (or is flagged) for help from the teacher."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import SupportTicket


def _open_ticket_for(session: Session, conversation_id: str, reason: str) -> SupportTicket | None:
    return session.scalar(
        select(SupportTicket).where(
            SupportTicket.conversation_id == conversation_id,
            SupportTicket.reason == reason,
            SupportTicket.status == "open",
        )
    )


def open_ticket(
    session: Session, course_id: str, student_id: str, conversation_id: str, reason: str
) -> SupportTicket:
    """Create a ticket, or return the one already open for this conversation and reason.

    A partial unique index backs this up, so two simultaneous requests cannot both create one.
    """
    existing = _open_ticket_for(session, conversation_id, reason)
    if existing is not None:
        return existing
    ticket = SupportTicket(
        course_id=course_id, student_id=student_id, conversation_id=conversation_id, reason=reason
    )
    try:
        with session.begin_nested():
            session.add(ticket)
    except IntegrityError:
        winner = _open_ticket_for(session, conversation_id, reason)
        if winner is None:  # not a race: the data itself is invalid (e.g. unknown reason)
            raise
        return winner
    return ticket
