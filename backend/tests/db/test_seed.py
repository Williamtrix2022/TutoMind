from sqlalchemy import func, select

from app.core.passwords import verify_password
from app.db.models import Course, Enrollment, User
from app.db.seed import DEMO_COURSE_ID, DEMO_PASSWORD, seed


def users_with(session, role):
    return session.scalars(select(User).where(User.role == role)).all()


def test_seed_creates_one_course_one_teacher_and_students(session):
    seed(session)

    assert [c.id for c in session.scalars(select(Course)).all()] == [DEMO_COURSE_ID]
    assert len(users_with(session, "teacher")) == 1
    assert len(users_with(session, "student")) >= 3


def test_everyone_is_enrolled_in_the_demo_course(session):
    seed(session)

    enrolled = session.scalar(select(func.count()).select_from(Enrollment))
    users = session.scalar(select(func.count()).select_from(User))
    assert enrolled == users


def test_seed_is_idempotent(session):
    seed(session)
    first = session.scalar(select(func.count()).select_from(User))

    seed(session)

    assert session.scalar(select(func.count()).select_from(User)) == first
    assert session.scalar(select(func.count()).select_from(Enrollment)) == first


def test_seeded_users_can_log_in_with_the_demo_password(session):
    seed(session)

    teacher = users_with(session, "teacher")[0]

    assert teacher.password_hash != DEMO_PASSWORD
    assert verify_password(DEMO_PASSWORD, teacher.password_hash)
