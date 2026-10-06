"""Secure, idempotent GitHub webhook handling primitives."""

import hashlib
import hmac
import json
from collections import deque
from threading import Lock
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InvalidWebhookSignature(ValueError):
    """Raised when a GitHub webhook signature is missing or invalid."""


def verify_signature(payload: bytes, signature: str | None, secret: str) -> None:
    """Verify GitHub's sha256 HMAC signature in constant time."""

    if not signature or not signature.startswith("sha256="):
        raise InvalidWebhookSignature("Missing GitHub webhook signature")
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise InvalidWebhookSignature("Invalid GitHub webhook signature")


class DeliveryStore:
    """Bounded, thread-safe delivery registry for the pre-database slice."""

    def __init__(self, max_entries: int = 10_000) -> None:
        self._seen: set[str] = set()
        self._order: deque[str] = deque()
        self._max_entries = max_entries
        self._lock = Lock()

    def claim(self, delivery_id: str) -> bool:
        """Atomically claim a delivery; return false when it was already seen."""

        with self._lock:
            if delivery_id in self._seen:
                return False
            self._seen.add(delivery_id)
            self._order.append(delivery_id)
            while len(self._order) > self._max_entries:
                self._seen.remove(self._order.popleft())
            return True

    def release(self, delivery_id: str) -> None:
        """Release a delivery after downstream processing fails before acknowledgement."""

        with self._lock:
            if delivery_id not in self._seen:
                return
            self._seen.remove(delivery_id)
            try:
                self._order.remove(delivery_id)
            except ValueError:
                pass


class GitHubIssueEvent(BaseModel):
    """Minimum typed contract needed to start issue-triggered work."""

    model_config = ConfigDict(extra="ignore")

    action: str = "unknown"
    issue: dict[str, Any] = Field(default_factory=dict)
    repository: dict[str, Any] = Field(default_factory=dict)
    installation: dict[str, Any] | None = None
    repositories_added: list[dict[str, Any]] = Field(default_factory=list)


def parse_event(payload: bytes) -> GitHubIssueEvent:
    data = json.loads(payload)
    return GitHubIssueEvent.model_validate(data)
