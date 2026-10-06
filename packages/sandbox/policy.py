"""Authorization rules for commands and repository paths."""

from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, Field


class DeniedOperation(ValueError):
    """Raised when a sandbox operation violates policy."""


class CommandId(StrEnum):
    PYTEST = "pytest"
    RUFF = "ruff"
    MYPY = "mypy"
    PYTHON = "python"


class ResourceLimits(BaseModel):
    timeout_seconds: int = Field(default=120, ge=1, le=900)
    memory_mb: int = Field(default=1_024, ge=128, le=16_384)
    disk_mb: int = Field(default=2_048, ge=128, le=100_000)


class CommandRequest(BaseModel):
    command: CommandId
    args: list[str] = Field(default_factory=list, max_length=32)
    limits: ResourceLimits = Field(default_factory=ResourceLimits)


class CommandPolicy:
    """Allow only typed, non-shell validation commands."""

    protected_prefixes = (".git", ".env", "secrets", "credentials")
    forbidden_tokens = ("&&", "||", ";", "|", ">", "<", "$", "`", "..")

    def authorize(self, request: CommandRequest) -> CommandRequest:
        if request.command is CommandId.PYTHON and request.args and request.args[0] not in {"--version", "-m"}:
            raise DeniedOperation("Python execution is limited to version checks and pytest module runs")
        if request.command is CommandId.PYTHON and request.args[:2] == ["-m", "pytest"]:
            pass
        elif request.command is CommandId.PYTHON and request.args and request.args[0] == "-m":
            raise DeniedOperation("Only the pytest Python module is allowlisted")
        for argument in request.args:
            if any(token in argument for token in self.forbidden_tokens):
                raise DeniedOperation("Command argument contains a forbidden shell or traversal token")
            normalized = PurePosixPath(argument.replace("\\", "/"))
            if normalized.parts and normalized.parts[0] in self.protected_prefixes:
                raise DeniedOperation(f"Protected path is not allowed: {argument}")
        return request

    def authorize_path(self, path: str, write: bool = False) -> str:
        normalized = PurePosixPath(path.replace("\\", "/"))
        if normalized.is_absolute() or ".." in normalized.parts:
            raise DeniedOperation("Path must remain inside the sandbox workspace")
        if normalized.parts and normalized.parts[0] in self.protected_prefixes:
            raise DeniedOperation(f"Protected path is not allowed: {path}")
        if write and normalized.name in {".gitconfig", ".gitmodules"}:
            raise DeniedOperation(f"Protected Git file is not writable: {path}")
        return str(normalized)
