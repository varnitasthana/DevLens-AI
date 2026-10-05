from functools import lru_cache
from pydantic import field_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DevLens API"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://devlens:devlens-dev-password@localhost:5432/devlens"
    cors_origins: list[str] = ["http://localhost:5173"]
    max_archive_size_bytes: int = 50 * 1024 * 1024
    max_repository_size_bytes: int = 200 * 1024 * 1024
    max_file_size_bytes: int = 10 * 1024 * 1024
    max_file_count: int = 10_000

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
