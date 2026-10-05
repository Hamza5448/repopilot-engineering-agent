import pytest

from packages.sandbox.policy import CommandPolicy, CommandRequest, DeniedOperation


def test_policy_allows_typed_validation_command() -> None:
    request = CommandRequest(command="pytest", args=["tests/unit"])
    assert CommandPolicy().authorize(request) == request


@pytest.mark.parametrize("argument", ["tests && whoami", "tests/../secrets", "$(whoami)"])
def test_policy_rejects_shell_injection_and_traversal(argument: str) -> None:
    with pytest.raises(DeniedOperation):
        CommandPolicy().authorize(CommandRequest(command="pytest", args=[argument]))


def test_policy_rejects_protected_and_absolute_paths() -> None:
    policy = CommandPolicy()
    with pytest.raises(DeniedOperation):
        policy.authorize_path(".env", write=True)
    with pytest.raises(DeniedOperation):
        policy.authorize_path("/workspace/file.py")
