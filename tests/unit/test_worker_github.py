from apps.worker.worker.github import GitHubAppPublisherFactory
from apps.worker.worker.queue import RunJob


def test_worker_factory_caches_installation_token_and_publisher() -> None:
    factory = GitHubAppPublisherFactory(123, private_key="key")
    calls = []

    class FakeTokenProvider:
        def get_token(self, installation_id: int) -> str:
            calls.append(installation_id)
            return "installation-token"

    factory.token_provider = FakeTokenProvider()
    job = RunJob(
        run_id="run-1",
        repository_id=1,
        installation_id=55,
        github_owner="owner",
        github_repository="repo",
    )
    first = factory.for_job(job)
    second = factory.for_job(job)
    assert first is second
    assert calls == [55]
    assert first.owner == "owner"
    assert first.repository == "repo"
    assert factory.token_for(job) == "installation-token"


def test_worker_factory_requires_installation_context() -> None:
    factory = GitHubAppPublisherFactory(123, private_key="key")
    try:
        factory.for_job(RunJob(run_id="run-1", repository_id=1))
    except ValueError as exc:
        assert str(exc) == "GitHub installation context is required for publication"
    else:
        raise AssertionError("Expected missing installation context to fail")
