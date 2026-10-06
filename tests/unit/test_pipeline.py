import subprocess

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


def git(path, *args):
    return subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True).stdout.strip()


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


def test_pipeline_applies_patch_and_runs_workspace_validation(tmp_path) -> None:
    repository = tmp_path / "source"
    repository.mkdir()
    git(repository, "init", "-b", "main")
    git(repository, "config", "user.name", "Test")
    git(repository, "config", "user.email", "test@example.com")
    (repository / "parser.py").write_text("VALUE = 1\n")
    git(repository, "add", "parser.py")
    git(repository, "commit", "-m", "initial")
    base_sha = git(repository, "rev-parse", "HEAD")

    store = RunStore(str(tmp_path / "runs.db"))
    run = store.create_run(1, "issue", base_sha)
    queue = RedisQueue(FakeRedis())
    queue.enqueue(
        RunJob(
            run_id=run["id"],
            repository_id=1,
            base_sha=base_sha,
            repository_url=str(repository),
            patch="""diff --git a/parser.py b/parser.py
--- a/parser.py
+++ b/parser.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
""",
        )
    )
    dispatcher = StageDispatcher(store, queue, LocalCheckPublisher(), str(tmp_path / "workspaces"))
    worker = RunWorker(queue, store, dispatcher.dispatch)
    while worker.run_once():
        if store.get_run(run["id"])["status"] == "succeeded":
            break

    assert store.get_run(run["id"])["status"] == "succeeded"
    assert any(event["event_type"] == "run.implemented" for event in store.list_events(run["id"]))
