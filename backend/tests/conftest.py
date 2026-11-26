from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import Course, Enrollment, User
from app.db.session import get_session
from app.main import create_app

# Shared database fixtures (embedded PostgreSQL + pgvector); see tests/db_fixtures.py.
from tests.db_fixtures import database_url, engine, session  # noqa: F401

TEST_SECRET = "test-secret-" + "x" * 32


@pytest.fixture
def client() -> TestClient:
    # raise_server_exceptions=False: we assert on the HTTP response, not on a re-raised exception.
    return TestClient(create_app(), raise_server_exceptions=False)


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, jwt_secret=TEST_SECRET, access_token_expires_seconds=3600)


@pytest.fixture
def api(session: Session, settings: Settings) -> Iterator[TestClient]:  # noqa: F811
    """The real app wired to the rollback-per-test database session."""
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_settings] = lambda: settings
    yield TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def make_user(session: Session):  # noqa: F811
    """Factory: persists a user (enrolled in course `c1`) and returns it."""
    from app.core.passwords import hash_password

    if session.get(Course, "c1") is None:
        session.add(Course(id="c1", name="Cálculo"))
        session.flush()

    def _make(
        user_id: str = "u1",
        role: str = "student",
        email: str | None = None,
        password: str = "demo12345",
    ) -> User:
        user = User(
            id=user_id,
            name=f"Usuario {user_id}",
            email=email or f"{user_id}@tutomind.demo",
            role=role,
            password_hash=hash_password(password),
        )
        session.add(user)
        session.flush()
        session.add(Enrollment(course_id="c1", user_id=user.id))
        session.flush()
        return user

    return _make
