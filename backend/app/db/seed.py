"""Demo data: 1 course, 1 teacher and some students. Idempotent. Run: `python -m app.db.seed`."""

from sqlalchemy.orm import Session

from app.core.passwords import hash_password
from app.db.models import Course, Enrollment, User

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


def main() -> None:
    from app.db.session import get_engine

    with Session(get_engine()) as session:
        seed(session)
        session.commit()
    print("Seed aplicado.")


if __name__ == "__main__":
    main()
