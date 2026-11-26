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
from app.services.moodle import SimulatedMoodleClient
from app.services.moodle_sync import sync_course

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


# Student questions to the tutor: (days ago, frustration score, topic). Within 7 days they feed the
# classroom thermometer (one alert: Derivadas); older ones only count towards the risk model.
_QUESTIONS = {
    "s1": [(1, 0.0, "Derivadas"), (2, 0.0, "Derivadas"), (3, 0.0, "Límites"),
           (5, 0.0, "Integrales"), (8, 0.0, "Derivadas"), (9, 0.0, "Límites")],
    "s2": [(1, 0.8, "Derivadas"), (1.1, 0.7, "Derivadas"), (11, 0.7, "Derivadas"),
           (11.1, 0.8, "Derivadas"), (12, 0.1, "Derivadas")],
    "s3": [(3, 0.6, "Derivadas"), (5, 0.0, "Límites")],
    "s5": [(2, 0.5, "Integrales"), (4, 0.0, "Integrales")],
}  # fmt: skip


def _demo_question(topic: str, score: float) -> str:
    if score >= 0.5:
        return f"No entiendo {topic.lower()}, ¿me ayudas?"
    return f"¿Puedes explicarme {topic.lower()}?"


def seed_activity(session: Session, now: datetime | None = None) -> None:
    """Demo LMS events (simulated Moodle) and tutor questions, so the dashboards have data.

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
    # LMS events arrive through the real ingestion pipeline, from the simulated Moodle.
    sync_course(session, SimulatedMoodleClient(), DEMO_COURSE_ID, now)
    for user_id, questions in _QUESTIONS.items():
        conversation = Conversation(
            id=f"seed-{user_id}", course_id=DEMO_COURSE_ID, student_id=user_id
        )
        session.add(conversation)
        session.flush()
        for days, score, topic in questions:
            session.add(
                Message(
                    conversation_id=conversation.id, role="user",
                    content=_demo_question(topic, score), topic=topic,
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
