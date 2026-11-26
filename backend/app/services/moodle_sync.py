"""Ingest Moodle (or simulated) events into `student_events`, which feed the risk model.

Run it by hand or from cron:  `python -m app.services.moodle_sync <course_id>`
It is idempotent: a unique index on (course, student, type, moment, source) makes re-running safe.
Simulated data is the exception by design: each run replaces the previous simulated snapshot.
"""

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import Course, Enrollment, StudentEvent, User
from app.services.moodle import MoodleClient, MoodleError, get_moodle_client


class UnknownCourseError(Exception):
    pass


@dataclass(frozen=True)
class SyncResult:
    received: int  # events the client returned
    inserted: int
    duplicates: int  # already stored
    unknown_users: int  # distinct emails that match no student enrolled in the course
    source: str


def sync_course(
    session: Session, client: MoodleClient, course_id: str, now: datetime
) -> SyncResult:
    if session.get(Course, course_id) is None:
        raise UnknownCourseError(course_id)

    source = getattr(client, "source", "moodle")
    events = client.fetch_events(course_id, now)
    if source == "simulated":
        # Simulated data is dated relative to "now", so each run is a fresh snapshot: replace the
        # previous one instead of piling up (which would inflate, say, missed deadlines). Real
        # Moodle data is never touched.
        session.execute(
            delete(StudentEvent).where(
                StudentEvent.course_id == course_id, StudentEvent.source == "simulated"
            )
        )
    students = {
        email.lower(): user_id
        for user_id, email in session.execute(
            select(User.id, User.email)
            .join(Enrollment, Enrollment.user_id == User.id)
            .where(Enrollment.course_id == course_id, User.role == "student")
        )
    }

    rows, unknown = [], set()
    for event in events:
        user_id = students.get(event.email.lower())
        if user_id is None:
            unknown.add(event.email.lower())
            continue
        rows.append(
            {
                "course_id": course_id,
                "user_id": user_id,
                "type": event.type,
                "value": event.value,
                "scale": event.scale,
                "occurred_at": event.occurred_at,
                "source": event.source,
            }
        )

    inserted = 0
    if rows:
        statement = (
            insert(StudentEvent)
            .values(rows)
            .on_conflict_do_nothing(
                index_elements=["course_id", "user_id", "type", "occurred_at", "source"]
            )
            .returning(StudentEvent.id)
        )
        inserted = len(session.execute(statement).all())
    session.flush()
    return SyncResult(
        received=len(events),
        inserted=inserted,
        duplicates=len(rows) - inserted,
        unknown_users=len(unknown),
        source=source,
    )


def run_sync(session: Session, settings: Settings, course_id: str, now: datetime) -> SyncResult:
    return sync_course(session, get_moodle_client(settings), course_id, now)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync Moodle activity into TutoMind.")
    parser.add_argument("course_id", help="Course id (the Moodle course id, or `demo`).")
    args = parser.parse_args(argv)

    from app.db.session import get_session_factory

    settings = get_settings()
    try:
        client = get_moodle_client(settings)
        if client.source == "simulated":
            print(
                "AVISO: Moodle no está configurado (MOODLE_BASE_URL / MOODLE_TOKEN): "
                "se usan datos SIMULADOS de demostración.",
                file=sys.stderr,
            )
        with get_session_factory()() as session:
            result = sync_course(session, client, args.course_id, datetime.now(UTC))
            session.commit()
    except (MoodleError, UnknownCourseError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(
        f"[{result.source}] recibidos={result.received} nuevos={result.inserted} "
        f"repetidos={result.duplicates} usuarios_desconocidos={result.unknown_users}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
