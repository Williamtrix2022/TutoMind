from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.db.models import (
    Conversation,
    Course,
    Document,
    DocumentChunk,
    Message,
    StudentEvent,
    User,
)

DIM = Settings(_env_file=None).embedding_dimensions


def vector(*head: float) -> list[float]:
    """A unit-ish vector of the configured dimension that starts with `head`."""
    return [*head, *([0.0] * (DIM - len(head)))]


def make_course(session) -> Course:
    course = Course(id="c1", name="Cálculo")
    session.add(course)
    session.flush()
    return course


def make_document(session, **overrides) -> Document:
    values = {
        "id": "d1",
        "course_id": "c1",
        "filename": "a.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 10,
    }
    document = Document(**{**values, **overrides})
    session.add(document)
    session.flush()
    return document


def test_new_document_defaults_to_queued(session):
    make_course(session)

    document = make_document(session)
    session.refresh(document)

    assert document.status == "queued"
    assert document.created_at is not None


def test_email_is_unique(session):
    session.add(User(id="u1", name="A", email="a@x.edu", password_hash="h", role="student"))
    session.flush()
    session.add(User(id="u2", name="B", email="a@x.edu", password_hash="h", role="student"))

    with pytest.raises(IntegrityError):
        session.flush()


def test_role_outside_the_contract_is_rejected(session):
    session.add(User(id="u1", name="A", email="a@x.edu", password_hash="h", role="admin"))

    with pytest.raises(IntegrityError):
        session.flush()


def test_document_with_unsupported_mime_is_rejected(session):
    make_course(session)

    with pytest.raises(IntegrityError):
        make_document(session, mime_type="text/plain")


def test_negative_size_is_rejected(session):
    make_course(session)

    with pytest.raises(IntegrityError):
        make_document(session, size_bytes=-1)


def test_deleting_a_document_deletes_its_chunks(session):
    make_course(session)
    document = make_document(session)
    session.add(
        DocumentChunk(
            document_id=document.id, course_id="c1", chunk_index=0,
            content="texto", embedding=vector(1.0),
        )
    )  # fmt: skip
    session.flush()

    session.delete(document)
    session.flush()

    assert session.scalars(select(DocumentChunk)).all() == []


def test_nearest_chunk_by_cosine_distance_comes_first(session):
    """The retrieval primitive for RAG: closest embedding within one course."""
    make_course(session)
    session.add(Course(id="c2", name="Otro"))
    make_document(session)
    make_document(session, id="d2", course_id="c2", filename="b.pdf")
    chunks = [
        ("d1", "c1", 0, "derivadas", vector(1.0, 0.0)),
        ("d1", "c1", 1, "integrales", vector(0.0, 1.0)),
        ("d2", "c2", 0, "otro curso", vector(1.0, 0.0)),
    ]
    for document_id, course_id, index, content, embedding in chunks:
        session.add(
            DocumentChunk(
                document_id=document_id, course_id=course_id, chunk_index=index,
                content=content, embedding=embedding,
            )
        )  # fmt: skip
    session.flush()

    nearest = session.scalars(
        select(DocumentChunk)
        .where(DocumentChunk.course_id == "c1")
        .order_by(DocumentChunk.embedding.cosine_distance(vector(0.9, 0.1)))
        .limit(2)
    ).all()

    assert [c.content for c in nearest] == ["derivadas", "integrales"]


def test_chunk_index_is_unique_per_document(session):
    make_course(session)
    make_document(session)
    session.add(
        DocumentChunk(
            document_id="d1", course_id="c1", chunk_index=0,
            content="a", embedding=vector(1.0),
        )
    )  # fmt: skip
    session.flush()
    session.add(
        DocumentChunk(
            document_id="d1", course_id="c1", chunk_index=0,
            content="b", embedding=vector(1.0),
        )
    )  # fmt: skip

    with pytest.raises(IntegrityError):
        session.flush()


def test_unknown_event_type_is_rejected(session):
    make_course(session)
    session.add(User(id="s1", name="A", email="a@x.edu", password_hash="h", role="student"))
    session.flush()
    session.add(
        StudentEvent(course_id="c1", user_id="s1", type="teleport", occurred_at=datetime.now(UTC))
    )

    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize("score", [-0.1, 1.5])
def test_frustration_score_must_be_between_0_and_1(session, score):
    make_course(session)
    session.add(User(id="s1", name="A", email="a@x.edu", password_hash="h", role="student"))
    session.flush()
    session.add(Conversation(id="conv", course_id="c1", student_id="s1"))
    session.flush()
    session.add(Message(conversation_id="conv", role="user", content="x", frustration_score=score))

    with pytest.raises(IntegrityError):
        session.flush()
