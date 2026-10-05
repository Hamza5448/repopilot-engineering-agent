"""HTTP GitHub App adapter for installation tokens and publication."""

from typing import Any

import httpx

from .auth import GitHubAppAuthenticator
from .publisher import (
    BranchSpec,
    CheckSpec,
    CommitSpec,
    GitHubPublisher,
    PublishedResource,
    PullRequestSpec,
)


class GitHubInstallationTokenProvider:
    def __init__(self, authenticator: GitHubAppAuthenticator, client: httpx.Client | None = None) -> None:
        self.authenticator = authenticator
        self.client = client or httpx.Client(base_url="https://api.github.com")

    def get_token(self, installation_id: int) -> str:
        response = self.client.post(
            f"/app/installations/{installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {self.authenticator.build_app_jwt()}"},
        )
        response.raise_for_status()
        return response.json()["token"]


class GitHubPublisherClient(GitHubPublisher):
    def __init__(self, owner: str, repository: str, token: str, client: httpx.Client | None = None) -> None:
        self.owner = owner
        self.repository = repository
        self.client = client or httpx.Client(base_url="https://api.github.com")
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    def _resource(self, response: httpx.Response) -> PublishedResource:
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return PublishedResource(id=str(data.get("id", data.get("number", data.get("ref", "unknown")))), url=data.get("html_url"))

    def create_branch(self, spec: BranchSpec) -> PublishedResource:
        response = self.client.post(
            f"/repos/{self.owner}/{self.repository}/git/refs",
            headers=self.headers,
            json={"ref": f"refs/heads/{spec.name}", "sha": spec.base_sha},
        )
        return self._resource(response)

    def commit_patch(self, spec: CommitSpec) -> PublishedResource:
        raise NotImplementedError("Patch-to-tree publication will be added with the workspace publisher")

    def open_pull_request(self, spec: PullRequestSpec) -> PublishedResource:
        response = self.client.post(
            f"/repos/{self.owner}/{self.repository}/pulls",
            headers=self.headers,
            json={"title": spec.title, "body": spec.body, "head": spec.branch, "base": spec.base_branch},
        )
        return self._resource(response)

    def publish_check(self, spec: CheckSpec) -> PublishedResource:
        response = self.client.post(
            f"/repos/{self.owner}/{self.repository}/check-runs",
            headers=self.headers,
            json={"name": spec.name, "status": spec.status, "conclusion": "success" if spec.status == "completed" else None, "output": {"title": spec.name, "summary": spec.summary, "annotations": spec.annotations}},
        )
        return self._resource(response)
