from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, new_id

ROLES = ("student", "teacher")
DOCUMENT_STATUSES = ("queued", "processing", "indexed", "failed")
MIME_TYPES = (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
)
MESSAGE_ROLES = ("user", "assistant")
TICKET_REASONS = ("student_requested", "persistent_frustration", "repeated_failure")
TICKET_STATUSES = ("open", "resolved")
EVENT_TYPES = ("login", "grade", "submission", "missed_deadline")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint(_in("role", ROLES), name="ck_users_role"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = _created_at()


class Course(Base):
    __tablename__ = "courses"

    # Matches the Moodle course id used in the API path (`/courses/{course_id}`).
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = _created_at()


class Enrollment(Base):
    """Who belongs to a course: students and its teacher."""

    __tablename__ = "enrollments"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(_in("status", DOCUMENT_STATUSES), name="ck_documents_status"),
        CheckConstraint(_in("mime_type", MIME_TYPES), name="ck_documents_mime_type"),
        CheckConstraint("size_bytes >= 0", name="ck_documents_size_bytes"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(200))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20), default="queued", server_default="queued")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_index"),
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    # Denormalised so retrieval can filter by course without joining.
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(get_settings().embedding_dimensions))

    document: Mapped[Document] = relationship(back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = _created_at()


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(_in("role", MESSAGE_ROLES), name="ck_messages_role"),
        CheckConstraint(
            "frustration_score IS NULL OR (frustration_score >= 0 AND frustration_score <= 1)",
            name="ck_messages_frustration_score",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    # Frustration of a student message (0-1); NULL for tutor replies and older messages.
    frustration_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = _created_at()


class SupportTicket(Base):
    """A request for the teacher's help, raised from a tutor conversation."""

    __tablename__ = "support_tickets"
    __table_args__ = (
        CheckConstraint(_in("reason", TICKET_REASONS), name="ck_tickets_reason"),
        CheckConstraint(_in("status", TICKET_STATUSES), name="ck_tickets_status"),
        # One open ticket per conversation and reason, even under concurrent requests.
        Index(
            "uq_tickets_open_per_conversation_reason",
            "conversation_id",
            "reason",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="open", server_default="open")
    created_at: Mapped[datetime] = _created_at()


class StudentEvent(Base):
    """Activity of a student in the LMS (Moodle): logins, grades, submissions, missed deadlines.

    Feeds the risk model. For `grade`, `value` is the mark and `scale` its maximum.
    """

    __tablename__ = "student_events"
    __table_args__ = (
        CheckConstraint(_in("type", EVENT_TYPES), name="ck_student_events_type"),
        CheckConstraint("scale IS NULL OR scale > 0", name="ck_student_events_scale"),
        Index("ix_student_events_course_user_time", "course_id", "user_id", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(30))
    value: Mapped[float | None] = mapped_column(Float)
    scale: Mapped[float | None] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(20), default="moodle", server_default="moodle")
