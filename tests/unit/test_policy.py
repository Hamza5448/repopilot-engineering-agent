import pytest

from packages.domain.policy import (
    AuthorityLevel,
    Mutation,
    RepositoryPolicy,
    authorize_mutation,
)


def test_pull_request_publication_requires_approval_by_default() -> None:
    policy = RepositoryPolicy(authority_level=AuthorityLevel.PULL_REQUEST)
    with pytest.raises(PermissionError, match="approval"):
        authorize_mutation(policy, Mutation.OPEN_PULL_REQUEST, target_branch="agent/fix-1")


def test_default_branch_mutation_is_always_denied() -> None:
    policy = RepositoryPolicy(authority_level=AuthorityLevel.MERGE, require_approval_for=[])
    with pytest.raises(PermissionError, match="default-branch"):
        authorize_mutation(policy, Mutation.MERGE, target_branch="main")


def test_branch_authority_can_create_non_default_branch_without_approval() -> None:
    policy = RepositoryPolicy(authority_level=AuthorityLevel.BRANCH, require_approval_for=[])
    authorize_mutation(policy, Mutation.CREATE_BRANCH, target_branch="agent/fix-1")
