from fastapi.testclient import TestClient

from apps.api.app.github.repositories import RepositoryStore
from apps.api.app.main import app
from apps.api.app.storage.sqlite import RunStore


def test_plan_run_persists_structured_plan_event(tmp_path) -> None:
    app.state.repository_store = RepositoryStore()
    app.state.repository_store.upsert_from_github({"id": 11, "full_name": "team/planner"}, 1)
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    client = TestClient(app)
    created = client.post(
        "/api/v1/repositories/11/runs",
        json={"trigger_type": "issue", "base_sha": "abcdef1"},
    ).json()

    response = client.post(
        f"/api/v1/runs/{created['id']}/plan",
        json={
            "issue_title": "Fix parser validation",
            "issue_body": "Parser rejects valid input",
            "files": [
                {"path": "parser.py", "content": "def parse(): pass"},
                {"path": "README.md", "content": "project overview"},
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["steps"][0]["order"] == 1

    events = client.get(f"/api/v1/runs/{created['id']}/events").json()
    assert [event["event_type"] for event in events] == ["run.created", "run.planned"]
    assert events[1]["payload"]["context"]["base_sha"] == "abcdef1"


def test_plan_run_requires_existing_run(tmp_path) -> None:
    app.state.run_store = RunStore(str(tmp_path / "runs.db"))
    response = TestClient(app).post(
        "/api/v1/runs/missing/plan",
        json={"issue_title": "Missing run"},
    )
    assert response.status_code == 404
