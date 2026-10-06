from packages.sandbox.executor import LocalSandboxExecutor
from packages.sandbox.policy import CommandRequest


def test_local_executor_runs_allowlisted_command_without_shell(tmp_path) -> None:
    result = LocalSandboxExecutor(tmp_path).run(CommandRequest(command="python", args=["--version"]))
    assert result.ok is True
    assert "Python" in result.output


def test_local_executor_rejects_python_code_execution(tmp_path) -> None:
    result = LocalSandboxExecutor(tmp_path).run(CommandRequest(command="python", args=["-c", "print('unsafe')"]))
    assert result.ok is False
    assert "limited" in (result.error or "")


def test_local_executor_captures_nonzero_result(tmp_path) -> None:
    result = LocalSandboxExecutor(tmp_path).run(CommandRequest(command="ruff", args=["check", "missing.py"]))
    assert result.ok is False
    assert result.error == "Command failed"
