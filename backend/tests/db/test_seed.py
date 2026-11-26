from datetime import UTC, datetime

from sqlalchemy import func, select

from app.core.passwords import verify_password
from app.db.models import Course, Enrollment, StudentEvent, SupportTicket, User
from app.db.seed import DEMO_COURSE_ID, DEMO_PASSWORD, seed
from app.services.activity import load_activity
from app.services.risk import compute_risk


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


def demo_risks(session):
    now = datetime.now(UTC)
    activities = load_activity(session, DEMO_COURSE_ID, now)
    return {a.student_id: compute_risk(a, now) for a in activities}


def test_demo_activity_gives_the_dashboard_every_risk_level(session):
    seed(session)

    risks = demo_risks(session)

    assert {r.risk_level for r in risks.values()} == {"green", "yellow", "red"}
    assert risks["s1"].risk_level == "green"
    assert risks["s2"].risk_level == "red"
    assert risks["s4"].risk_level == "red"  # never seen


def test_activity_seed_is_idempotent(session):
    seed(session)
    events = session.scalar(select(func.count()).select_from(StudentEvent))
    tickets = session.scalar(select(func.count()).select_from(SupportTicket))

    seed(session)

    assert session.scalar(select(func.count()).select_from(StudentEvent)) == events
    assert session.scalar(select(func.count()).select_from(SupportTicket)) == tickets


def test_activity_seed_does_not_touch_a_course_that_already_has_data(session):
    seed(session)
    session.query(StudentEvent).delete()
    session.add(
        StudentEvent(
            course_id=DEMO_COURSE_ID, user_id="s1", type="login", occurred_at=datetime.now(UTC)
        )
    )
    session.flush()

    seed(session)

    assert session.scalar(select(func.count()).select_from(StudentEvent)) == 1


def test_demo_questions_give_the_thermometer_one_alert_and_some_calm_topics(session):
    from app.services.topics import compute_topics, load_topic_questions

    seed(session)

    stats = compute_topics(load_topic_questions(session, DEMO_COURSE_ID, datetime.now(UTC)))

    assert stats[0].topic == "Derivadas" and stats[0].confusion_alert is True
    assert {s.topic for s in stats} == {"Derivadas", "Límites", "Integrales"}
    assert sum(s.confusion_alert for s in stats) == 1
