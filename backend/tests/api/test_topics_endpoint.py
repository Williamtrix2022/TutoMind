from datetime import UTC, datetime, timedelta

import pytest
from pydantic import TypeAdapter

from app.db.models import Conversation, Course, Message
from app.schemas import CourseTopicsResponse

URL = "/api/v1/analytics/courses/{course}/topics"


@pytest.fixture
def teacher(make_user):
    return make_user("t1", role="teacher")


@pytest.fixture
def ask(session):
    """Persist a student question: (student, topic, score, days_ago, course)."""

    def _ask(student, topic, score=0.0, days_ago=1.0, course="c1", text="Una duda"):
        conversation = f"conv-{student}-{course}"
        if session.get(Conversation, conversation) is None:
            session.add(Conversation(id=conversation, course_id=course, student_id=student))
            session.flush()
        session.add(
            Message(
                conversation_id=conversation, role="user", content=text, topic=topic,
                frustration_score=score, created_at=datetime.now(UTC) - timedelta(days=days_ago),
            )
        )  # fmt: skip
        session.flush()

    return _ask


@pytest.fixture
def class_questions(make_user, ask):
    for student in ("s1", "s2", "s3"):
        make_user(student, role="student")
    ask("s1", "Derivadas", 0.8, text="no entiendo la regla de la cadena")
    ask("s1", "Derivadas", 0.7)
    ask("s2", "Derivadas", 0.9)
    ask("s3", "Límites", 0.0)
    ask("s2", "Límites", 0.0)


def get(api, headers, course="c1"):
    return api.get(URL.format(course=course), headers=headers)


def test_returns_a_contract_valid_thermometer(api, teacher, class_questions, auth):
    response = get(api, auth(teacher))

    assert response.status_code == 200
    body = response.json()
    TypeAdapter(CourseTopicsResponse).validate_python(body)
    assert body["course_id"] == "c1"
    start = datetime.fromisoformat(body["period_start"])
    end = datetime.fromisoformat(body["period_end"])
    assert end - start == timedelta(days=7)


def test_the_confused_topic_comes_first_with_an_alert(api, teacher, class_questions, auth):
    topics = get(api, auth(teacher)).json()["topics"]

    assert [t["topic"] for t in topics] == ["Derivadas", "Límites"]
    derivatives, limits = topics
    assert derivatives["confusion_alert"] is True
    assert (derivatives["question_count"], derivatives["unique_students"]) == (3, 2)
    assert "no entiendo la regla de la cadena" in derivatives["sample_questions"]
    assert limits["confusion_alert"] is False and limits["confusion_score"] == 0.0


def test_questions_older_than_the_window_are_left_out(api, teacher, make_user, ask, auth):
    make_user("s1", role="student")
    ask("s1", "Derivadas", 0.9, days_ago=8)
    ask("s1", "Límites", 0.0, days_ago=2)

    topics = get(api, auth(teacher)).json()["topics"]

    assert [t["topic"] for t in topics] == ["Límites"]


def test_other_courses_do_not_leak_in(api, session, teacher, make_user, ask, auth):
    make_user("s1", role="student")
    session.add(Course(id="c2", name="Otro"))
    session.flush()
    ask("s1", "Secreto de otro curso", 0.9, course="c2")

    assert get(api, auth(teacher)).json()["topics"] == []


def test_questions_without_a_topic_are_not_counted(api, teacher, make_user, ask, auth):
    make_user("s1", role="student")
    ask("s1", None, 0.0)

    assert get(api, auth(teacher)).json()["topics"] == []


def test_a_course_without_questions_is_empty_but_valid(api, teacher, auth):
    body = get(api, auth(teacher)).json()

    assert body["topics"] == []
    TypeAdapter(CourseTopicsResponse).validate_python(body)


def test_tutor_replies_are_not_questions(api, session, teacher, make_user, auth):
    make_user("s1", role="student")
    session.add(Conversation(id="c", course_id="c1", student_id="s1"))
    session.flush()
    session.add(
        Message(conversation_id="c", role="assistant", content="Respuesta", topic="Derivadas")
    )
    session.flush()

    assert get(api, auth(teacher)).json()["topics"] == []


def test_no_token_is_401(api):
    assert get(api, {}).status_code == 401


def test_students_cannot_see_the_thermometer(api, make_user, auth):
    assert get(api, auth(make_user("s1", role="student"))).status_code == 403


def test_unknown_course_is_404(api, teacher, auth):
    assert get(api, auth(teacher), course="nope").status_code == 404


def test_teacher_of_another_course_is_403(api, session, teacher, auth):
    session.add(Course(id="c2", name="Otro"))
    session.flush()

    assert get(api, auth(teacher), course="c2").status_code == 403
