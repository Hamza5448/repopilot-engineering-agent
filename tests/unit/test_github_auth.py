from datetime import UTC, datetime

import jwt

from packages.github.auth import GitHubAppAuthenticator


def test_app_jwt_contains_github_app_claims(monkeypatch) -> None:
    captured = {}

    def fake_encode(payload, key, algorithm):
        captured.update(payload=payload, key=key, algorithm=algorithm)
        return "signed-jwt"

    monkeypatch.setattr(jwt, "encode", fake_encode)
    token = GitHubAppAuthenticator(123, "private-key").build_app_jwt(
        datetime(2026, 1, 1, tzinfo=UTC)
    )
    assert token == "signed-jwt"
    assert captured["payload"]["iss"] == "123"
    assert captured["algorithm"] == "RS256"
