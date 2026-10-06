"""Typed repository tool contracts; implementations remain sandbox-owned."""

from enum import StrEnum

from pydantic import BaseModel, Field

from .policy import CommandRequest


class ToolName(StrEnum):
    SEARCH = "repo.search"
    READ = "repo.read"
    TREE = "repo.tree"
    WRITE_PATCH = "repo.write_patch"
    RUN = "exec.run"


class ToolCall(BaseModel):
    tool: ToolName
    path: str | None = None
    query: str | None = None
    patch: str | None = None
    command: CommandRequest | None = None


class ToolResult(BaseModel):
    ok: bool
    output: str = ""
    error: str | None = None
    artifact_ids: list[str] = Field(default_factory=list)
