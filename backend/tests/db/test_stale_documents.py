from contextlib import nullcontext
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.db.models import Course, Document
from app.main import create_app
from app.services.ingestion import (
    STALE_AFTER,
    STALE_MESSAGE,
    STARTUP_GRACE,
    fail_stale_documents,
)

NOW = datetime(2026, 11, 28, 12, 0, tzinfo=UTC)
PDF = "application/pdf"


@pytest.fixture
def docs(session):
    session.add_all([Course(id="c1", name="A"), Course(id="c2", name="B")])
    session.flush()

    def add(doc_id, status, minutes_old, course="c1"):
        session.add(
            Document(
                id=doc_id, course_id=course, filename=f"{doc_id}.pdf", mime_type=PDF,
                size_bytes=10, status=status, created_at=NOW - timedelta(minutes=minutes_old),
            )
        )  # fmt: skip
        session.flush()

    return add


def status_of(session, doc_id):
    return session.get(Document, doc_id).status


def test_documents_stuck_in_progress_are_failed_with_a_clear_reason(session, docs):
    docs("queued-old", "queued", 30)
    docs("processing-old", "processing", 30)

    count = fail_stale_documents(session, NOW, STALE_AFTER)

    assert count == 2
    for doc_id in ("queued-old", "processing-old"):
        session.refresh(session.get(Document, doc_id))
        assert status_of(session, doc_id) == "failed"
        assert session.get(Document, doc_id).error_message == STALE_MESSAGE


def test_recent_documents_are_left_alone(session, docs):
    docs("fresh", "processing", 1)

    assert fail_stale_documents(session, NOW, STALE_AFTER) == 0
    assert status_of(session, "fresh") == "processing"


def test_finished_documents_are_never_touched(session, docs):
    docs("done", "indexed", 600)
    docs("broken", "failed", 600)
    session.get(Document, "broken").error_message = "Su propio motivo."
    session.flush()

    assert fail_stale_documents(session, NOW, STALE_AFTER) == 0
    assert status_of(session, "done") == "indexed"
    assert session.get(Document, "broken").error_message == "Su propio motivo."


def test_the_age_limit_is_exclusive_at_the_boundary(session, docs):
    docs("edge", "processing", STALE_AFTER.total_seconds() / 60)

    assert fail_stale_documents(session, NOW, STALE_AFTER) == 0


def test_it_can_be_limited_to_one_course(session, docs):
    docs("mine", "processing", 30, course="c1")
    docs("theirs", "processing", 30, course="c2")

    assert fail_stale_documents(session, NOW, STALE_AFTER, course_id="c1") == 1
    assert status_of(session, "mine") == "failed"
    assert status_of(session, "theirs") == "processing"


def test_running_it_twice_changes_nothing_the_second_time(session, docs):
    docs("old", "processing", 30)
    fail_stale_documents(session, NOW, STALE_AFTER)

    assert fail_stale_documents(session, NOW, STALE_AFTER) == 0


def test_the_startup_grace_is_shorter_than_the_listing_limit():
    assert STARTUP_GRACE < STALE_AFTER


class TestOnStartup:
    @pytest.fixture
    def with_session(self, session, monkeypatch):
        monkeypatch.setattr(
            main_module, "get_session_factory", lambda: lambda: nullcontext(session)
        )

    def test_documents_abandoned_by_a_restart_are_failed_when_the_server_boots(
        self, session, docs, with_session
    ):
        now = datetime.now(UTC)
        docs("abandoned", "processing", 0)
        session.get(Document, "abandoned").created_at = now - timedelta(minutes=5)
        docs("just-uploaded", "queued", 0)
        session.get(Document, "just-uploaded").created_at = now - timedelta(seconds=20)
        session.flush()

        with TestClient(create_app()):
            pass

        assert status_of(session, "abandoned") == "failed"
        assert status_of(session, "just-uploaded") == "queued"  # inside the grace period

    def test_a_database_failure_at_boot_does_not_stop_the_server(self, monkeypatch):
        def broken():
            raise RuntimeError("database unreachable")

        monkeypatch.setattr(main_module, "get_session_factory", broken)

        with TestClient(create_app()) as client:
            assert client.get("/health").status_code == 200
