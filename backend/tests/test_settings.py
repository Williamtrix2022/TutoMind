from app.core.config import Settings


def test_defaults_allow_the_local_frontend():
    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["http://localhost:3000"]


def test_cors_origins_can_be_set_from_env_as_comma_separated(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://tutomind.example")

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["http://localhost:3000", "https://tutomind.example"]


def test_database_url_without_driver_gets_psycopg(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db?sslmode=require")

    assert (
        Settings(_env_file=None).database_url == "postgresql+psycopg://u:p@host/db?sslmode=require"
    )


def test_database_url_postgres_scheme_gets_psycopg(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host/db")

    assert Settings(_env_file=None).database_url == "postgresql+psycopg://u:p@host/db"


def test_database_url_with_driver_is_left_alone(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host/db")

    assert Settings(_env_file=None).database_url == "postgresql+psycopg://u:p@host/db"
