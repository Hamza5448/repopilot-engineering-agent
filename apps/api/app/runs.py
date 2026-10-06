"""Run API request and response contracts."""

from pydantic import BaseModel, Field

from packages.context.context import FileSnapshot


class CreateRunRequest(BaseModel):
    trigger_type: str = Field(min_length=1, max_length=64)
    base_sha: str = Field(min_length=7, max_length=64)
    issue_title: str = Field(default="", max_length=300)
    issue_body: str = Field(default="", max_length=20_000)
    files: list[FileSnapshot] = Field(default_factory=list, max_length=200)
    repository_url: str | None = None
    patch: str | None = None
    branch_name: str = Field(default="agent/repopilot-change", pattern=r"^[a-z0-9][a-z0-9/_-]{2,80}$")
    commit_message: str = Field(default="Apply RepoPilot change", max_length=200)


class PlanRunRequest(BaseModel):
    issue_title: str = Field(min_length=1, max_length=300)
    issue_body: str = Field(default="", max_length=20_000)
    files: list[FileSnapshot] = Field(default_factory=list, max_length=200)


class ApprovalDecision(BaseModel):
    gate: str = Field(default="publication", min_length=1, max_length=64)
    rationale: str = Field(default="", max_length=2_000)
