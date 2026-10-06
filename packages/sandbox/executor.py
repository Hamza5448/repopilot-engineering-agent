"""Replaceable sandbox execution adapters.

The local adapter is for development only. It uses no shell and enforces the
typed command policy, but it is not a production isolation boundary. Docker
execution will implement the same interface when Docker is available.
"""

import subprocess
from pathlib import Path
from typing import Protocol

from .policy import CommandPolicy, CommandRequest
from .tools import ToolResult


class SandboxExecutor(Protocol):
    def run(self, request: CommandRequest) -> ToolResult: ...


class LocalSandboxExecutor:
    def __init__(self, workspace: str | Path, policy: CommandPolicy | None = None) -> None:
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.policy = policy or CommandPolicy()

    def run(self, request: CommandRequest) -> ToolResult:
        try:
            self.policy.authorize(request)
            completed = subprocess.run(
                [request.command.value, *request.args],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=request.limits.timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(ok=False, error="Command timed out")
        except (OSError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

        output = (completed.stdout + completed.stderr).strip()
        return ToolResult(ok=completed.returncode == 0, output=output, error=None if completed.returncode == 0 else "Command failed")
