"""SQLAlchemy run/event persistence for PostgreSQL or local SQLite."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from packages.domain.run import RunState


class Base(DeclarativeBase):
    pass


class AgentRunRow(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    repository_id: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    base_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunEventRow(Base):
    __tablename__ = "run_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SqlAlchemyRunStore:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

    def create_run(self, repository_id: int, trigger_type: str, base_sha: str) -> dict[str, Any]:
        run_id = str(uuid4())
        now = datetime.now(UTC)
        with Session(self.engine) as session, session.begin():
            session.add(AgentRunRow(id=run_id, repository_id=repository_id, trigger_type=trigger_type, base_sha=base_sha, status=RunState.CREATED.value, created_at=now))
            session.add(RunEventRow(run_id=run_id, event_type="run.created", payload=json.dumps({"status": RunState.CREATED.value}), created_at=now))
        return self.get_run(run_id)  # type: ignore[return-value]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.get(AgentRunRow, run_id)
            if row is None:
                return None
            return {"id": row.id, "repository_id": row.repository_id, "trigger_type": row.trigger_type, "base_sha": row.base_sha, "status": row.status, "created_at": row.created_at.isoformat()}

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(RunEventRow(run_id=run_id, event_type=event_type, payload=json.dumps(payload), created_at=datetime.now(UTC)))

    def list_events(self, run_id: str) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            rows = session.scalars(select(RunEventRow).where(RunEventRow.run_id == run_id).order_by(RunEventRow.id)).all()
            return [{"id": row.id, "run_id": row.run_id, "event_type": row.event_type, "payload": json.loads(row.payload), "created_at": row.created_at.isoformat()} for row in rows]
