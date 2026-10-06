import pytest

from packages.github.publisher import BranchSpec, CheckSpec, PullRequestSpec


def test_publisher_contracts_validate_expected_shapes() -> None:
    branch = BranchSpec(name="agent/fix-123", base_sha="abcdef1")
    pull_request = PullRequestSpec(branch=branch.name, title="Fix parser")
    check = CheckSpec(name="RepoPilot", status="completed", summary="Tests passed")
    assert pull_request.base_branch == "main"
    assert check.annotations == []


def test_branch_names_cannot_contain_spaces() -> None:
    with pytest.raises(ValueError):
        BranchSpec(name="agent bad branch", base_sha="abcdef1")
