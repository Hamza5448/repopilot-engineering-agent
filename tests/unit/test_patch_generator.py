import httpx

from packages.agents.openai_patches import OpenAIResponsesPatchGenerator
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


def test_openai_patch_generator_parses_structured_response_without_real_credentials() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/responses"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"patch":"diff --git a/a.py b/a.py\\n"}',
                            }
                        ]
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.openai.com/v1")
    generator = OpenAIResponsesPatchGenerator("test-key", "test-model", client)
    context = RepositoryContext(repository_id=1, base_sha="abcdef1", issue_title="Fix", issue_body="", files=[])
    assert generator.generate("Fix it", context) == "diff --git a/a.py b/a.py\n"
