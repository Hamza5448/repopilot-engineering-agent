"""GitHub App JWT and installation-token authentication."""

from datetime import UTC, datetime, timedelta
from typing import Protocol

import jwt


class InstallationTokenProvider(Protocol):
    def get_token(self, installation_id: int) -> str: ...


class GitHubAppAuthenticator:
    def __init__(self, app_id: int, private_key: str, token_ttl_seconds: int = 540) -> None:
        self.app_id = app_id
        self.private_key = private_key
        self.token_ttl_seconds = token_ttl_seconds

    def build_app_jwt(self, now: datetime | None = None) -> str:
        issued_at = now or datetime.now(UTC)
        payload = {
            "iat": int((issued_at - timedelta(seconds=60)).timestamp()),
            "exp": int((issued_at + timedelta(seconds=self.token_ttl_seconds)).timestamp()),
            "iss": str(self.app_id),
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")
