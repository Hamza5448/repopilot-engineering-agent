import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from apps.api.app.github.webhooks import DeliveryStore, InvalidWebhookSignature, verify_signature
from apps.api.app.main import app, settings

SECRET = "unit-test-secret"


def signed(body: bytes) -> str:
    digest = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_signature_verification_accepts_valid_payload() -> None:
    body = b'{"action":"opened"}'
    verify_signature(body, signed(body), SECRET)


def test_signature_verification_rejects_tampering() -> None:
    with __import__("pytest").raises(InvalidWebhookSignature):
        verify_signature(b"tampered", signed(b"original"), SECRET)


def test_delivery_store_is_idempotent() -> None:
    store = DeliveryStore(max_entries=2)
    assert store.claim("one") is True
    assert store.claim("one") is False
    assert store.claim("two") is True
    assert store.claim("three") is True
    assert store.claim("one") is True


def test_github_webhook_accepts_and_deduplicates(monkeypatch) -> None:
    monkeypatch.setattr(settings, "github_webhook_secret", SECRET)
    app.state.delivery_store = DeliveryStore()
    body = json.dumps(
        {"action": "opened", "issue": {"number": 1}, "repository": {"id": 42}}
    ).encode()
    headers = {
        "x-github-delivery": "delivery-1",
        "x-github-event": "issues",
        "x-hub-signature-256": signed(body),
    }
    client = TestClient(app)
    first = client.post("/webhooks/github", content=body, headers=headers)
    second = client.post("/webhooks/github", content=body, headers=headers)
    assert first.status_code == 202
    assert first.json()["status"] == "accepted"
    assert second.status_code == 202
    assert second.json()["status"] == "duplicate"
