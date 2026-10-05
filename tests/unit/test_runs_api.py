from fastapi.testclient import TestClient

from apps.api.app.github.repositories import RepositoryStore
from apps.api.app.main import app
from apps.api.app.storage.sqlite import RunStore


def test_create_run_returns_run_and_event_timeline(tmp_path) -> None:
    app.state.repository_store = RepositoryStore()
    app.state.repository_store.upsert_from_github({"id": 7, "full_name": "team/demo"}, 1)
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    client = TestClient(app)

    response = client.post(
        "/api/v1/repositories/7/runs",
        json={"trigger_type": "issue", "base_sha": "abcdef1"},
    )
    assert response.status_code == 201
    run = response.json()
    assert run["repository_id"] == 7
    assert run["status"] == "created"

    events = client.get(f"/api/v1/runs/{run['id']}/events")
    assert events.status_code == 200
    assert events.json()[0]["event_type"] == "run.created"


def test_create_run_requires_onboarded_repository(tmp_path) -> None:
    app.state.repository_store = RepositoryStore()
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    response = TestClient(app).post(
        "/api/v1/repositories/404/runs",
        json={"trigger_type": "issue", "base_sha": "abcdef1"},
    )
    assert response.status_code == 404
