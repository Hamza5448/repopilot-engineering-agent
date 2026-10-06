"""Durable worker loop for queued RepoPilot runs."""

from collections.abc import Callable
from typing import Any, Protocol

from .queue import RedisQueue, RunJob


class RunStore(Protocol):
    def get_run(self, run_id: str) -> dict[str, Any] | None: ...

    def update_status(self, run_id: str, status: str) -> None: ...

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None: ...


class RunWorker:
    def __init__(self, queue: RedisQueue, store: RunStore, handler: Callable[[RunJob], None], max_attempts: int = 3) -> None:
        self.queue = queue
        self.store = store
        self.handler = handler
        self.max_attempts = max_attempts

    def run_once(self) -> bool:
        job = self.queue.dequeue()
        if job is None:
            return False
        current = self.store.get_run(job.run_id)
        if current is None or current["status"] in {"cancelled", "failed", "succeeded"}:
            return True
        self.store.update_status(job.run_id, "running")
        self.store.append_event(job.run_id, "run.started", {"stage": job.stage, "attempt": job.attempt})
        try:
            terminal = self.handler(job)
            if terminal is False:
                return True
        except Exception as exc:  # noqa: BLE001
            if job.attempt < self.max_attempts:
                retry = job.model_copy(update={"attempt": job.attempt + 1})
                self.store.update_status(job.run_id, "queued")
                self.store.append_event(job.run_id, "run.retry_scheduled", {"attempt": retry.attempt, "error": str(exc)})
                self.queue.enqueue(retry)
            else:
                self.store.update_status(job.run_id, "failed")
                self.store.append_event(job.run_id, "run.failed", {"attempt": job.attempt, "error": str(exc)})
            return True
        self.store.update_status(job.run_id, "succeeded")
        self.store.append_event(job.run_id, "run.succeeded", {"stage": job.stage})
        return True
