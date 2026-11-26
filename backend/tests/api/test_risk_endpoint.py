from datetime import UTC, datetime, timedelta

import pytest
from pydantic import TypeAdapter

from app.db.models import Course, StudentEvent
from app.schemas import CourseRiskResponse

URL = "/api/v1/analytics/courses/{course}/risk"


def now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def teacher(make_user):
    return make_user("t1", role="teacher")


@pytest.fixture
def class_of_three(make_user, session):
    """A healthy student, a struggling one and one nobody has heard from."""
    good = make_user("s1", role="student")
    bad = make_user("s2", role="student")
    ghost = make_user("s3", role="student")
    when = now()
    for kind, days, value in [
        ("login", 0.2, None),
        ("submission", 1, None),
        ("grade", 3, 4.6),
    ]:
        session.add(
            StudentEvent(
                course_id="c1", user_id=good.id, type=kind, value=value,
                scale=5 if kind == "grade" else None, occurred_at=when - timedelta(days=days),
            )
        )  # fmt: skip
    for kind, days, value in [
        ("login", 15, None),
        ("grade", 5, 1.8),
        ("missed_deadline", 3, None),
        ("missed_deadline", 6, None),
        ("missed_deadline", 9, None),
    ]:
        session.add(
            StudentEvent(
                course_id="c1", user_id=bad.id, type=kind, value=value,
                scale=5 if kind == "grade" else None, occurred_at=when - timedelta(days=days),
            )
        )  # fmt: skip
    session.flush()
    return good, bad, ghost


def get(api, headers, course="c1", **params):
    return api.get(URL.format(course=course), headers=headers, params=params)


def test_returns_a_contract_valid_ranking_with_explained_factors(
    api, teacher, class_of_three, auth
):
    response = get(api, auth(teacher))

    assert response.status_code == 200
    body = response.json()
    TypeAdapter(CourseRiskResponse).validate_python(body)
    assert body["course_id"] == "c1"
    ranked = [s["student_id"] for s in body["students"]]
    assert ranked[-1] == "s1"  # the healthy one is last
    assert set(ranked) == {"s1", "s2", "s3"}
    scores = [s["risk_score"] for s in body["students"]]
    assert scores == sorted(scores, reverse=True)
    assert all(
        s["factors"] and all(f["explanation"] for f in s["factors"]) for s in body["students"]
    )


def test_levels_match_the_situation_of_each_student(api, teacher, class_of_three, auth):
    students = {s["student_id"]: s for s in get(api, auth(teacher)).json()["students"]}

    assert students["s1"]["risk_level"] == "green"
    assert students["s2"]["risk_level"] == "red"
    assert students["s3"]["risk_level"] == "red"  # no activity at all is itself a warning
    keys = {f["key"] for f in students["s2"]["factors"]}
    assert {"days_since_last_login", "average_grade", "missed_assignments"} <= keys


def test_summary_counts_the_whole_course(api, teacher, class_of_three, auth):
    summary = get(api, auth(teacher)).json()["summary"]

    assert summary == {"green": 1, "yellow": 0, "red": 2}


def test_level_filter_narrows_the_list_but_not_the_summary(api, teacher, class_of_three, auth):
    body = get(api, auth(teacher), level="red").json()

    assert {s["student_id"] for s in body["students"]} == {"s2", "s3"}
    assert body["summary"] == {"green": 1, "yellow": 0, "red": 2}


def test_filter_with_no_matches_returns_an_empty_list(api, teacher, class_of_three, auth):
    body = get(api, auth(teacher), level="yellow").json()

    assert body["students"] == []


def test_unknown_level_is_422(api, teacher, class_of_three, auth):
    response = get(api, auth(teacher), level="orange")

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"


def test_the_teacher_is_not_listed_as_a_student(api, teacher, class_of_three, auth):
    ids = {s["student_id"] for s in get(api, auth(teacher)).json()["students"]}

    assert "t1" not in ids


def test_course_without_students_is_empty_but_valid(api, teacher, auth):
    body = get(api, auth(teacher)).json()

    assert body["students"] == []
    assert body["summary"] == {"green": 0, "yellow": 0, "red": 0}


def test_no_token_is_401(api):
    assert get(api, {}).status_code == 401


def test_students_cannot_see_the_dashboard(api, make_user, auth):
    student = make_user("s1", role="student")

    assert get(api, auth(student)).status_code == 403


def test_unknown_course_is_404(api, teacher, auth):
    assert get(api, auth(teacher), course="nope").status_code == 404


def test_teacher_of_another_course_is_403(api, session, teacher, auth):
    session.add(Course(id="c2", name="Otro"))
    session.flush()

    assert get(api, auth(teacher), course="c2").status_code == 403
