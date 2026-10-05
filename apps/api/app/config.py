"""Environment-backed API configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RepoPilot API"
    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://repopilot:repopilot@localhost:5432/repopilot"
    redis_url: str = "redis://localhost:6379/0"
    database_path: str = ".local/repopilot.db"
    storage_backend: str = "sqlite"
    github_webhook_secret: str | None = None
    github_app_id: int | None = None
    github_app_private_key: str | None = None
    github_app_private_key_path: str | None = None
    github_owner: str | None = None
    github_repository: str | None = None

    @property
    def github_credentials_configured(self) -> bool:
        return bool(
            self.github_app_id
            and (self.github_app_private_key or self.github_app_private_key_path)
            and self.github_webhook_secret
        )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
