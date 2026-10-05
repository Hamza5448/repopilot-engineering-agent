from packages.sandbox.executor import LocalSandboxExecutor
from packages.sandbox.policy import CommandRequest
from packages.validation.results import ValidationKind
from packages.validation.runner import ValidationRunner


def test_validation_runner_normalizes_execution_evidence(tmp_path) -> None:
    report = ValidationRunner(LocalSandboxExecutor(tmp_path)).run(
        ValidationKind.TEST,
        CommandRequest(command="python", args=["--version"]),
    )
    assert report.passed is True
    assert report.kind is ValidationKind.TEST
    assert report.duration_ms >= 0
