"""Repository authority and mutation policy contracts."""

from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field


class AuthorityLevel(IntEnum):
    OBSERVE = 0
    PROPOSE = 1
    WORKSPACE = 2
    BRANCH = 3
    PULL_REQUEST = 4
    MERGE = 5


class Mutation(StrEnum):
    CREATE_BRANCH = "create_branch"
    COMMIT = "commit"
    OPEN_PULL_REQUEST = "open_pull_request"
    PUBLISH_CHECK = "publish_check"
    MERGE = "merge"


class RepositoryPolicy(BaseModel):
    authority_level: AuthorityLevel = AuthorityLevel.OBSERVE
    default_branch: str = "main"
    protected_paths: list[str] = Field(default_factory=lambda: [".github/workflows", "secrets"])
    require_approval_for: list[Mutation] = Field(
        default_factory=lambda: [Mutation.CREATE_BRANCH, Mutation.OPEN_PULL_REQUEST]
    )


def authorize_mutation(policy: RepositoryPolicy, mutation: Mutation, target_branch: str | None = None) -> None:
    required_level = {
        Mutation.CREATE_BRANCH: AuthorityLevel.BRANCH,
        Mutation.COMMIT: AuthorityLevel.BRANCH,
        Mutation.OPEN_PULL_REQUEST: AuthorityLevel.PULL_REQUEST,
        Mutation.PUBLISH_CHECK: AuthorityLevel.PULL_REQUEST,
        Mutation.MERGE: AuthorityLevel.MERGE,
    }[mutation]
    if policy.authority_level < required_level:
        raise PermissionError(f"Authority level {policy.authority_level} cannot perform {mutation}")
    if target_branch and target_branch == policy.default_branch:
        raise PermissionError("Direct default-branch mutations are denied")
    if mutation in policy.require_approval_for:
        raise PermissionError(f"Explicit approval is required before {mutation}")
