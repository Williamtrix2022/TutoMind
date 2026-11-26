import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.models import Conversation, Course, SupportTicket, User
from app.services.tickets import open_ticket


@pytest.fixture
def setup(session):
    session.add(Course(id="c1", name="Cálculo"))
    session.add(User(id="s1", name="Ana", email="a@x.edu", password_hash="h", role="student"))
    session.flush()
    session.add(Conversation(id="conv1", course_id="c1", student_id="s1"))
    session.flush()


def count(session) -> int:
    return session.scalar(select(func.count()).select_from(SupportTicket))


def test_ticket_is_created_open(session, setup):
    ticket = open_ticket(session, "c1", "s1", "conv1", "student_requested")

    assert ticket.status == "open"
    assert ticket.reason == "student_requested"
    assert ticket.created_at is not None
    assert count(session) == 1


def test_same_conversation_and_reason_reuses_the_open_ticket(session, setup):
    first = open_ticket(session, "c1", "s1", "conv1", "persistent_frustration")

    again = open_ticket(session, "c1", "s1", "conv1", "persistent_frustration")

    assert again.id == first.id
    assert count(session) == 1


def test_a_different_reason_is_a_different_ticket(session, setup):
    open_ticket(session, "c1", "s1", "conv1", "persistent_frustration")

    open_ticket(session, "c1", "s1", "conv1", "student_requested")

    assert count(session) == 2


def test_a_resolved_ticket_does_not_block_a_new_one(session, setup):
    first = open_ticket(session, "c1", "s1", "conv1", "student_requested")
    first.status = "resolved"
    session.flush()

    second = open_ticket(session, "c1", "s1", "conv1", "student_requested")

    assert second.id != first.id


def test_reason_outside_the_contract_is_rejected(session, setup):
    with pytest.raises(IntegrityError):
        open_ticket(session, "c1", "s1", "conv1", "because")
