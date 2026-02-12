"""
List threads for a user.
"""

from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.observability import Logger
from py_core.database.models.thread import Thread as ThreadModel, Message

from .types import ThreadListItem


@dataclass
class Params:
    """Parameters for list_threads operation."""

    user_id: str
    offset: int = 0
    limit: int = 20


@dataclass
class Context:
    """Dependencies for list_threads operation."""

    db: AsyncSession
    logger: Logger


@dataclass
class Result:
    """Result of list_threads operation."""

    threads: list[ThreadListItem]
    total: int


async def list_threads(
    params: Params,
    ctx: Context,
) -> Result:
    """
    List threads for a user.

    Args:
        params: User ID and pagination
        ctx: Database session and logger

    Returns:
        List of threads with total count
    """
    # Get threads
    result = await ctx.db.execute(
        select(ThreadModel)
        .where(ThreadModel.user_id == params.user_id)
        .order_by(ThreadModel.updated_at.desc())
        .offset(params.offset)
        .limit(params.limit)
    )
    threads = list(result.scalars().all())

    # Get total count
    count_result = await ctx.db.execute(
        select(func.count(ThreadModel.id)).where(ThreadModel.user_id == params.user_id)
    )
    total = count_result.scalar() or 0

    # Get message counts
    thread_ids = [t.id for t in threads]
    if thread_ids:
        counts_result = await ctx.db.execute(
            select(Message.thread_id, func.count(Message.id))
            .where(Message.thread_id.in_(thread_ids))
            .group_by(Message.thread_id)
        )
        message_counts: dict[str, int] = {
            str(row[0]): int(row[1]) for row in counts_result.all()
        }
    else:
        message_counts = {}

    return Result(
        threads=[
            ThreadListItem(
                id=t.id,
                title=t.title,
                created_at=t.created_at,
                updated_at=t.updated_at,
                message_count=message_counts.get(t.id, 0),
            )
            for t in threads
        ],
        total=total,
    )
