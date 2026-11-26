"""Demo data: 1 course, 1 teacher and some students. Idempotent. Run: `python -m app.db.seed`."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.passwords import hash_password
from app.db.models import (
    Conversation,
    Course,
    Enrollment,
    Message,
    StudentEvent,
    SupportTicket,
    User,
)

DEMO_COURSE_ID = "demo"  # the frontend uses this id (frontend/src/lib/config.ts)
DEMO_PASSWORD = "demo12345"  # development only

TEACHER = ("t1", "Profe Demo", "docente@tutomind.demo", "teacher")
STUDENTS = [
    ("s1", "Ana Torres", "ana@tutomind.demo", "student"),
    ("s2", "Luis Gómez", "luis@tutomind.demo", "student"),
    ("s3", "María Ruiz", "maria@tutomind.demo", "student"),
    ("s4", "Carlos Peña", "carlos@tutomind.demo", "student"),
    ("s5", "Sofía Díaz", "sofia@tutomind.demo", "student"),
]


# Demo activity, as (days ago, kind, value, scale). Gives the dashboard one student per situation:
# s1 green, s2 red (absent, failing, frustrated), s3 yellow, s4 red (no activity), s5 yellow.
_EVENTS = {
    "s1": [(0.3, "login", None, None), (1, "submission", None, None), (2, "submission", None, None),
           (4, "submission", None, None), (6, "grade", 4.5, 5), (12, "grade", 4.2, 5)],
    "s2": [(12, "login", None, None), (10, "grade", 2.0, 5), (20, "grade", 1.8, 5),
           (3, "missed_deadline", None, None), (8, "missed_deadline", None, None),
           (15, "missed_deadline", None, None)],
    "s3": [(5, "login", None, None), (9, "grade", 3.2, 5), (4, "missed_deadline", None, None)],
    "s5": [(6, "login", None, None), (14, "grade", 3.0, 5)],
}  # fmt: skip
# Student questions to the tutor: (days ago, frustration score).
_QUESTIONS = {
    "s1": [(1, 0.0), (2, 0.0), (3, 0.0), (5, 0.0), (7, 0.0), (9, 0.0)],
    "s2": [(11, 0.7), (11.1, 0.8), (12, 0.1)],
    "s3": [(5, 0.0)],
}


def seed_activity(session: Session, now: datetime | None = None) -> None:
    """Demo LMS events and tutor questions so the risk dashboard has something to show.

    Does nothing if the course already has activity (never overwrites real data).
    """
    now = now or datetime.now(UTC)
    existing = session.scalar(
        select(func.count())
        .select_from(StudentEvent)
        .where(StudentEvent.course_id == DEMO_COURSE_ID)
    )
    if existing:
        return
    for user_id, events in _EVENTS.items():
        for days, kind, value, scale in events:
            session.add(
                StudentEvent(
                    course_id=DEMO_COURSE_ID, user_id=user_id, type=kind, value=value,
                    scale=scale, occurred_at=now - timedelta(days=days), source="seed",
                )
            )  # fmt: skip
    for user_id, questions in _QUESTIONS.items():
        conversation = Conversation(
            id=f"seed-{user_id}", course_id=DEMO_COURSE_ID, student_id=user_id
        )
        session.add(conversation)
        session.flush()
        for days, score in questions:
            session.add(
                Message(
                    conversation_id=conversation.id, role="user", content="Consulta de demo",
                    frustration_score=score, created_at=now - timedelta(days=days),
                )
            )  # fmt: skip
    session.add(
        SupportTicket(
            course_id=DEMO_COURSE_ID, student_id="s2", conversation_id="seed-s2",
            reason="persistent_frustration",
        )
    )  # fmt: skip
    session.flush()


def seed(session: Session) -> None:
    """Create the demo records that do not exist yet; never overwrites existing ones."""
    if session.get(Course, DEMO_COURSE_ID) is None:
        session.add(Course(id=DEMO_COURSE_ID, name="Cálculo Diferencial (demo)"))
        session.flush()

    for user_id, name, email, role in [TEACHER, *STUDENTS]:
        if session.get(User, user_id) is None:
            session.add(
                User(
                    id=user_id,
                    name=name,
                    email=email,
                    role=role,
                    password_hash=hash_password(DEMO_PASSWORD),
                )
            )
            session.flush()
        if session.get(Enrollment, (DEMO_COURSE_ID, user_id)) is None:
            session.add(Enrollment(course_id=DEMO_COURSE_ID, user_id=user_id))
    session.flush()
    seed_activity(session)


def main() -> None:
    from app.db.session import get_engine

    with Session(get_engine()) as session:
        seed(session)
        session.commit()
    print("Seed aplicado.")


if __name__ == "__main__":
    main()
