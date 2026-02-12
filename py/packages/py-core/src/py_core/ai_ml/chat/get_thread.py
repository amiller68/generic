"""
Get a single thread with its messages.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from py_core.observability import Logger
from py_core.database.models.thread import Thread as ThreadModel

from .exceptions import ThreadNotFound
from .types import Message, Thread


@dataclass
class Params:
    """Parameters for get_thread operation."""

    user_id: str
    thread_id: str


@dataclass
class Context:
    """Dependencies for get_thread operation."""

    db: AsyncSession
    logger: Logger


async def get_thread(
    params: Params,
    ctx: Context,
) -> Thread:
    """
    Get a thread with its messages.

    Args:
        params: User ID and thread ID
        ctx: Database session and logger

    Returns:
        Thread with messages

    Raises:
        ThreadNotFound: If thread doesn't exist or user doesn't have access
    """
    result = await ctx.db.execute(
        select(ThreadModel)
        .options(selectinload(ThreadModel.messages))
        .where(
            ThreadModel.id == params.thread_id,
            ThreadModel.user_id == params.user_id,
        )
    )
    thread = result.scalar_one_or_none()

    if not thread:
        raise ThreadNotFound(f"Thread {params.thread_id} not found")

    return Thread(
        id=thread.id,
        user_id=thread.user_id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        messages=[
            Message(
                id=m.id,
                thread_id=m.thread_id,
                role=m.role.value if hasattr(m.role, "value") else str(m.role),
                parts=m.parts,
                created_at=m.created_at,
                completion_id=m.completion_id,
            )
            for m in thread.messages
        ],
    )
