from fastapi.testclient import TestClient

from apps.api.app.github.repositories import RepositoryStore
from apps.api.app.main import app
from apps.api.app.storage.sqlite import RunStore


def setup_run(tmp_path, status="waiting_for_approval"):
    app.state.repository_store = RepositoryStore()
    app.state.repository_store.upsert_from_github({"id": 21, "full_name": "team/controls"}, 1)
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    run = app.state.run_store.create_run(21, "issue", "abcdef1")
    app.state.run_store.update_status(run["id"], status)
    return TestClient(app), run["id"]


def test_approval_resumes_waiting_run(tmp_path) -> None:
    client, run_id = setup_run(tmp_path)
    response = client.post(f"/api/v1/runs/{run_id}/approve", json={"gate": "publication", "rationale": "approved"})
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_rejection_fails_waiting_run(tmp_path) -> None:
    client, run_id = setup_run(tmp_path)
    response = client.post(f"/api/v1/runs/{run_id}/reject", json={"rationale": "too risky"})
    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_cancel_stops_nonterminal_run(tmp_path) -> None:
    client, run_id = setup_run(tmp_path, status="queued")
    response = client.post(f"/api/v1/runs/{run_id}/cancel", json={"rationale": "user requested"})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
