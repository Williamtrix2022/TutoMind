"""Support tickets raised from tutor conversations (human escalation).

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def upgrade() -> None:
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "course_id", sa.String(64), sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id", sa.String(32),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            _in("reason", ("student_requested", "persistent_frustration", "repeated_failure")),
            name="ck_tickets_reason",
        ),
        sa.CheckConstraint(_in("status", ("open", "resolved")), name="ck_tickets_status"),
    )  # fmt: skip
    op.create_index("ix_support_tickets_course_id", "support_tickets", ["course_id"])
    op.create_index("ix_support_tickets_student_id", "support_tickets", ["student_id"])
    op.create_index("ix_support_tickets_conversation_id", "support_tickets", ["conversation_id"])
    op.create_index(
        "uq_tickets_open_per_conversation_reason",
        "support_tickets",
        ["conversation_id", "reason"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade() -> None:
    op.drop_table("support_tickets")
