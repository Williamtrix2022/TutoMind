"""Moodle: link of each document, and one row per (event, source) so syncs are re-runnable.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("moodle_url", sa.String(500)))
    # Keep the oldest of any repeated event before the unique index is created.
    op.execute(
        """
        DELETE FROM student_events a
        USING student_events b
        WHERE a.id > b.id
          AND a.course_id = b.course_id AND a.user_id = b.user_id AND a.type = b.type
          AND a.occurred_at = b.occurred_at AND a.source = b.source
        """
    )
    op.create_index(
        "uq_student_events_dedupe",
        "student_events",
        ["course_id", "user_id", "type", "occurred_at", "source"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_student_events_dedupe", table_name="student_events")
    op.drop_column("documents", "moodle_url")
