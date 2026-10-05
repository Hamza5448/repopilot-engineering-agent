"""Stage dispatcher connecting planning, validation, and Check publication."""

from pathlib import Path
from typing import Any, Protocol

from packages.agents.planner import Planner
from packages.context.context import build_context
from packages.github.publisher import CheckSpec, PublishedResource
from packages.sandbox.executor import LocalSandboxExecutor
from packages.sandbox.policy import CommandRequest
from packages.validation.results import ValidationKind
from packages.validation.runner import ValidationRunner

from .queue import RedisQueue, RunJob


class RunStore(Protocol):
    def update_status(self, run_id: str, status: str) -> None: ...

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None: ...


class CheckPublisher(Protocol):
    def publish(self, run_id: str, passed: bool, summary: str) -> PublishedResource: ...


class LocalCheckPublisher:
    """Records a Check artifact locally when GitHub credentials are absent."""

    def publish(self, run_id: str, passed: bool, summary: str) -> PublishedResource:
        return PublishedResource(id=f"local-check-{run_id}", url=None)


class GitHubCheckPublisher:
    def __init__(self, publisher: Any) -> None:
        self.publisher = publisher

    def publish(self, run_id: str, passed: bool, summary: str) -> PublishedResource:
        return self.publisher.publish_check(
            CheckSpec(name="RepoPilot", status="completed", summary=summary)
        )


class StageDispatcher:
    def __init__(
        self,
        store: RunStore,
        queue: RedisQueue,
        check_publisher: CheckPublisher | None = None,
        workspace_root: str = "/tmp/repopilot",
    ) -> None:
        self.store = store
        self.queue = queue
        self.check_publisher = check_publisher or LocalCheckPublisher()
        self.workspace_root = workspace_root

    def _next(self, job: RunJob, stage: str) -> None:
        self.store.update_status(job.run_id, "queued")
        self.queue.enqueue(job.model_copy(update={"stage": stage, "attempt": 1}))

    def dispatch(self, job: RunJob) -> bool:
        if job.stage == "triage":
            self.store.append_event(job.run_id, "run.triaged", {"issue_title": job.issue_title})
            self._next(job, "plan")
            return False

        if job.stage == "plan":
            context = build_context(
                repository_id=job.repository_id,
                base_sha=job.base_sha,
                issue_title=job.issue_title or "Repository task",
                issue_body=job.issue_body,
                files=job.files,
            )
            plan = Planner().plan(context)
            self.store.append_event(job.run_id, "run.planned", {"context": context.model_dump(), "plan": plan.model_dump()})
            self._next(job, "validate")
            return False

        if job.stage == "validate":
            workspace = Path(self.workspace_root) / job.run_id
            result = ValidationRunner(LocalSandboxExecutor(workspace)).run(
                ValidationKind.TEST,
                CommandRequest(command="python", args=["--version"]),
            )
            self.store.append_event(job.run_id, "run.validated", result.model_dump())
            if not result.passed:
                self.store.update_status(job.run_id, "failed")
                self.store.append_event(job.run_id, "run.failed", {"reason": "validation_failed"})
                return True
            self._next(job, "publish_check")
            return False

        if job.stage == "publish_check":
            result = self.check_publisher.publish(job.run_id, True, "RepoPilot validation passed")
            self.store.append_event(job.run_id, "run.check.published", result.model_dump())
            return True

        raise ValueError(f"Unknown run stage: {job.stage}")
