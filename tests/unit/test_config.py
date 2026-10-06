from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

from apps.api.app.config import Settings


def test_github_configuration_status_does_not_expose_secret() -> None:
    settings = Settings(
        github_app_id=123,
        github_app_private_key=rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode(),
        github_webhook_secret="secret",
    )
    assert settings.github_credentials_configured is True
    assert "secret" not in str(settings.github_credentials_configured)


def test_github_configuration_requires_app_id_key_and_webhook_secret() -> None:
    settings = Settings(github_app_private_key="private-key")
    assert settings.github_credentials_configured is False
