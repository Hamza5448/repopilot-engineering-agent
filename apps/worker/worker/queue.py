"""Redis queue contract for durable background run dispatch."""

import json
from typing import Any

from pydantic import BaseModel, Field

from packages.context.context import FileSnapshot


class RunJob(BaseModel):
    run_id: str
    repository_id: int
    installation_id: int | None = None
    github_owner: str | None = None
    github_repository: str | None = None
    base_branch: str = "main"
    require_approval: bool = False
    base_sha: str = "unknown"
    stage: str = "triage"
    attempt: int = 1
    issue_title: str = ""
    issue_body: str = ""
    files: list[FileSnapshot] = Field(default_factory=list)
    repository_url: str | None = None
    patch: str | None = None
    branch_name: str = "agent/repopilot-change"
    commit_message: str = "Apply RepoPilot change"
    workspace_path: str | None = None
    changed_files: dict[str, str] = Field(default_factory=dict)


class RedisQueue:
    def __init__(self, client: Any, queue_name: str = "repopilot:runs") -> None:
        self.client = client
        self.queue_name = queue_name

    def enqueue(self, job: RunJob) -> None:
        self.client.rpush(self.queue_name, job.model_dump_json())

    def dequeue(self) -> RunJob | None:
        payload = self.client.lpop(self.queue_name)
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode()
        return RunJob.model_validate(json.loads(payload))
