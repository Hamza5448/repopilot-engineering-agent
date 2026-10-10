from fastapi.testclient import TestClient

from apps.api.app.github.repositories import RepositoryStore
from apps.api.app.main import app
from apps.api.app.storage.sqlite import RunStore


class FakeQueue:
    def __init__(self):
        self.jobs = []

    def enqueue(self, job):
        self.jobs.append(job)


def test_create_run_returns_run_and_event_timeline(tmp_path) -> None:
    app.state.repository_store = RepositoryStore()
    app.state.repository_store.upsert_from_github({"id": 7, "full_name": "team/demo"}, 1)
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    app.state.queue = FakeQueue()
    client = TestClient(app)

    response = client.post(
        "/api/v1/repositories/7/runs",
        json={"trigger_type": "issue", "base_sha": "abcdef1"},
    )
    assert response.status_code == 201
    run = response.json()
    assert run["repository_id"] == 7
    assert run["status"] == "created"
    assert app.state.queue.jobs[0].run_id == run["id"]

    events = client.get(f"/api/v1/runs/{run['id']}/events")
    assert events.status_code == 200
    assert events.json()[0]["event_type"] == "run.created"


def test_create_run_requires_onboarded_repository(tmp_path) -> None:
    app.state.repository_store = RepositoryStore()
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    app.state.queue = FakeQueue()
    response = TestClient(app).post(
        "/api/v1/repositories/404/runs",
        json={"trigger_type": "issue", "base_sha": "abcdef1"},
    )
    assert response.status_code == 404


def test_list_runs_returns_recent_runs(tmp_path) -> None:
    app.state.repository_store = RepositoryStore()
    app.state.repository_store.upsert_from_github({"id": 8, "full_name": "team/list"}, 1)
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    app.state.queue = FakeQueue()
    created = app.state.run_store.create_run(8, "issue", "abcdef1")
    response = TestClient(app).get("/api/v1/runs?limit=10")
    assert response.status_code == 200
    assert response.json()[0]["id"] == created["id"]
