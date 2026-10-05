"""Production worker entrypoint for the local Compose stack."""

import os
import time

import redis

from apps.api.app.storage.sqlalchemy import SqlAlchemyRunStore
from packages.github.api import GitHubPublisherClient

from .pipeline import GitHubCheckPublisher, LocalCheckPublisher, StageDispatcher
from .queue import RedisQueue, RunJob
from .runtime import RunWorker


def handle_job(job: RunJob, store: SqlAlchemyRunStore) -> None:
    """Record the stage boundary until concrete stage handlers are connected."""

    store.append_event(job.run_id, "run.stage.completed", {"stage": job.stage})


def main() -> None:
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
    store = SqlAlchemyRunStore(os.getenv("DATABASE_URL", "postgresql+psycopg://repopilot:repopilot@postgres:5432/repopilot"))
    queue = RedisQueue(redis_client)
    check_publisher = LocalCheckPublisher()
    owner = os.getenv("GITHUB_OWNER")
    repository = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")
    if owner and repository and token:
        check_publisher = GitHubCheckPublisher(GitHubPublisherClient(owner, repository, token))
    dispatcher = StageDispatcher(store, queue, check_publisher)
    worker = RunWorker(queue, store, dispatcher.dispatch)
    while True:
        worker.run_once()
        time.sleep(1)


if __name__ == "__main__":
    main()
