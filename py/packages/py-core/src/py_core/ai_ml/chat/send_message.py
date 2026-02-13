"""
Send message to an existing thread.

Adds a user message and creates a pending completion.
"""

from dataclasses import dataclass, field
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from py_core.ai_ml.types.llm import ContentPart
from py_core.observability import Logger

from .engine import ThreadManager


class DispatchCompletionTask(Protocol):
    """Protocol for dispatching a completion task to a background worker."""

    async def __call__(self, user_id: str, completion_id: str) -> None:
        """Dispatch a completion task."""
        ...


@dataclass
class Params:
    """Parameters for send_message operation."""

    user_id: str
    thread_id: str
    parts: list[ContentPart]
    dispatch_task: DispatchCompletionTask | None = field(default=None)


@dataclass
class Context:
    """Dependencies for send_message operation."""

    db: AsyncSession
    logger: Logger


@dataclass
class Result:
    """Result of send_message operation."""

    thread_id: str
    message_id: str
    completion_id: str


async def send_message(
    params: Params,
    ctx: Context,
) -> Result:
    """
    Send a message to an existing chat thread.

    Args:
        params: User ID, thread ID, and message parts
        ctx: Database session and logger

    Returns:
        Result with thread_id, message_id, and completion_id

    Raises:
        ThreadNotFound: If thread doesn't exist or user doesn't have access
        CompletionInProgress: If thread already has an active completion
    """
    # Load thread for this user
    manager = await ThreadManager.load_for_send(
        ctx.db, params.thread_id, params.user_id
    )

    # Add message and create completion
    message, completion = await manager.add_message_and_complete(ctx.db, params.parts)
    await ctx.db.commit()

    ctx.logger.info(
        f"Added message to thread: thread_id={params.thread_id}, "
        f"completion_id={completion.id}"
    )

    # Dispatch completion task if callback provided
    if params.dispatch_task is not None:
        await params.dispatch_task(params.user_id, completion.id)

    return Result(
        thread_id=params.thread_id,
        message_id=message.id,
        completion_id=completion.id,
    )
