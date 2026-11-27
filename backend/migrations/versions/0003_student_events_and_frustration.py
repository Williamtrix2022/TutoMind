"""Student activity events (risk model input) and per-message frustration score.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("frustration_score", sa.Float))
    op.create_check_constraint(
        "ck_messages_frustration_score",
        "messages",
        "frustration_score IS NULL OR (frustration_score >= 0 AND frustration_score <= 1)",
    )
    op.create_table(
        "student_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "course_id", sa.String(64), sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("value", sa.Float),
        sa.Column("scale", sa.Float),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="moodle"),
        sa.CheckConstraint(
            "type IN ('login', 'grade', 'submission', 'missed_deadline')",
            name="ck_student_events_type",
        ),
        sa.CheckConstraint("scale IS NULL OR scale > 0", name="ck_student_events_scale"),
    )  # fmt: skip
    op.create_index(
        "ix_student_events_course_user_time",
        "student_events",
        ["course_id", "user_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("student_events")
    op.drop_constraint("ck_messages_frustration_score", "messages", type_="check")
    op.drop_column("messages", "frustration_score")
