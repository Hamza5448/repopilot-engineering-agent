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


def test_queued_run_completes_all_pipeline_stages(tmp_path) -> None:
    store = RunStore(str(tmp_path / "runs.db"))
    run = store.create_run(1, "issue", "abcdef1")
    queue = RedisQueue(FakeRedis())
    queue.enqueue(RunJob(run_id=run["id"], repository_id=1, issue_title="Fix parser"))
    dispatcher = StageDispatcher(store, queue, LocalCheckPublisher(), str(tmp_path / "workspaces"))
    worker = RunWorker(queue, store, dispatcher.dispatch)

    while worker.run_once():
        if store.get_run(run["id"])["status"] == "succeeded":
            break

    assert store.get_run(run["id"])["status"] == "succeeded"
    event_types = [event["event_type"] for event in store.list_events(run["id"])]
    assert "run.triaged" in event_types
    assert "run.planned" in event_types
    assert "run.validated" in event_types
    assert "run.check.published" in event_types
