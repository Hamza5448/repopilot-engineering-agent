from apps.worker.worker.queue import RedisQueue, RunJob


class FakeRedis:
    def __init__(self):
        self.items = []

    def rpush(self, name, value):
        self.items.append((name, value))

    def lpop(self, name):
        return self.items.pop(0)[1] if self.items else None


def test_redis_queue_serializes_and_restores_run_jobs() -> None:
    queue = RedisQueue(FakeRedis())
    queue.enqueue(RunJob(run_id="run-1", repository_id=3))
    assert queue.dequeue() == RunJob(run_id="run-1", repository_id=3)
    assert queue.dequeue() is None
