"""The Web Services client, against a fake Moodle (httpx.MockTransport).

The fake follows Moodle's documented REST responses; it has NOT been checked against a real Moodle
server. Field names are the part most worth verifying the first time a real Moodle is available.
"""

import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs

import httpx
import pytest

from app.services.moodle import MoodleError, MoodleWebServiceClient

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


def epoch(days_ago: float) -> int:
    return int((NOW - timedelta(days=days_ago)).timestamp())


STUDENT = [{"shortname": "student"}]
USERS = [
    {"id": 11, "email": "Ana@Uni.edu", "lastaccess": epoch(2), "roles": STUDENT},
    {"id": 12, "email": "beto@uni.edu", "lastaccess": 0, "roles": STUDENT},  # never accessed
    {
        "id": 13,
        "email": "profe@uni.edu",
        "lastaccess": epoch(1),
        "roles": [{"shortname": "editingteacher"}],
    },
]
GRADES = {
    "usergrades": [
        {
            "userid": 11,
            "gradeitems": [
                {"itemtype": "mod", "graderaw": 4.5, "grademax": 5, "gradedategraded": epoch(5)},
                {"itemtype": "mod", "graderaw": None, "grademax": 5, "gradedategraded": None},
                {"itemtype": "course", "graderaw": 4.5, "grademax": 5, "gradedategraded": epoch(5)},
            ],
        },
        {
            "userid": 12,
            "gradeitems": [
                {"itemtype": "mod", "graderaw": 2.0, "grademax": 5, "gradedategraded": epoch(9)}
            ],
        },
    ]
}
ASSIGNMENTS = {
    "courses": [
        {
            "id": 101,
            "assignments": [
                {"id": 1, "duedate": epoch(10)},  # past due: Ana submitted, Beto did not
                {"id": 2, "duedate": epoch(-5)},  # still open: nobody is late
                {"id": 3, "duedate": 0},  # no due date
            ],
        }
    ]
}
SUBMISSIONS = {
    "assignments": [
        {
            "assignmentid": 1,
            "submissions": [
                {"userid": 11, "status": "submitted", "timemodified": epoch(11)},
                {
                    "userid": 12,
                    "status": "draft",
                    "timemodified": epoch(12),
                },  # a draft is not handed in
            ],
        },
        {"assignmentid": 2, "submissions": []},
        {"assignmentid": 3, "submissions": []},
    ]
}
RESPONSES = {
    "core_enrol_get_enrolled_users": USERS,
    "gradereport_user_get_grade_items": GRADES,
    "mod_assign_get_assignments": ASSIGNMENTS,
    "mod_assign_get_submissions": SUBMISSIONS,
}


def make_client(handler=None, base_url="https://moodle.example.edu", token="secret-token"):
    calls: list[tuple[httpx.Request, dict]] = []

    def default(request: httpx.Request) -> httpx.Response:
        form = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
        calls.append((request, form))
        return httpx.Response(200, json=RESPONSES[form["wsfunction"]])

    http = httpx.Client(transport=httpx.MockTransport(handler or default))
    return MoodleWebServiceClient(base_url, token, http=http), calls


def events_by(events, kind):
    return [e for e in events if e.type == kind]


