"""Moodle Web Services client, plus a clearly-labelled simulation for when there is no Moodle.

What it reads (REST protocol, `/webservice/rest/server.php`, one POST per function):

| Function                           | Becomes                                                   |
|------------------------------------|-----------------------------------------------------------|
| `core_enrol_get_enrolled_users`    | `login` at the user's `lastaccess` (and who is a student) |
| `gradereport_user_get_grade_items` | `grade` for each graded activity (value / max)            |
| `mod_assign_get_assignments`       | the due dates                                             |
| `mod_assign_get_submissions`       | `submission`; past-due without one is `missed_deadline`   |

Limits worth knowing: Moodle only exposes the *last* access, so each sync adds at most one login
event per student; and this client was written from Moodle's documented responses and tested
against a fake. It has NOT been run against a real Moodle: verify field names first.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import httpx

from app.core.config import Settings

REST_PATH = "/webservice/rest/server.php"
DEMO_COURSE_ID = "demo"


class MoodleError(Exception):
    """Moodle could not be reached or refused the request. The message never contains the token."""


@dataclass(frozen=True)
class MoodleEvent:
    email: str  # lower-cased; how Moodle users are matched to TutoMind users
    type: str  # login | grade | submission | missed_deadline
    value: float | None
    scale: float | None
    occurred_at: datetime
    source: str = "moodle"


class MoodleClient(Protocol):
    source: str

    def fetch_events(self, course_id: str, now: datetime) -> list[MoodleEvent]: ...


def _at(epoch: int | float) -> datetime:
    return datetime.fromtimestamp(epoch, tz=UTC)


def _is_student(user: dict[str, Any]) -> bool:
    roles = user.get("roles")
    return roles is None or any(role.get("shortname") == "student" for role in roles)


class MoodleWebServiceClient:
    source = "moodle"

    def __init__(
        self, base_url: str, token: str, http: httpx.Client | None = None, timeout: float = 20.0
    ) -> None:
        if not token:
            raise MoodleError("Falta el token de Web Services de Moodle (MOODLE_TOKEN).")
        self._endpoint = base_url.rstrip("/") + REST_PATH
        self._token = token
        self._http = http or httpx.Client(timeout=timeout)

    def _call(self, function: str, **params: Any) -> Any:
        # POST with the token in the body: query strings end up in proxy and server logs.
        data = {
            "wstoken": self._token,
            "wsfunction": function,
            "moodlewsrestformat": "json",
            **params,
        }
        try:
            response = self._http.post(self._endpoint, data=data)
        except httpx.HTTPError as error:
            raise MoodleError("No se pudo conectar con Moodle.") from error
        if response.status_code != 200:
            raise MoodleError(f"Moodle respondió HTTP {response.status_code}.")
        try:
            payload = response.json()
        except ValueError as error:
            raise MoodleError("Moodle no devolvió JSON válido (¿es correcta la URL?).") from error
        if isinstance(payload, dict) and "exception" in payload:
            code = payload.get("errorcode", "error")
            raise MoodleError(f"Moodle rechazó la llamada ({code}): {payload.get('message', '')}")
        return payload

    def fetch_events(self, course_id: str, now: datetime) -> list[MoodleEvent]:
        users = self._call("core_enrol_get_enrolled_users", courseid=course_id)
        students = {u["id"]: u["email"].lower() for u in users if _is_student(u)}
        events: list[MoodleEvent] = []

        def add(user_id: int, kind: str, when: datetime, value=None, scale=None) -> None:
            events.append(MoodleEvent(students[user_id], kind, value, scale, when, self.source))

        for user in users:
            if user["id"] in students and user.get("lastaccess"):
                add(user["id"], "login", _at(user["lastaccess"]))

        graded = self._call("gradereport_user_get_grade_items", courseid=course_id)
        for usergrade in graded.get("usergrades", []):
            if usergrade["userid"] not in students:
                continue
            for item in usergrade.get("gradeitems", []):
                when = item.get("gradedategraded") or item.get("gradedatesubmitted")
                if (
                    item.get("itemtype") == "mod"  # not the course or category totals
                    and item.get("graderaw") is not None
                    and item.get("grademax")
                    and when
                ):
                    add(usergrade["userid"], "grade", _at(when), item["graderaw"], item["grademax"])

        courses = self._call("mod_assign_get_assignments", **{"courseids[0]": course_id})
        assignments = [a for c in courses.get("courses", []) for a in c.get("assignments", [])]
        if not assignments:
            return events
        ids = {f"assignmentids[{i}]": a["id"] for i, a in enumerate(assignments)}
        handed_in: dict[int, set[int]] = {a["id"]: set() for a in assignments}
        for block in self._call("mod_assign_get_submissions", **ids).get("assignments", []):
            for submission in block.get("submissions", []):
                user_id = submission["userid"]
                if submission.get("status") == "submitted" and user_id in students:
                    handed_in[block["assignmentid"]].add(user_id)
                    add(user_id, "submission", _at(submission["timemodified"]))

        for assignment in assignments:
            due = assignment.get("duedate") or 0
            if 0 < due < now.timestamp():
                for user_id in students:
                    if user_id not in handed_in[assignment["id"]]:
                        add(user_id, "missed_deadline", _at(due))
        return events


# Demo profiles for the simulation, by email: (days ago, type, value, scale).
# One student per situation: ana green, luis red, maria and sofia yellow; carlos never seen.
_DEMO_EVENTS: dict[str, list[tuple[float, str, float | None, float | None]]] = {
    "ana@tutomind.demo": [
        (0.3, "login", None, None), (1, "submission", None, None), (2, "submission", None, None),
        (4, "submission", None, None), (6, "grade", 4.5, 5), (12, "grade", 4.2, 5),
    ],
    "luis@tutomind.demo": [
        (12, "login", None, None), (10, "grade", 2.0, 5), (20, "grade", 1.8, 5),
        (3, "missed_deadline", None, None), (8, "missed_deadline", None, None),
        (15, "missed_deadline", None, None),
    ],
    "maria@tutomind.demo": [
        (5, "login", None, None), (9, "grade", 3.2, 5), (4, "missed_deadline", None, None),
    ],
    "sofia@tutomind.demo": [(6, "login", None, None), (14, "grade", 3.0, 5)],
}  # fmt: skip


class SimulatedMoodleClient:
    """Demo data for the `demo` course when no Moodle is configured. Always says it is simulated."""

    source = "simulated"

    def fetch_events(self, course_id: str, now: datetime) -> list[MoodleEvent]:
        if course_id != DEMO_COURSE_ID:
            return []
        return [
            MoodleEvent(email, kind, value, scale, now - timedelta(days=days), self.source)
            for email, events in _DEMO_EVENTS.items()
            for days, kind, value, scale in events
        ]


def get_moodle_client(settings: Settings) -> MoodleClient:
    """The real client when Moodle is configured, the simulation when it is not."""
    if not settings.moodle_base_url:
        return SimulatedMoodleClient()
    if not settings.moodle_token:
        raise MoodleError("MOODLE_BASE_URL está configurada pero falta MOODLE_TOKEN.")
    return MoodleWebServiceClient(settings.moodle_base_url, settings.moodle_token)


def moodle_course_url(settings: Settings, course_id: str) -> str | None:
    """Link to the course page in Moodle. Only for real Moodle course ids (numeric)."""
    if not settings.moodle_base_url or not course_id.isdigit():
        return None
    return f"{settings.moodle_base_url.rstrip('/')}/course/view.php?id={course_id}"
