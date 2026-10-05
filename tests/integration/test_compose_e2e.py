"""Opt-in black-box test for the Docker Compose runtime.

Run with the local stack up:

    $env:REPOPILOT_E2E = "1"
    python -m pytest tests/integration/test_compose_e2e.py -q
"""

import hashlib
import hmac
import json
import os
import time
from uuid import uuid4

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("REPOPILOT_E2E") != "1", reason="requires the Docker Compose API and worker"
)


def test_compose_run_completes_end_to_end() -> None:
    base_url = os.getenv("REPOPILOT_API_URL", "http://localhost:8000")
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "local-development-secret")
    repository_id = int(uuid4().int % 1_000_000_000)
    delivery_id = str(uuid4())
    installation_payload = {
        "action": "added",
        "installation": {"id": 7001},
        "repositories_added": [{"id": repository_id, "full_name": "repopilot/e2e-demo"}],
    }
    body = json.dumps(installation_payload).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    with httpx.Client(base_url=base_url, timeout=5) as client:
        webhook = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "x-github-delivery": delivery_id,
                "x-github-event": "installation_repositories",
                "x-hub-signature-256": signature,
            },
        )
        assert webhook.status_code == 202, webhook.text

        created = client.post(
            f"/api/v1/repositories/{repository_id}/runs",
            json={
                "trigger_type": "issue",
                "base_sha": "abcdef1234567",
                "issue_title": "Fix parser validation",
                "issue_body": "Parser rejects valid input; add a regression test.",
                "files": [{"path": "parser.py", "content": "def parse(): pass"}],
            },
        )
        assert created.status_code == 201, created.text
        run_id = created.json()["id"]

        deadline = time.monotonic() + 20
        status = "created"
        while time.monotonic() < deadline:
            status = client.get(f"/api/v1/runs/{run_id}").json()["status"]
            if status in {"succeeded", "failed", "cancelled"}:
                break
            time.sleep(0.5)

        assert status == "succeeded"
        events = client.get(f"/api/v1/runs/{run_id}/events").json()
        event_types = {event["event_type"] for event in events}
        assert {"run.triaged", "run.planned", "run.validated", "run.check.published"} <= event_types
