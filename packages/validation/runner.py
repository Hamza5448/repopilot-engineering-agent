"""Run allowlisted validation commands and normalize their evidence."""

from time import perf_counter

from packages.sandbox.executor import SandboxExecutor
from packages.sandbox.policy import CommandRequest
from packages.validation.results import ValidationKind, ValidationResult


class ValidationRunner:
    def __init__(self, executor: SandboxExecutor) -> None:
        self.executor = executor

    def run(self, kind: ValidationKind, request: CommandRequest) -> ValidationResult:
        started = perf_counter()
        result = self.executor.run(request)
        return ValidationResult(
            kind=kind,
            passed=result.ok,
            exit_code=0 if result.ok else 1,
            summary=result.output or result.error or "No command output",
            duration_ms=round((perf_counter() - started) * 1000),
        )
