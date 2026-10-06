import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from apps.api.app.github.repositories import RepositoryStore
from apps.api.app.github.webhooks import DeliveryStore
from apps.api.app.main import app, settings
from apps.api.app.storage.sqlite import RunStore
from apps.worker.worker.pipeline import LocalCheckPublisher, StageDispatcher
from apps.worker.worker.queue import RedisQueue, RunJob
from apps.worker.worker.runtime import RunWorker


class FakeQueue:
    def __init__(self):
        self.jobs = []

    def enqueue(self, job):
        self.jobs.append(job)


class FakeRedis:
    def __init__(self):
        self.items = []

    def rpush(self, name, value):
        self.items.append(value)

    def lpop(self, name):
        return self.items.pop(0) if self.items else None


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
    assert app.state.queue.jobs[0].installation_id == 55
    assert app.state.queue.jobs[0].github_owner == "owner"
    assert app.state.queue.jobs[0].github_repository == "repo"
    assert app.state.queue.jobs[0].issue_title == "Fix parser"
    run = app.state.run_store.get_run(app.state.queue.jobs[0].run_id)
    assert run["trigger_type"] == "github_issue"
    assert [event["event_type"] for event in app.state.run_store.list_events(run["id"])] == [
        "run.created",
        "run.trigger.accepted",
        "run.enqueued",
    ]


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


def test_webhook_queue_worker_dispatch_boundary(monkeypatch, tmp_path) -> None:
    secret = "test-webhook-secret"
    monkeypatch.setattr(settings, "github_webhook_secret", secret)
    app.state.delivery_store = DeliveryStore()
    app.state.repository_store = RepositoryStore()
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    redis_client = FakeRedis()
    queue = RedisQueue(redis_client)
    app.state.queue = queue
    app.state.github_sha_resolver = lambda owner, repository, branch, installation_id: "exact-base-sha"
    payload = {
        "action": "labeled",
        "installation": {"id": 55},
        "repository": {"id": 123, "full_name": "owner/repo", "default_branch": "main"},
        "issue": {"title": "Run boundary", "labels": [{"name": "repopilot"}]},
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    response = TestClient(app).post(
        "/webhooks/github",
        content=body,
        headers={
            "x-github-delivery": "issue-trigger-boundary",
            "x-github-event": "issues",
            "x-hub-signature-256": signature,
        },
    )
    assert response.status_code == 202
    assert redis_client.items
    job = queue.dequeue()
    assert job is not None
    stored_run = app.state.run_store.get_run(job.run_id)
    worker_queue = RedisQueue(FakeRedis())
    worker_queue.enqueue(RunJob.model_validate(job.model_dump()))
    worker = RunWorker(
        worker_queue,
        app.state.run_store,
        StageDispatcher(app.state.run_store, worker_queue, LocalCheckPublisher()).dispatch,
    )
    while worker.run_once():
        if not worker_queue.client.items:
            break
    assert app.state.run_store.get_run(stored_run["id"])["status"] == "succeeded"


def test_failed_enqueue_releases_delivery_for_retry(monkeypatch, tmp_path) -> None:
    secret = "test-webhook-secret"
    monkeypatch.setattr(settings, "github_webhook_secret", secret)
    app.state.delivery_store = DeliveryStore()
    app.state.repository_store = RepositoryStore()
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    app.state.github_sha_resolver = lambda owner, repository, branch, installation_id: "exact-base-sha"
    payload = {
        "action": "labeled",
        "installation": {"id": 55},
        "repository": {"id": 123, "full_name": "owner/repo", "default_branch": "main"},
        "issue": {"title": "Retry enqueue", "labels": [{"name": "repopilot"}]},
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    app.state.queue = FakeQueue()
    app.state.queue.enqueue = lambda job: (_ for _ in ()).throw(RuntimeError("redis unavailable"))
    failed = TestClient(app).post(
        "/webhooks/github",
        content=body,
        headers={
            "x-github-delivery": "issue-trigger-retry",
            "x-github-event": "issues",
            "x-hub-signature-256": signature,
        },
    )
    assert failed.status_code == 503
    app.state.queue = FakeQueue()
    retried = TestClient(app).post(
        "/webhooks/github",
        content=body,
        headers={
            "x-github-delivery": "issue-trigger-retry",
            "x-github-event": "issues",
            "x-hub-signature-256": signature,
        },
    )
    assert retried.status_code == 202
    assert len(app.state.queue.jobs) == 1
