"""Patch-generation contracts and the safe local baseline adapter."""

import re
from typing import Protocol

from packages.context.context import RepositoryContext


class PatchGenerator(Protocol):
    def generate(self, issue_body: str, context: RepositoryContext) -> str | None: ...


class FencedDiffPatchGenerator:
    """Extract an explicit unified diff from issue text for controlled local runs."""

    _fenced_diff = re.compile(r"```(?:diff|patch)\s*\n(?P<patch>.*?)```", re.IGNORECASE | re.DOTALL)

    def generate(self, issue_body: str, context: RepositoryContext) -> str | None:
        match = self._fenced_diff.search(issue_body)
        if match is None:
            return None
        patch = match.group("patch").strip() + "\n"
        if not patch.startswith("diff --git "):
            raise ValueError("Generated patch must be a unified git diff")
        return patch
