"""Durable worker loop for queued RepoPilot runs."""

import logging
from collections.abc import Callable
from typing import Any, Protocol

from packages.observability.logging import log_event

from .queue import RedisQueue, RunJob

logger = logging.getLogger("repopilot.worker")


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
        log_event(logger, "worker_received_run", run_id=job.run_id, stage=job.stage, attempt=job.attempt)
        current = self.store.get_run(job.run_id)
        if current is None or current["status"] in {"cancelled", "failed", "succeeded"}:
            log_event(logger, "worker_skipped_run", run_id=job.run_id, reason="missing_or_terminal")
            return True
        self.store.update_status(job.run_id, "running")
        self.store.append_event(job.run_id, "run.started", {"stage": job.stage, "attempt": job.attempt})
        try:
            log_event(logger, "dispatcher_started", run_id=job.run_id, stage=job.stage)
            terminal = self.handler(job)
            log_event(logger, "dispatcher_succeeded", run_id=job.run_id, stage=job.stage, terminal=bool(terminal))
            if terminal is False:
                return True
        except Exception as exc:  # noqa: BLE001
            log_event(logger, "dispatcher_failed", run_id=job.run_id, stage=job.stage, error_type=type(exc).__name__)
            if job.attempt < self.max_attempts:
                retry = job.model_copy(update={"attempt": job.attempt + 1})
                self.store.update_status(job.run_id, "queued")
                self.store.append_event(job.run_id, "run.retry_scheduled", {"attempt": retry.attempt, "error": str(exc)})
                self.queue.enqueue(retry)
                log_event(logger, "run_retry_enqueued", run_id=job.run_id, attempt=retry.attempt)
            else:
                self.store.update_status(job.run_id, "failed")
                self.store.append_event(job.run_id, "run.failed", {"attempt": job.attempt, "error": str(exc)})
                log_event(logger, "run_failed", run_id=job.run_id, attempt=job.attempt)
            return True
        self.store.update_status(job.run_id, "succeeded")
        self.store.append_event(job.run_id, "run.succeeded", {"stage": job.stage})
        log_event(logger, "run_succeeded", run_id=job.run_id, stage=job.stage)
        return True
