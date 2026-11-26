from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.db.models import Course, Enrollment, StudentEvent, User
from app.services.moodle import MoodleEvent
from app.services.moodle_sync import sync_course

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


class FakeMoodle:
    def __init__(self, events):
        self.events = events
        self.requested: list[str] = []

    def fetch_events(self, course_id, now):
        self.requested.append(course_id)
        return list(self.events)


def event(email, kind="login", days_ago=1.0, value=None, scale=None, source="moodle"):
    return MoodleEvent(
        email=email, type=kind, value=value, scale=scale,
        occurred_at=NOW - timedelta(days=days_ago), source=source,
    )  # fmt: skip


@pytest.fixture
def world(session):
    session.add_all([Course(id="101", name="Cálculo"), Course(id="202", name="Otro")])
    session.flush()
    for user_id, role in [("s1", "student"), ("s2", "student"), ("t1", "teacher")]:
        session.add(
            User(id=user_id, name=user_id, email=f"{user_id}@uni.edu", password_hash="h", role=role)
        )
    session.flush()
    for user_id in ("s1", "s2", "t1"):
        session.add(Enrollment(course_id="101", user_id=user_id))
    session.flush()
    return session


def stored(session, course="101"):
    rows = session.scalars(
        select(StudentEvent).where(StudentEvent.course_id == course).order_by(StudentEvent.id)
    ).all()
    return [(r.user_id, r.type, r.value, r.scale, r.source) for r in rows]


def test_events_are_matched_to_students_by_email_and_stored(world):
    client = FakeMoodle([event("s1@uni.edu"), event("s2@uni.edu", "grade", value=3.5, scale=5)])

    result = sync_course(world, client, "101", NOW)

    assert (result.received, result.inserted, result.duplicates, result.unknown_users) == (
        2,
        2,
        0,
        0,
    )
    assert stored(world) == [
        ("s1", "login", None, None, "moodle"),
        ("s2", "grade", 3.5, 5, "moodle"),
    ]
    assert client.requested == ["101"]


def test_email_matching_ignores_case(world):
    sync_course(world, FakeMoodle([event("S1@UNI.edu")]), "101", NOW)

    assert [row[0] for row in stored(world)] == ["s1"]


def test_unknown_emails_and_teachers_are_skipped_and_counted(world):
    client = FakeMoodle(
        [event("nobody@uni.edu"), event("nobody@uni.edu", "grade"), event("t1@uni.edu")]
    )

    result = sync_course(world, client, "101", NOW)

    assert result.inserted == 0
    assert result.unknown_users == 2  # distinct emails: the stranger and the teacher
    assert stored(world) == []


def test_running_it_twice_changes_nothing(world):
    client = FakeMoodle([event("s1@uni.edu"), event("s1@uni.edu", "grade", 2, value=4, scale=5)])
    sync_course(world, client, "101", NOW)

    second = sync_course(world, client, "101", NOW)

    assert (second.inserted, second.duplicates) == (0, 2)
    assert len(stored(world)) == 2


def test_only_new_events_are_added_on_a_later_run(world):
    sync_course(world, FakeMoodle([event("s1@uni.edu", days_ago=5)]), "101", NOW)

    later = sync_course(
        world,
        FakeMoodle([event("s1@uni.edu", days_ago=5), event("s1@uni.edu", days_ago=1)]),
        "101",
        NOW,
    )

    assert (later.inserted, later.duplicates) == (1, 1)


def test_the_same_moment_from_another_source_is_a_separate_fact(world):
    sync_course(world, FakeMoodle([event("s1@uni.edu", source="moodle")]), "101", NOW)

    result = sync_course(world, FakeMoodle([event("s1@uni.edu", source="simulated")]), "101", NOW)

    assert result.inserted == 1


def test_other_courses_are_untouched(world):
    sync_course(world, FakeMoodle([event("s1@uni.edu")]), "101", NOW)

    assert stored(world, "202") == []
    assert session_count(world) == 1


def session_count(session) -> int:
    return session.scalar(select(func.count()).select_from(StudentEvent))


def test_an_empty_moodle_answer_is_a_valid_run(world):
    result = sync_course(world, FakeMoodle([]), "101", NOW)

    assert (result.received, result.inserted) == (0, 0)


def test_unknown_course_is_an_error_not_silence(world):
    from app.services.moodle_sync import UnknownCourseError

    with pytest.raises(UnknownCourseError):
        sync_course(world, FakeMoodle([]), "nope", NOW)


def test_what_moodle_reports_feeds_the_risk_model(world):
    from app.services.activity import load_activity
    from app.services.risk import compute_risk

    sync_course(
        world,
        FakeMoodle(
            [
                event("s1@uni.edu", "grade", 3, value=1.5, scale=5),
                event("s1@uni.edu", "missed_deadline", 2),
                event("s1@uni.edu", "missed_deadline", 4),
                event("s1@uni.edu", "missed_deadline", 6),
            ]
        ),
        "101",
        NOW,
    )

    risk = {a.student_id: compute_risk(a, NOW) for a in load_activity(world, "101", NOW)}["s1"]

    assert risk.risk_level == "red"
    assert {"average_grade", "missed_assignments"} <= {f.key for f in risk.factors}


def test_run_sync_without_moodle_configured_uses_the_labelled_simulation(world):
    from app.core.config import Settings
    from app.services.moodle_sync import run_sync

    world.add(Course(id="demo", name="Demo"))
    world.flush()
    for email, user_id in [("ana@tutomind.demo", "s9"), ("luis@tutomind.demo", "s8")]:
        world.add(User(id=user_id, name=user_id, email=email, password_hash="h", role="student"))
        world.flush()
        world.add(Enrollment(course_id="demo", user_id=user_id))
    world.flush()

    result = run_sync(world, Settings(_env_file=None), "demo", NOW)

    assert result.source == "simulated"
    assert (
        result.inserted > 0 and result.unknown_users == 2
    )  # maria and sofia are not enrolled here


class SimulatedMoodle(FakeMoodle):
    source = "simulated"


def test_a_simulated_sync_replaces_its_previous_snapshot_instead_of_piling_up(world):
    first = SimulatedMoodle([event("s1@uni.edu", "missed_deadline", 3, source="simulated")])
    sync_course(world, first, "101", NOW)
    later = SimulatedMoodle([event("s1@uni.edu", "missed_deadline", 2, source="simulated")])

    result = sync_course(world, later, "101", NOW + timedelta(days=1))

    assert result.inserted == 1
    rows = world.scalars(select(StudentEvent)).all()
    assert [r.occurred_at for r in rows] == [NOW - timedelta(days=2)]


def test_a_simulated_sync_never_touches_real_moodle_data(world):
    sync_course(world, FakeMoodle([event("s1@uni.edu", "login", 4)]), "101", NOW)

    sync_course(world, SimulatedMoodle([event("s1@uni.edu", source="simulated")]), "101", NOW)

    assert sorted(row[4] for row in stored(world)) == ["moodle", "simulated"]


def test_a_real_sync_does_not_delete_simulated_data(world):
    sync_course(world, SimulatedMoodle([event("s1@uni.edu", source="simulated")]), "101", NOW)

    sync_course(world, FakeMoodle([event("s1@uni.edu", "login", 4)]), "101", NOW)

    assert sorted(row[4] for row in stored(world)) == ["moodle", "simulated"]
