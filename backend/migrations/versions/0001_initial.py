"""Initial schema: users, courses, documents, chunks (pgvector) and conversations.

Revision ID: 0001
Revises:
"""

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# A migration is a frozen snapshot: it must not read the application settings.
EMBEDDING_DIMENSIONS = 1024

MIME_TYPES = (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
)


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        _created_at(),
        sa.CheckConstraint(_in("role", ("student", "teacher")), name="ck_users_role"),
    )
    op.create_table(
        "courses",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        _created_at(),
    )
    op.create_table(
        "enrollments",
        sa.Column(
            "course_id", sa.String(64), sa.ForeignKey("courses.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )  # fmt: skip
    op.create_table(
        "documents",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "course_id", sa.String(64), sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("error_message", sa.Text),
        _created_at(),
        sa.CheckConstraint(
            _in("status", ("queued", "processing", "indexed", "failed")),
            name="ck_documents_status",
        ),
        sa.CheckConstraint(_in("mime_type", MIME_TYPES), name="ck_documents_mime_type"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_documents_size_bytes"),
    )  # fmt: skip
    op.create_index("ix_documents_course_id", "documents", ["course_id"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "document_id", sa.String(32), sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id", sa.String(64), sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("page", sa.Integer),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "embedding", pgvector.sqlalchemy.Vector(EMBEDDING_DIMENSIONS), nullable=False
        ),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_index"),
    )  # fmt: skip
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_course_id", "document_chunks", ["course_id"])
    op.create_index(
        "ix_document_chunks_embedding_hnsw",
        "document_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "course_id", sa.String(64), sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        _created_at(),
    )  # fmt: skip
    op.create_index("ix_conversations_course_id", "conversations", ["course_id"])
    op.create_index("ix_conversations_student_id", "conversations", ["student_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id", sa.String(32),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        _created_at(),
        sa.CheckConstraint(_in("role", ("user", "assistant")), name="ck_messages_role"),
    )  # fmt: skip
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    for table in (
        "messages",
        "conversations",
        "document_chunks",
        "documents",
        "enrollments",
        "courses",
        "users",
    ):
        op.drop_table(table)
    op.execute("DROP EXTENSION IF EXISTS vector")
