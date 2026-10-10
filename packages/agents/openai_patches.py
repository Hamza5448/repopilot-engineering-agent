"""OpenAI Responses API patch generator with a strict JSON response contract."""

import json
from typing import Any

import httpx

from packages.context.context import RepositoryContext


class OpenAIPatchGenerationError(RuntimeError):
    """Raised when a model response cannot produce a safe unified diff."""


class OpenAIResponsesPatchGenerator:
    def __init__(self, api_key: str, model: str, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(base_url="https://api.openai.com/v1", timeout=120.0)
        self.model = model
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def generate(self, issue_body: str, context: RepositoryContext) -> str | None:
        response = self.client.post(
            "/responses",
            headers=self.headers,
            json={
                "model": self.model,
                "input": [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    "You generate the smallest safe unified git diff for a repository task. "
                                    "Return an empty patch when the evidence is insufficient. Never modify protected files."
                                ),
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": json.dumps(
                                    {
                                        "issue": issue_body,
                                        "repository_context": context.model_dump(),
                                    }
                                ),
                            }
                        ],
                    },
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "repopilot_patch",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {"patch": {"type": "string"}},
                            "required": ["patch"],
                            "additionalProperties": False,
                        },
                    }
                },
            },
        )
        try:
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            raw = self._output_text(data)
            patch = json.loads(raw).get("patch", "").strip()
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise OpenAIPatchGenerationError("OpenAI patch generation returned an invalid response") from exc
        if not patch:
            return None
        if not patch.startswith("diff --git "):
            raise OpenAIPatchGenerationError("Generated patch is not a unified git diff")
        return patch + "\n"

    @staticmethod
    def _output_text(data: dict[str, Any]) -> str:
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return str(content["text"])
        raise ValueError("Response did not contain output text")
