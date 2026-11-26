from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from app.core.config import Settings
from app.db.base import Base
from tests.db.conftest import alembic_config

EXPECTED_TABLES = {
    "users",
    "courses",
    "enrollments",
    "documents",
    "document_chunks",
    "conversations",
    "messages",
}


def test_upgrade_creates_every_table_and_the_vector_extension(engine):
    tables = set(inspect(engine).get_table_names())

    assert EXPECTED_TABLES <= tables
    with engine.connect() as connection:
        extension = connection.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
    assert extension == "vector"


def test_models_and_migrations_describe_the_same_schema(engine):
    """No drift: autogenerate against the migrated database must find nothing to change."""
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert diff == []


def test_vector_dimension_in_models_matches_the_setting(engine):
    with engine.connect() as connection:
        dimension = connection.execute(
            text(
                "SELECT atttypmod FROM pg_attribute "
                "WHERE attrelid = 'document_chunks'::regclass AND attname = 'embedding'"
            )
        ).scalar()

    assert dimension == Settings(_env_file=None).embedding_dimensions


def test_downgrade_then_upgrade_round_trips(engine, database_url):
    config = alembic_config(database_url)

    command.downgrade(config, "base")
    assert not (EXPECTED_TABLES & set(inspect(engine).get_table_names()))

    command.upgrade(config, "head")
    assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())
