from packages.agents.patches import FencedDiffPatchGenerator
from packages.context.context import RepositoryContext


def test_fenced_diff_patch_generator_extracts_only_unified_diff() -> None:
    generator = FencedDiffPatchGenerator()
    context = RepositoryContext(
        repository_id=1,
        base_sha="abcdef1",
        issue_title="Fix parser",
        issue_body="",
        files=[],
    )
    patch = generator.generate(
        "Please apply this change:\n```diff\ndiff --git a/parser.py b/parser.py\n--- a/parser.py\n+++ b/parser.py\n@@ -1 +1 @@\n-VALUE = 1\n+VALUE = 2\n```",
        context,
    )
    assert patch is not None
    assert patch.startswith("diff --git a/parser.py b/parser.py")


def test_fenced_diff_patch_generator_returns_none_without_explicit_patch() -> None:
    generator = FencedDiffPatchGenerator()
    context = RepositoryContext(
        repository_id=1,
        base_sha="abcdef1",
        issue_title="Fix parser",
        issue_body="",
        files=[],
    )
    assert generator.generate("Please fix the parser.", context) is None
