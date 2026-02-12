"""
Task dependency injection helpers using TaskiqDepends.

These dependencies are resolved by taskiq-fastapi when running in worker context,
providing access to database sessions, storage, and logging via the FastAPI app state.

The Request object injected by taskiq-fastapi is a mocked request that provides
access to app.state, allowing tasks to use the same dependencies as HTTP handlers.

Usage in tasks:
    from src.tasks import broker
    from src.tasks.deps import get_db_session, get_logger, get_event_publisher

    @broker.task
    async def my_task(
        param: str,
        db: AsyncSession = TaskiqDepends(get_db_session),
        logger: Logger = TaskiqDepends(get_logger),
        events: EventPublisher = TaskiqDepends(get_event_publisher),
    ) -> dict:
        logger.info(f"Processing: {param}")
        await events.publish(user_id, SomeEvent(...))
        return {"result": param}
"""

from typing import AsyncGenerator

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from py_core.events import EventPublisher
from py_core.observability import Logger


async def get_db_session(
    request: Request = TaskiqDepends(),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session from FastAPI app state.

    The session is yielded within a context manager to ensure proper cleanup.
    """
    async with request.app.state.app_state.database.session() as session:
        yield session


async def get_logger(request: Request = TaskiqDepends()) -> Logger:
    """Get logger from FastAPI app state."""
    return request.app.state.app_state.logger


async def get_redis(request: Request = TaskiqDepends()) -> Redis:
    """Get Redis client from FastAPI app state."""
    return request.app.state.app_state.redis


async def get_event_publisher(request: Request = TaskiqDepends()) -> EventPublisher:
    """Get typed event publisher for publishing real-time events."""
    return EventPublisher(request.app.state.app_state.redis)


async def get_taskiq_context(context: "Context" = TaskiqDepends()) -> "Context":
    """Get TaskIQ context for lifecycle decorator."""
    return context


from taskiq import Context  # noqa: E402

__all__ = [
    "get_db_session",
    "get_logger",
    "get_redis",
    "get_event_publisher",
    "get_taskiq_context",
]
