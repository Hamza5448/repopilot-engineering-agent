"""Small local persistence adapter used while PostgreSQL is deferred."""

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from packages.domain.run import RunState


class RunStore:
    """Persist runs and ordered events behind a minimal application interface."""

    def __init__(self, database_path: str = ".local/repopilot.db") -> None:
        self.database_path = database_path
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id TEXT PRIMARY KEY,
                    repository_id INTEGER NOT NULL,
                    trigger_type TEXT NOT NULL,
                    base_sha TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS run_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL REFERENCES agent_runs(id),
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def create_run(self, repository_id: int, trigger_type: str, base_sha: str) -> dict[str, Any]:
        run_id = str(uuid4())
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO agent_runs (id, repository_id, trigger_type, base_sha, status) VALUES (?, ?, ?, ?, ?)",
                (run_id, repository_id, trigger_type, base_sha, RunState.CREATED.value),
            )
            connection.execute(
                "INSERT INTO run_events (run_id, event_type, payload) VALUES (?, ?, ?)",
                (run_id, "run.created", json.dumps({"status": RunState.CREATED.value})),
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row) if row else None

    def list_events(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, run_id, event_type, payload, created_at FROM run_events WHERE run_id = ? ORDER BY id",
                (run_id,),
            ).fetchall()
        return [
            {**dict(row), "payload": json.loads(row["payload"])}
            for row in rows
        ]

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO run_events (run_id, event_type, payload) VALUES (?, ?, ?)",
                (run_id, event_type, json.dumps(payload)),
            )

    def update_status(self, run_id: str, status: str) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE agent_runs SET status = ? WHERE id = ?", (status, run_id))
