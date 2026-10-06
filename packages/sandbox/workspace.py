"""Exact-SHA repository workspace and patch application boundary."""

import subprocess
from pathlib import Path

from .policy import CommandPolicy, DeniedOperation


class WorkspaceError(RuntimeError):
    """Raised when a workspace operation cannot be completed safely."""


class RepositoryWorkspace:
    def __init__(self, path: str | Path, policy: CommandPolicy | None = None) -> None:
        self.path = Path(path).resolve()
        self.policy = policy or CommandPolicy()

    def _git(self, *args: str, input_text: str | None = None) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.path if self.path.exists() else None,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
        )
        if result.returncode:
            raise WorkspaceError(result.stderr.strip() or "Git operation failed")
        return result.stdout.strip()

    def clone_at(self, repository_url: str, commit_sha: str) -> str:
        if self.path.exists() and any(self.path.iterdir()):
            raise WorkspaceError("Workspace must be empty before cloning")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--no-checkout", repository_url, str(self.path)],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        if result.returncode:
            raise WorkspaceError(result.stderr.strip() or "Repository clone failed")
        self._git("checkout", "--detach", commit_sha)
        actual_sha = self._git("rev-parse", "HEAD")
        if actual_sha != commit_sha:
            raise WorkspaceError(f"Workspace SHA mismatch: expected {commit_sha}, got {actual_sha}")
        return actual_sha

    def apply_patch(self, patch: str) -> list[str]:
        self._git("apply", "--check", input_text=patch)
        self._git("apply", "--index", "--ignore-space-change", input_text=patch)
        changed = self.changed_files()
        for path in changed:
            try:
                self.policy.authorize_path(path, write=True)
            except DeniedOperation as exc:
                raise WorkspaceError(str(exc)) from exc
        return changed

    def changed_files(self) -> list[str]:
        output = self._git("diff", "--cached", "--name-only")
        return [path for path in output.splitlines() if path]

    def diff(self) -> str:
        return self._git("diff", "--cached")

    def commit(self, message: str) -> str:
        self._git("config", "user.name", "RepoPilot")
        self._git("config", "user.email", "repopilot[bot]@users.noreply.github.com")
        self._git("commit", "-m", message)
        return self._git("rev-parse", "HEAD")
