"""Provider-neutral contracts for GitHub branch, PR, and Check publication."""

from typing import Protocol

from pydantic import BaseModel, Field


class BranchSpec(BaseModel):
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9/_-]{2,80}$")
    base_sha: str = Field(min_length=7, max_length=64)


class CommitSpec(BaseModel):
    branch: str
    message: str = Field(min_length=1, max_length=200)
    patch: str = Field(min_length=1)


class PullRequestSpec(BaseModel):
    branch: str
    base_branch: str = "main"
    title: str = Field(min_length=1, max_length=256)
    body: str = ""


class CheckSpec(BaseModel):
    name: str
    status: str
    summary: str
    annotations: list[dict[str, str]] = Field(default_factory=list)


class PublishedResource(BaseModel):
    id: str
    url: str | None = None


class GitHubPublisher(Protocol):
    def create_branch(self, spec: BranchSpec) -> PublishedResource: ...

    def commit_patch(self, spec: CommitSpec) -> PublishedResource: ...

    def open_pull_request(self, spec: PullRequestSpec) -> PublishedResource: ...

    def publish_check(self, spec: CheckSpec) -> PublishedResource: ...
