import httpx

from packages.github.api import GitHubInstallationTokenProvider, GitHubPublisherClient
from packages.github.auth import GitHubAppAuthenticator
from packages.github.publisher import BranchSpec, CheckSpec, CommitSpec, PullRequestSpec


def test_installation_token_provider_uses_app_jwt() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/app/installations/9/access_tokens")
        assert request.headers["Authorization"] == "Bearer signed"
        return httpx.Response(201, json={"token": "installation-token"})

    authenticator = GitHubAppAuthenticator(1, "key")
    authenticator.build_app_jwt = lambda: "signed"
    provider = GitHubInstallationTokenProvider(authenticator, httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.github.com"))
    assert provider.get_token(9) == "installation-token"


def test_publisher_calls_branch_pr_and_check_endpoints() -> None:
    paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path.endswith("/git/refs"):
            return httpx.Response(201, json={"ref": "refs/heads/agent/fix-1"})
        if request.url.path.endswith("/pulls"):
            return httpx.Response(201, json={"number": 4, "html_url": "https://github.com/pr/4"})
        return httpx.Response(201, json={"id": 8})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.github.com")
    publisher = GitHubPublisherClient("owner", "repo", "token", client)
    publisher.create_branch(BranchSpec(name="agent/fix-1", base_sha="abcdef1"))
    publisher.open_pull_request(PullRequestSpec(branch="agent/fix-1", title="Fix"))
    publisher.publish_check(CheckSpec(name="RepoPilot", status="completed", summary="ok"))
    assert paths == ["/repos/owner/repo/git/refs", "/repos/owner/repo/pulls", "/repos/owner/repo/check-runs"]


def test_publisher_commits_changed_files_through_git_data_api() -> None:
    methods_and_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        methods_and_paths.append((request.method, request.url.path))
        if request.url.path.endswith("/git/ref/heads/agent/fix-1"):
            return httpx.Response(200, json={"object": {"sha": "parent"}})
        if request.url.path.endswith("/git/commits/parent"):
            return httpx.Response(200, json={"tree": {"sha": "base-tree"}})
        if request.url.path.endswith("/git/blobs"):
            return httpx.Response(201, json={"sha": "blob-1"})
        if request.url.path.endswith("/git/trees"):
            return httpx.Response(201, json={"sha": "tree-1"})
        if request.url.path.endswith("/git/commits"):
            return httpx.Response(201, json={"sha": "commit-1"})
        return httpx.Response(200, json={"ref": "refs/heads/agent/fix-1"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.github.com")
    publisher = GitHubPublisherClient("owner", "repo", "token", client)
    result = publisher.commit_patch(
        CommitSpec(branch="agent/fix-1", message="Fix parser", files={"parser.py": "VALUE = 2\n"})
    )
    assert result.id == "refs/heads/agent/fix-1"
    assert ("POST", "/repos/owner/repo/git/blobs") in methods_and_paths
    assert ("PATCH", "/repos/owner/repo/git/refs/heads/agent/fix-1") in methods_and_paths
