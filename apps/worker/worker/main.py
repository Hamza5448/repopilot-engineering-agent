"""Production worker entrypoint for the local Compose stack."""

import logging
import os
import time

import redis

from apps.api.app.storage.sqlalchemy import SqlAlchemyRunStore
from packages.github.api import GitHubPublisherClient
from packages.observability.logging import log_event

from .pipeline import GitHubCheckPublisher, LocalCheckPublisher, StageDispatcher
from .queue import RedisQueue, RunJob
from .runtime import RunWorker

logger = logging.getLogger("repopilot.worker")


def handle_job(job: RunJob, store: SqlAlchemyRunStore) -> None:
    """Record the stage boundary until concrete stage handlers are connected."""

    store.append_event(job.run_id, "run.stage.completed", {"stage": job.stage})


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
    store = SqlAlchemyRunStore(os.getenv("DATABASE_URL", "postgresql+psycopg://repopilot:repopilot@postgres:5432/repopilot"))
    queue = RedisQueue(redis_client)
    check_publisher = LocalCheckPublisher()
    owner = os.getenv("GITHUB_OWNER")
    repository = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")
    if owner and repository and token:
        github_publisher = GitHubPublisherClient(owner, repository, token)
        check_publisher = GitHubCheckPublisher(github_publisher)
    else:
        github_publisher = None
    dispatcher = StageDispatcher(store, queue, check_publisher, github_publisher=github_publisher)
    log_event(
        logger,
        "worker_started",
        queue="repopilot:runs",
        github_publisher_configured=github_publisher is not None,
        database_configured=bool(os.getenv("DATABASE_URL")),
        redis_configured=bool(os.getenv("REDIS_URL")),
    )
    worker = RunWorker(queue, store, dispatcher.dispatch)
    while True:
        worker.run_once()
        time.sleep(1)


if __name__ == "__main__":
    main()
