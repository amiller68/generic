"""
Create a new chat thread with a single message from the user.

Thin wrapper that delegates to ThreadManager for thread lifecycle.
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
        """
        Dispatch a completion task.

        Args:
            user_id: The user who owns the thread
            completion_id: The completion to process
        """
        ...


@dataclass
class Params:
    """Parameters for create_thread operation."""

    user_id: str
    parts: list[ContentPart]
    dispatch_task: DispatchCompletionTask | None = field(default=None)
    """Optional callback to dispatch the completion task to a background worker."""


@dataclass
class Context:
    """Dependencies for create_thread operation."""

    db: AsyncSession
    logger: Logger


@dataclass
class Result:
    """Result of create_thread operation."""

    thread_id: str
    message_id: str
    completion_id: str


async def create_thread(
    params: Params,
    ctx: Context,
) -> Result:
    """
    Create a new chat thread with an initial user message.

    Args:
        params: User ID and message parts
        ctx: Database session, logger, and task dispatcher

    Returns:
        Result with thread_id, message_id, and completion_id
    """
    manager, completion = await ThreadManager.create(
        ctx.db, params.user_id, params.parts
    )
    await ctx.db.commit()

    ctx.logger.info(f"Created thread {manager.thread.id} for user {params.user_id}")

    # Dispatch completion task if callback provided
    if params.dispatch_task is not None:
        await params.dispatch_task(params.user_id, completion.id)

    return Result(
        thread_id=manager.thread.id,
        message_id=manager.messages[0].id,
        completion_id=completion.id,
    )
