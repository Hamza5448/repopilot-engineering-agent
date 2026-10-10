"""Exact-SHA repository workspace and patch application boundary."""

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

from packages.context.context import FileSnapshot

from .policy import CommandPolicy, DeniedOperation


class WorkspaceError(RuntimeError):
    """Raised when a workspace operation cannot be completed safely."""


class RepositoryWorkspace:
    def __init__(self, path: str | Path, policy: CommandPolicy | None = None) -> None:
        self.path = Path(path).resolve()
        self.policy = policy or CommandPolicy()

    def _git(self, *args: str, input_text: str | None = None, env: dict[str, str] | None = None) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.path if self.path.exists() else None,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            env=env,
        )
        if result.returncode:
            raise WorkspaceError(result.stderr.strip() or "Git operation failed")
        return result.stdout.strip()

    def clone_at(self, repository_url: str, commit_sha: str, access_token: str | None = None) -> str:
        if self.path.exists() and any(self.path.iterdir()):
            raise WorkspaceError("Workspace must be empty before cloning")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        clone_env = None
        if access_token:
            clone_env = os.environ.copy()
            clone_env["GIT_CONFIG_COUNT"] = "1"
            clone_env["GIT_CONFIG_KEY_0"] = "http.extraheader"
            clone_env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: bearer {access_token}"
            clone_env["GIT_TERMINAL_PROMPT"] = "0"
        result = subprocess.run(
            ["git", "clone", "--no-checkout", repository_url, str(self.path)],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            env=clone_env,
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

    def file_snapshots(self, max_files: int = 200, max_file_chars: int = 16_000) -> list[FileSnapshot]:
        """Read bounded text files from the exact checkout without entering protected paths."""

        snapshots: list[FileSnapshot] = []
        for path in self._iter_files():
            if len(snapshots) >= max_files:
                break
            relative = path.relative_to(self.path).as_posix()
            try:
                self.policy.authorize_path(relative)
                content = path.read_text(encoding="utf-8")
            except (DeniedOperation, OSError, UnicodeDecodeError):
                continue
            snapshots.append(
                FileSnapshot(path=relative, content=content[:max_file_chars], language=path.suffix.lstrip(".") or None)
            )
        return snapshots

    def _iter_files(self) -> Iterator[Path]:
        for path in sorted(self.path.rglob("*")):
            if path.is_file() and ".git" not in path.relative_to(self.path).parts:
                yield path

    def diff(self) -> str:
        return self._git("diff", "--cached")

    def commit(self, message: str) -> str:
        self._git("config", "user.name", "RepoPilot")
        self._git("config", "user.email", "repopilot[bot]@users.noreply.github.com")
        self._git("commit", "-m", message)
        return self._git("rev-parse", "HEAD")
