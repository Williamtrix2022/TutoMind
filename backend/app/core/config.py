from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-insecure-secret-change-me-0123456789"


class Settings(BaseSettings):
    """Application settings, read from environment variables or a local `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TutoMind API"
    environment: str = "development"
    # NoDecode: accept "a,b" from the environment instead of requiring a JSON list.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Matches docker-compose.yml. Development credentials only.
    database_url: str = "postgresql+psycopg://tutomind:tutomind@localhost:5432/tutomind"
    # Size of the embedding vectors stored in pgvector. Changing it needs a new migration.
    embedding_dimensions: int = 1024

    # IA gratuita (Google AI Studio). La clave se crea en https://aistudio.google.com/apikey
    gemini_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"

    # Moodle Web Services. Empty = no Moodle: simulated demo data is used (services/moodle.py).
    moodle_base_url: str = ""
    moodle_token: str = ""

    # Signs access tokens (HS256). The default only exists for local development.
    jwt_secret: str = DEV_JWT_SECRET
    access_token_expires_seconds: int = 3600

    @model_validator(mode="after")
    def require_a_real_secret_outside_development(self) -> "Settings":
        if self.environment != "development" and (
            self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < 32
        ):
            raise ValueError(
                "JWT_SECRET must be set to a random value of at least 32 characters "
                f"when ENVIRONMENT is '{self.environment}'."
            )
        return self

    @field_validator("moodle_base_url")
    @classmethod
    def moodle_url_must_be_http(cls, value: str) -> str:
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("MOODLE_BASE_URL must start with http:// or https://")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
