from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
