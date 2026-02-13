"""
Cancel thread operation.

Requests cancellation of a running thread.
"""

from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models.completion import Completion, CompletionStatus
from py_core.database.models.thread import Thread

from .engine import get_cancel_key


@dataclass
class CancelResult:
    """Result of a cancel operation."""

    thread_id: str
    cancelled: bool
    message: str | None = None


@dataclass
class Params:
    """Parameters for cancel_thread operation."""

    thread_id: str
    user_id: str
    ttl_seconds: int = 60


@dataclass
class Context:
    """Dependencies for cancel_thread operation."""

    db: AsyncSession
    redis: Redis


async def request_cancel(
    params: Params,
    ctx: Context,
) -> CancelResult:
    """
    Request cancellation of a running thread.

    Only sets the cancellation signal if the thread has an active
    completion (PENDING or PROCESSING). If not, returns immediately.

    The engine will detect the Redis key and handle status update.

    Args:
        params: Thread ID, user ID, and optional TTL
        ctx: Database session and Redis client

    Returns:
        CancelResult with status and message
    """
    # Load thread and active completion in one query
    result = await ctx.db.execute(
        select(Thread, Completion)
        .outerjoin(
            Completion,
            (Completion.thread_id == Thread.id)
            & Completion.status.in_(
                [CompletionStatus.PENDING, CompletionStatus.PROCESSING]
            ),
        )
        .where(
            Thread.id == params.thread_id,
            Thread.user_id == params.user_id,
        )
    )
    row = result.one_or_none()

    if not row:
        return CancelResult(
            thread_id=params.thread_id,
            cancelled=False,
            message="Thread not found",
        )

    thread, completion = row

    if not completion:
        return CancelResult(
            thread_id=params.thread_id,
            cancelled=False,
            message="Thread is not currently processing",
        )

    # Active completion found - set cancellation signal
    # The engine will detect this and update status
    cancel_key = get_cancel_key(completion.id)
    await ctx.redis.set(cancel_key, "1", ex=params.ttl_seconds)

    return CancelResult(
        thread_id=params.thread_id,
        cancelled=True,
    )
