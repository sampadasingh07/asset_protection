from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "VeriLens Backend"
    environment: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./verilens.db"
    jwt_secret_key: str = "development-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    redis_url: str = "redis://localhost:6379/0"
    task_mode: str = "eager"
    upload_dir: str = "uploads"
    max_search_results: int = 5
    alert_similarity_threshold: float = 0.85
    default_org_name: str = "Demo Organisation"
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()

