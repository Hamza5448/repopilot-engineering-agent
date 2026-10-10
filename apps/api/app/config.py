"""Environment-backed API configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from packages.github.auth import GitHubAppAuthenticator, GitHubAppConfigurationError


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
    openai_api_key: str | None = None
    openai_model: str | None = None

    @property
    def github_credentials_configured(self) -> bool:
        if not self.github_app_id or not self.github_webhook_secret:
            return False
        try:
            GitHubAppAuthenticator(
                self.github_app_id,
                private_key=self.github_app_private_key,
                private_key_path=self.github_app_private_key_path,
            ).validate()
        except GitHubAppConfigurationError:
            return False
        return True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
