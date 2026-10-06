from apps.api.app.storage.sqlite import RunStore
from apps.worker.worker.main import handle_job
from apps.worker.worker.queue import RunJob


def test_worker_stage_handler_records_auditable_completion(tmp_path) -> None:
    store = RunStore(str(tmp_path / "runs.db"))
    run = store.create_run(1, "issue", "abcdef1")
    handle_job(RunJob(run_id=run["id"], repository_id=1, stage="triage"), store)
    assert store.list_events(run["id"])[-1]["event_type"] == "run.stage.completed"
