from apps.api.app.storage.sqlite import RunStore
from apps.worker.worker.queue import RedisQueue, RunJob
from apps.worker.worker.runtime import RunWorker


class FakeRedis:
    def __init__(self):
        self.items = []

    def rpush(self, name, value):
        self.items.append(value)

    def lpop(self, name):
        return self.items.pop(0) if self.items else None


def test_worker_marks_success_and_records_events(tmp_path) -> None:
    store = RunStore(str(tmp_path / "runs.db"))
    run = store.create_run(1, "issue", "abcdef1")
    queue = RedisQueue(FakeRedis())
    queue.enqueue(RunJob(run_id=run["id"], repository_id=1))
    worker = RunWorker(queue, store, lambda job: None)
    assert worker.run_once() is True
    assert store.get_run(run["id"])["status"] == "succeeded"
    assert [event["event_type"] for event in store.list_events(run["id"])] == ["run.created", "run.started", "run.succeeded"]


def test_worker_retries_then_records_terminal_failure(tmp_path) -> None:
    store = RunStore(str(tmp_path / "runs.db"))
    run = store.create_run(1, "issue", "abcdef1")
    queue = RedisQueue(FakeRedis())
    queue.enqueue(RunJob(run_id=run["id"], repository_id=1))
    worker = RunWorker(queue, store, lambda job: (_ for _ in ()).throw(RuntimeError("boom")), max_attempts=2)
    worker.run_once()
    assert store.get_run(run["id"])["status"] == "queued"
    worker.run_once()
    assert store.get_run(run["id"])["status"] == "failed"
    assert store.list_events(run["id"])[-1]["event_type"] == "run.failed"
