"""GitHub App JWT and installation-token authentication."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key


class InstallationTokenProvider(Protocol):
    def get_token(self, installation_id: int) -> str: ...


class GitHubAppConfigurationError(ValueError):
    """Raised when GitHub App key material is missing or invalid."""


class GitHubAppAuthenticator:
    def __init__(
        self,
        app_id: int,
        private_key: str | None = None,
        private_key_path: str | None = None,
        token_ttl_seconds: int = 540,
    ) -> None:
        self.app_id = app_id
        self.private_key = private_key
        self.private_key_path = private_key_path
        self.token_ttl_seconds = token_ttl_seconds

    def _load_private_key(self) -> str:
        if self.private_key:
            key = self.private_key
        elif self.private_key_path:
            try:
                key = Path(self.private_key_path).read_text(encoding="utf-8")
            except FileNotFoundError as exc:
                raise GitHubAppConfigurationError("GitHub App private-key path does not exist") from exc
            except (PermissionError, OSError) as exc:
                raise GitHubAppConfigurationError("GitHub App private-key path is not readable") from exc
        else:
            raise GitHubAppConfigurationError("GitHub App private key is not configured")
        try:
            load_pem_private_key(key.encode(), password=None)
        except (ValueError, TypeError) as exc:
            raise GitHubAppConfigurationError("GitHub App private key is invalid") from exc
        return key

    def validate(self) -> None:
        self._load_private_key()

    def build_app_jwt(self, now: datetime | None = None) -> str:
        issued_at = now or datetime.now(UTC)
        payload = {
            "iat": int((issued_at - timedelta(seconds=60)).timestamp()),
            "exp": int((issued_at + timedelta(seconds=self.token_ttl_seconds)).timestamp()),
            "iss": str(self.app_id),
        }
        try:
            return jwt.encode(payload, self._load_private_key(), algorithm="RS256")
        except GitHubAppConfigurationError:
            raise
        except (ValueError, TypeError) as exc:
            raise GitHubAppConfigurationError("GitHub App private key could not sign JWT") from exc
