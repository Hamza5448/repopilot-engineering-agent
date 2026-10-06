import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from apps.api.app.github.repositories import RepositoryStore
from apps.api.app.github.webhooks import DeliveryStore
from apps.api.app.main import app, settings
from apps.api.app.storage.sqlite import RunStore


class FakeQueue:
    def __init__(self):
        self.jobs = []

    def enqueue(self, job):
        self.jobs.append(job)


def test_labeled_issue_creates_exact_sha_run(monkeypatch, tmp_path) -> None:
    secret = "test-webhook-secret"
    monkeypatch.setattr(settings, "github_webhook_secret", secret)
    app.state.delivery_store = DeliveryStore()
    app.state.repository_store = RepositoryStore()
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    app.state.queue = FakeQueue()
    app.state.github_sha_resolver = lambda owner, repository, branch, installation_id: "exact-base-sha"
    payload = {
        "action": "labeled",
        "installation": {"id": 55},
        "repository": {"id": 123, "full_name": "owner/repo", "default_branch": "main"},
        "issue": {"title": "Fix parser", "body": "Please fix it", "labels": [{"name": "repopilot"}]},
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    response = TestClient(app).post(
        "/webhooks/github",
        content=body,
        headers={
            "x-github-delivery": "issue-trigger-1",
            "x-github-event": "issues",
            "x-hub-signature-256": signature,
        },
    )
    assert response.status_code == 202
    assert len(app.state.queue.jobs) == 1
    assert app.state.queue.jobs[0].base_sha == "exact-base-sha"
    assert app.state.queue.jobs[0].issue_title == "Fix parser"


def test_unlabeled_issue_is_acknowledged_without_creating_run(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "github_webhook_secret", "test-webhook-secret")
    app.state.delivery_store = DeliveryStore()
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    app.state.queue = FakeQueue()
    body = json.dumps({"action": "opened", "issue": {"labels": []}}).encode()
    signature = "sha256=" + hmac.new(b"test-webhook-secret", body, hashlib.sha256).hexdigest()
    response = TestClient(app).post(
        "/webhooks/github",
        content=body,
        headers={
            "x-github-delivery": "issue-trigger-2",
            "x-github-event": "issues",
            "x-hub-signature-256": signature,
        },
    )
    assert response.status_code == 202
    assert app.state.queue.jobs == []
