"""
TaskIQ broker configuration for background jobs.

Usage:
    from src.tasks import broker

    @broker.task
    async def my_task(param: str) -> dict:
        return {"result": param}
"""

import os

import taskiq_fastapi
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

result_backend = RedisAsyncResultBackend(
    redis_url=REDIS_URL,
    result_ex_time=3600,
)

broker = RedisStreamBroker(
    url=REDIS_URL,
).with_result_backend(result_backend)

taskiq_fastapi.init(broker, "src.__main__:app")

__all__ = ["broker", "REDIS_URL"]

# Import jobs subpackage to register tasks with broker
from src.tasks import jobs  # noqa: E402, F401