class TestMapping:
    def test_last_access_becomes_a_login_event_and_never_accessed_is_skipped(self):
        client, _ = make_client()

        logins = events_by(client.fetch_events("101", NOW), "login")

        assert [(e.email, e.occurred_at) for e in logins] == [
            ("ana@uni.edu", NOW - timedelta(days=2))
        ]

    def test_only_graded_module_items_become_grades_with_their_scale(self):
        client, _ = make_client()

        grades = events_by(client.fetch_events("101", NOW), "grade")

        assert sorted((e.email, e.value, e.scale) for e in grades) == [
            ("ana@uni.edu", 4.5, 5),
            ("beto@uni.edu", 2.0, 5),
        ]

    def test_a_handed_in_assignment_is_a_submission_at_its_modification_time(self):
        client, _ = make_client()

        submissions = events_by(client.fetch_events("101", NOW), "submission")

        assert [(e.email, e.occurred_at) for e in submissions] == [
            ("ana@uni.edu", NOW - timedelta(days=11))
        ]

    def test_past_due_without_a_real_submission_is_a_missed_deadline(self):
        client, _ = make_client()

        missed = events_by(client.fetch_events("101", NOW), "missed_deadline")

        # Beto only has a draft; assignment 2 is still open; assignment 3 has no due date.
        assert [(e.email, e.occurred_at) for e in missed] == [
            ("beto@uni.edu", NOW - timedelta(days=10))
        ]

    def test_teachers_are_not_students(self):
        client, _ = make_client()

        assert "profe@uni.edu" not in {e.email for e in client.fetch_events("101", NOW)}

    def test_emails_are_lower_cased_for_matching(self):
        client, _ = make_client()

        assert all(e.email == e.email.lower() for e in client.fetch_events("101", NOW))

    def test_source_is_moodle(self):
        client, _ = make_client()

        assert {e.source for e in client.fetch_events("101", NOW)} == {"moodle"}


class TestRequests:
    def test_calls_the_four_documented_functions_on_the_rest_endpoint(self):
        client, calls = make_client()

        client.fetch_events("101", NOW)

        assert {f["wsfunction"] for _, f in calls} == set(RESPONSES)
        assert all(r.url.path == "/webservice/rest/server.php" for r, _ in calls)
        assert all(f["moodlewsrestformat"] == "json" for _, f in calls)

    def test_the_token_travels_in_the_body_never_in_the_url(self):
        client, calls = make_client()

        client.fetch_events("101", NOW)

        assert all(r.method == "POST" for r, _ in calls)
        assert all("secret-token" not in str(r.url) for r, _ in calls)
        assert all(f["wstoken"] == "secret-token" for _, f in calls)

    def test_a_trailing_slash_in_the_base_url_is_harmless(self):
        client, calls = make_client(base_url="https://moodle.example.edu/")

        client.fetch_events("101", NOW)

        assert calls[0][0].url.path == "/webservice/rest/server.php"

    def test_submissions_are_requested_only_for_the_courses_assignments(self):
        client, calls = make_client()

        client.fetch_events("101", NOW)

        forms = [f for _, f in calls if f["wsfunction"] == "mod_assign_get_submissions"]
        assert [f["assignmentids[0]"] for f in forms] == ["1"]
        assert {f["assignmentids[1]"] for f in forms} == {"2"}


class TestFailures:
    def test_a_moodle_exception_becomes_a_moodle_error_without_the_token(self):
        def handler(request):
            return httpx.Response(
                200,
                json={
                    "exception": "moodle_exception",
                    "errorcode": "invalidtoken",
                    "message": "Invalid token",
                },
            )

        client, _ = make_client(handler)

        with pytest.raises(MoodleError, match="invalidtoken") as error:
            client.fetch_events("101", NOW)
        assert "secret-token" not in str(error.value)

    @pytest.mark.parametrize("status", [401, 500, 503])
    def test_http_errors_are_reported(self, status):
        client, _ = make_client(lambda request: httpx.Response(status))

        with pytest.raises(MoodleError, match=str(status)):
            client.fetch_events("101", NOW)

    def test_a_non_json_answer_is_reported(self):
        client, _ = make_client(lambda request: httpx.Response(200, text="<html>login</html>"))

        with pytest.raises(MoodleError, match="JSON"):
            client.fetch_events("101", NOW)

    def test_network_failures_are_reported_without_the_token(self):
        def handler(request):
            raise httpx.ConnectError("boom", request=request)

        client, _ = make_client(handler)

        with pytest.raises(MoodleError, match="conectar") as error:
            client.fetch_events("101", NOW)
        assert "secret-token" not in str(error.value)

    def test_it_refuses_to_run_without_a_token(self):
        with pytest.raises(MoodleError, match="token"):
            MoodleWebServiceClient("https://moodle.example.edu", "")

    def test_the_wire_format_is_valid_json_for_the_fake(self):
        json.dumps(RESPONSES)  # guards the fixtures themselves
