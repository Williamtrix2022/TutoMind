from datetime import UTC, datetime

from app.core.config import Settings
from app.services.moodle import (
    MoodleWebServiceClient,
    SimulatedMoodleClient,
    get_moodle_client,
    moodle_course_url,
)

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


def test_the_simulation_is_deterministic_for_a_given_moment():
    client = SimulatedMoodleClient()

    assert client.fetch_events("demo", NOW) == client.fetch_events("demo", NOW)


def test_the_simulation_covers_every_kind_of_event_and_says_it_is_simulated():
    events = SimulatedMoodleClient().fetch_events("demo", NOW)

    assert {e.type for e in events} == {"login", "grade", "submission", "missed_deadline"}
    assert {e.source for e in events} == {"simulated"}
    assert all(e.occurred_at <= NOW for e in events)


def test_the_simulation_only_knows_the_demo_course():
    assert SimulatedMoodleClient().fetch_events("101", NOW) == []


def test_without_configuration_the_simulation_is_used():
    client = get_moodle_client(Settings(_env_file=None))

    assert isinstance(client, SimulatedMoodleClient)


def test_with_url_and_token_the_real_client_is_used():
    settings = Settings(
        _env_file=None, moodle_base_url="https://moodle.example.edu", moodle_token="t"
    )

    assert isinstance(get_moodle_client(settings), MoodleWebServiceClient)


def test_a_url_without_a_token_fails_loudly_instead_of_faking_data():
    import pytest

    from app.services.moodle import MoodleError

    settings = Settings(_env_file=None, moodle_base_url="https://moodle.example.edu")

    with pytest.raises(MoodleError, match="MOODLE_TOKEN"):
        get_moodle_client(settings)


class TestCourseUrl:
    def test_points_at_the_course_page_when_moodle_is_configured(self):
        settings = Settings(_env_file=None, moodle_base_url="https://moodle.example.edu/")

        assert (
            moodle_course_url(settings, "101")
            == "https://moodle.example.edu/course/view.php?id=101"
        )

    def test_no_link_without_a_moodle_url(self):
        assert moodle_course_url(Settings(_env_file=None), "101") is None

    def test_no_link_for_courses_that_are_not_moodle_ids(self):
        settings = Settings(_env_file=None, moodle_base_url="https://moodle.example.edu")

        assert moodle_course_url(settings, "demo") is None


def test_the_moodle_url_must_be_http():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="MOODLE_BASE_URL"):
        Settings(_env_file=None, moodle_base_url="moodle.example.edu")
