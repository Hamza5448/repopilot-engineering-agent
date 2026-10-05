"""Repository onboarding contracts for the GitHub App boundary.

This in-memory store is intentionally temporary. The interface will be backed by
PostgreSQL when the persistence phase begins, without changing the API contract.
"""

from threading import Lock
from typing import Any

from pydantic import BaseModel, ConfigDict


class RepositoryRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    full_name: str
    default_branch: str = "main"
    installation_id: int | None = None
    private: bool = False


class RepositoryStore:
    def __init__(self) -> None:
        self._repositories: dict[int, RepositoryRecord] = {}
        self._lock = Lock()

    def upsert_from_github(self, payload: dict[str, Any], installation_id: int | None) -> RepositoryRecord:
        record = RepositoryRecord(
            id=payload["id"],
            full_name=payload["full_name"],
            default_branch=payload.get("default_branch") or "main",
            installation_id=installation_id,
            private=payload.get("private", False),
        )
        with self._lock:
            self._repositories[record.id] = record
        return record

    def get(self, repository_id: int) -> RepositoryRecord | None:
        return self._repositories.get(repository_id)

    def list(self) -> list[RepositoryRecord]:
        return sorted(self._repositories.values(), key=lambda repository: repository.full_name)
