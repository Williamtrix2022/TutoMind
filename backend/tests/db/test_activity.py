from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import event

from app.db.models import (
    Conversation,
    Course,
    Enrollment,
    Message,
    StudentEvent,
    SupportTicket,
    User,
)
from app.services.activity import load_activity

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


def days_ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


@pytest.fixture
def world(session):
    """Course c1 with a teacher and students Ana and Beto; course c2 for isolation."""
    session.add_all([Course(id="c1", name="Cálculo"), Course(id="c2", name="Otro")])
    session.flush()
    for user_id, name, role in [
        ("t1", "Profe", "teacher"),
        ("s1", "Ana Torres", "student"),
        ("s2", "Beto Ruiz", "student"),
    ]:
        session.add(
            User(id=user_id, name=name, email=f"{user_id}@x.edu", password_hash="h", role=role)
        )
    session.flush()
    for user_id in ("t1", "s1", "s2"):
        session.add(Enrollment(course_id="c1", user_id=user_id))
    session.flush()
    return session


def add_event(session, user, kind, when, value=None, scale=None, course="c1"):
    session.add(
        StudentEvent(
            course_id=course, user_id=user, type=kind, occurred_at=when, value=value, scale=scale
        )
    )
    session.flush()


def add_message(session, user, when, role="user", score=None, course="c1", conversation=None):
    conversation = conversation or f"conv-{user}-{course}"
    if session.get(Conversation, conversation) is None:
        session.add(Conversation(id=conversation, course_id=course, student_id=user))
        session.flush()
    session.add(
        Message(
            conversation_id=conversation, role=role, content="hola", created_at=when,
            frustration_score=score,
        )
    )  # fmt: skip
    session.flush()


def by_id(activities):
    return {a.student_id: a for a in activities}


def test_only_enrolled_students_are_returned_sorted_by_name(world):
    activities = load_activity(world, "c1", NOW)

    assert [a.student_id for a in activities] == ["s1", "s2"]
    assert [a.name for a in activities] == ["Ana Torres", "Beto Ruiz"]


def test_a_course_without_students_is_empty(world):
    assert load_activity(world, "c2", NOW) == []


def test_a_student_with_no_data_has_no_activity(world):
    ana = by_id(load_activity(world, "c1", NOW))["s1"]

    assert ana.last_activity_at is None
    assert (ana.grades, ana.missed_deadlines, ana.submissions, ana.questions) == ([], 0, 0, 0)
    assert (ana.scored_messages, ana.frustrated_messages, ana.open_tickets) == (0, 0, 0)


def test_last_activity_is_the_latest_login_submission_or_question(world):
    add_event(world, "s1", "login", days_ago(6))
    add_event(world, "s1", "submission", days_ago(3))
    add_message(world, "s1", days_ago(2))

    assert by_id(load_activity(world, "c1", NOW))["s1"].last_activity_at == days_ago(2)


def test_grades_missed_deadlines_and_tutor_replies_are_not_student_activity(world):
    add_event(world, "s1", "login", days_ago(9))
    add_event(world, "s1", "grade", days_ago(1), value=4, scale=5)
    add_event(world, "s1", "missed_deadline", days_ago(1))
    add_message(world, "s1", days_ago(1), role="assistant")

    assert by_id(load_activity(world, "c1", NOW))["s1"].last_activity_at == days_ago(9)


def test_grades_older_than_90_days_are_left_out(world):
    add_event(world, "s1", "grade", days_ago(10), value=4, scale=5)
    add_event(world, "s1", "grade", days_ago(95), value=1, scale=5)

    grades = by_id(load_activity(world, "c1", NOW))["s1"].grades

    assert [(g.value, g.scale) for g in grades] == [(4, 5)]


def test_missed_deadlines_and_submissions_count_the_last_30_days(world):
    for days in (2, 10, 40):
        add_event(world, "s1", "missed_deadline", days_ago(days))
        add_event(world, "s1", "submission", days_ago(days))

    ana = by_id(load_activity(world, "c1", NOW))["s1"]

    assert (ana.missed_deadlines, ana.submissions) == (2, 2)


def test_tutor_stats_cover_the_last_14_days_and_only_student_messages(world):
    add_message(world, "s1", days_ago(1), score=0.8)
    add_message(world, "s1", days_ago(2), score=0.1)
    add_message(world, "s1", days_ago(3), score=None)  # not scored (older data)
    add_message(world, "s1", days_ago(2), role="assistant", score=None)
    add_message(world, "s1", days_ago(20), score=0.9)  # outside the window

    ana = by_id(load_activity(world, "c1", NOW))["s1"]

    assert ana.questions == 3
    assert ana.scored_messages == 2
    assert ana.frustrated_messages == 1


def test_frustration_threshold_is_inclusive(world):
    add_message(world, "s1", days_ago(1), score=0.5)

    assert by_id(load_activity(world, "c1", NOW))["s1"].frustrated_messages == 1


def test_open_tickets_are_counted_and_resolved_ones_are_not(world):
    add_message(world, "s1", days_ago(1))
    for status, reason in [("open", "student_requested"), ("resolved", "persistent_frustration")]:
        world.add(
            SupportTicket(
                course_id="c1", student_id="s1", conversation_id="conv-s1-c1",
                reason=reason, status=status,
            )
        )  # fmt: skip
    world.flush()

    assert by_id(load_activity(world, "c1", NOW))["s1"].open_tickets == 1


def test_other_courses_do_not_leak_in(world):
    add_event(world, "s1", "login", days_ago(1), course="c2")
    add_event(world, "s1", "grade", days_ago(1), value=1, scale=5, course="c2")
    add_message(world, "s1", days_ago(1), course="c2")

    ana = by_id(load_activity(world, "c1", NOW))["s1"]

    assert ana.last_activity_at is None and ana.grades == [] and ana.questions == 0


def test_query_count_does_not_grow_with_the_number_of_students(session, world):
    for index in range(20):
        user_id = f"extra{index}"
        session.add(
            User(id=user_id, name=f"E{index}", email=f"{user_id}@x.edu", password_hash="h",
                 role="student")
        )  # fmt: skip
        session.flush()
        session.add(Enrollment(course_id="c1", user_id=user_id))
    session.flush()
    statements = []
    engine = session.get_bind()
    listener = lambda *args: statements.append(args[2])  # noqa: E731
    event.listen(engine, "before_cursor_execute", listener)
    try:
        activities = load_activity(session, "c1", NOW)
    finally:
        event.remove(engine, "before_cursor_execute", listener)

    assert len(activities) == 22
    assert len(statements) <= 8
