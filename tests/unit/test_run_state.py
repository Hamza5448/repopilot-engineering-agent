import pytest

from packages.domain.run import InvalidRunTransition, RunState, transition


def test_run_can_progress_through_approval_and_finish() -> None:
    state = RunState.CREATED
    for target in (
        RunState.QUEUED,
        RunState.RUNNING,
        RunState.WAITING_FOR_APPROVAL,
        RunState.RUNNING,
        RunState.SUCCEEDED,
    ):
        state = transition(state, target)
    assert state is RunState.SUCCEEDED


def test_terminal_run_cannot_restart() -> None:
    with pytest.raises(InvalidRunTransition):
        transition(RunState.SUCCEEDED, RunState.RUNNING)


def test_created_run_can_be_cancelled() -> None:
    assert transition(RunState.CREATED, RunState.CANCELLED) is RunState.CANCELLED
