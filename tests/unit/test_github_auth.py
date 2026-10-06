from datetime import UTC, datetime

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

from packages.github.auth import GitHubAppAuthenticator, GitHubAppConfigurationError


def private_key() -> str:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    ).decode()


def test_app_jwt_contains_github_app_claims(monkeypatch) -> None:
    captured = {}

    def fake_encode(payload, key, algorithm):
        captured.update(payload=payload, key=key, algorithm=algorithm)
        return "signed-jwt"

    monkeypatch.setattr(jwt, "encode", fake_encode)
    token = GitHubAppAuthenticator(123, private_key=private_key()).build_app_jwt(
        datetime(2026, 1, 1, tzinfo=UTC)
    )
    assert token == "signed-jwt"
    assert captured["payload"]["iss"] == "123"
    assert captured["algorithm"] == "RS256"


def test_authenticator_loads_pem_from_configured_path(tmp_path) -> None:
    path = tmp_path / "github-app.pem"
    path.write_text(private_key(), encoding="utf-8")
    token = GitHubAppAuthenticator(123, private_key_path=str(path)).build_app_jwt()
    assert isinstance(token, str)


def test_authenticator_fails_safely_for_missing_or_invalid_key(tmp_path) -> None:
    with pytest.raises(GitHubAppConfigurationError, match="does not exist"):
        GitHubAppAuthenticator(123, private_key_path=str(tmp_path / "missing.pem")).build_app_jwt()
    invalid = tmp_path / "invalid.pem"
    invalid.write_text("not-a-private-key", encoding="utf-8")
    with pytest.raises(GitHubAppConfigurationError, match="invalid"):
        GitHubAppAuthenticator(123, private_key_path=str(invalid)).build_app_jwt()
