"""Worker-side GitHub App publisher construction."""

from packages.github.api import GitHubInstallationTokenProvider, GitHubPublisherClient
from packages.github.auth import GitHubAppAuthenticator

from .queue import RunJob


class GitHubAppPublisherFactory:
    """Build and cache installation-authenticated publishers per repository installation."""

    def __init__(
        self,
        app_id: int,
        private_key: str | None = None,
        private_key_path: str | None = None,
    ) -> None:
        self.authenticator = GitHubAppAuthenticator(
            app_id,
            private_key=private_key,
            private_key_path=private_key_path,
        )
        self.token_provider = GitHubInstallationTokenProvider(self.authenticator)
        self._tokens: dict[int, str] = {}
        self._publishers: dict[tuple[int, str, str], GitHubPublisherClient] = {}

    def token_for(self, job: RunJob) -> str:
        if not job.installation_id:
            raise ValueError("GitHub installation context is required for repository access")
        token = self._tokens.get(job.installation_id)
        if token is None:
            token = self.token_provider.get_token(job.installation_id)
            self._tokens[job.installation_id] = token
        return token

    def for_job(self, job: RunJob) -> GitHubPublisherClient:
        if not job.installation_id or not job.github_owner or not job.github_repository:
            raise ValueError("GitHub installation context is required for publication")
        cache_key = (job.installation_id, job.github_owner, job.github_repository)
        publisher = self._publishers.get(cache_key)
        if publisher is None:
            token = self.token_for(job)
            publisher = GitHubPublisherClient(job.github_owner, job.github_repository, token)
            self._publishers[cache_key] = publisher
        return publisher
