"""Durable RepoPilot run state primitives."""

from enum import StrEnum


class RunState(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStage(StrEnum):
    TRIAGE = "triage"
    CONTEXT = "context"
    PLAN = "plan"
    IMPLEMENT = "implement"
    VALIDATE = "validate"
    REVIEW = "review"
    PUBLISH = "publish"


class InvalidRunTransition(ValueError):
    """Raised when a requested state transition violates the run contract."""


_ALLOWED: dict[RunState, frozenset[RunState]] = {
    RunState.CREATED: frozenset({RunState.QUEUED, RunState.CANCELLED}),
    RunState.QUEUED: frozenset({RunState.RUNNING, RunState.CANCELLED}),
    RunState.RUNNING: frozenset(
        {RunState.WAITING_FOR_APPROVAL, RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED}
    ),
    RunState.WAITING_FOR_APPROVAL: frozenset({RunState.RUNNING, RunState.CANCELLED}),
    RunState.SUCCEEDED: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.CANCELLED: frozenset(),
}


def transition(current: RunState, target: RunState) -> RunState:
    """Validate and return a durable run state transition."""
    if target not in _ALLOWED[current]:
        raise InvalidRunTransition(f"Cannot transition run from {current} to {target}")
    return target
