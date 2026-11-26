"""Integration fixtures: a real PostgreSQL + pgvector, no Docker required.

By default an embedded server (`pgserver`) is started once per test session. Point
`TEST_DATABASE_URL` at any PostgreSQL with the `vector` extension to use it instead
(the schema is dropped and recreated, so use a throwaway database).
"""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]


def to_sqlalchemy_url(url: str) -> str:
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    external = os.environ.get("TEST_DATABASE_URL")
    if external:
        yield to_sqlalchemy_url(external)
        return

    import pgserver

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as data_dir:
        server = pgserver.get_server(data_dir)
        try:
            yield to_sqlalchemy_url(server.get_uri())
        finally:
            server.cleanup()


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    command.upgrade(alembic_config(database_url), "head")
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """A session whose changes are rolled back at the end of each test."""
    connection = engine.connect()
    transaction = connection.begin()
    db = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()
