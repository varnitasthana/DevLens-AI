from functools import lru_cache
from pydantic import field_validator
from pydantic import model_validator

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
    ai_base_url: str | None = None
    ai_api_key: str | None = None
    ai_model: str = "devlens-reviewer"
    ai_timeout_seconds: float = 20.0
    github_token: str | None = None
    auth_secret_key: str = "devlens-change-this-secret"
    auth_token_expire_minutes: int = 60
    redis_url: str | None = None
    rate_limit_window_seconds: int = 60
    rate_limit_requests: int = 30
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False
    analysis_upload_dir: str = ".devlens/uploads"
    chat_max_files: int = 8
    chat_max_context_chars: int = 24_000
    s3_endpoint_url: str | None = None
    s3_bucket_name: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str | None = None

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        if self.app_env.lower() not in {"development", "test"}:
            if self.auth_secret_key == "devlens-change-this-secret":
                raise ValueError("AUTH_SECRET_KEY must be configured outside development")
            if self.database_url.endswith("/devlens") and "devlens-dev-password" in self.database_url:
                raise ValueError("Production database credentials must be configured")
            if not self.redis_url:
                raise ValueError("REDIS_URL must be configured outside development")
        return self

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
