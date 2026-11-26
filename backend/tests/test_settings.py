from app.core.config import Settings


def test_defaults_allow_the_local_frontend():
    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["http://localhost:3000"]


def test_cors_origins_can_be_set_from_env_as_comma_separated(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://tutomind.example")

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["http://localhost:3000", "https://tutomind.example"]
