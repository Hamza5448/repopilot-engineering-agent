from fastapi.testclient import TestClient

from apps.api.app.github.repositories import RepositoryStore
from apps.api.app.main import app
from apps.api.app.storage.sqlite import RunStore
from apps.worker.worker.pipeline import LocalCheckPublisher, StageDispatcher
from apps.worker.worker.queue import RedisQueue, RunJob
from apps.worker.worker.runtime import RunWorker


class FakeRedis:
    def __init__(self):
        self.items = []

    def rpush(self, name, value):
        self.items.append(value)

    def lpop(self, name):
        return self.items.pop(0) if self.items else None


def test_approval_gate_pauses_and_resumes_publish_job(tmp_path) -> None:
    store = RunStore(str(tmp_path / "runs.db"))
    run = store.create_run(7, "github_issue", "abcdef1")
    queue = RedisQueue(FakeRedis())
    queue.enqueue(RunJob(run_id=run["id"], repository_id=7, require_approval=True))
    dispatcher = StageDispatcher(store, queue, LocalCheckPublisher(), str(tmp_path / "workspaces"))
    worker = RunWorker(queue, store, dispatcher.dispatch)

    while worker.run_once():
        if store.get_run(run["id"])["status"] == "waiting_for_approval":
            break

    assert store.get_run(run["id"])["status"] == "waiting_for_approval"
    pending = [event for event in store.list_events(run["id"]) if event["event_type"] == "run.waiting_for_approval"]
    assert pending[0]["payload"]["job"]["stage"] == "publish"

    app.state.repository_store = RepositoryStore()
    app.state.run_store = store
    app.state.queue = queue
    response = TestClient(app).post(
        f"/api/v1/runs/{run['id']}/approve",
        json={"gate": "publication", "rationale": "approved for controlled test"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    resumed = queue.dequeue()
    assert resumed is not None
    assert resumed.stage == "publish"

    queue.enqueue(resumed)
    while worker.run_once():
        if store.get_run(run["id"])["status"] == "succeeded":
            break
    assert store.get_run(run["id"])["status"] == "succeeded"
