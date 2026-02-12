"""Create async tool execution operation."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models.async_tool_execution import (
    AsyncToolExecution,
    AsyncToolExecutionStatus,
)
from py_core.observability import Logger


@dataclass
class Params:
    """Parameters for creating an async tool execution."""

    thread_id: str
    name: str
    completion_id: str | None = None
    timeout_seconds: int | None = None
    ref_type: str | None = None
    ref_id: str | None = None


@dataclass
class Context:
    """Dependencies for creating an async tool execution."""

    db: AsyncSession
    logger: Logger


@dataclass
class Result:
    """Result of creating an async tool execution."""

    execution_id: str


async def create_async_tool_execution(
    params: Params,
    ctx: Context,
) -> Result:
    """
    Create an AsyncToolExecution record to track an async operation.

    Args:
        params: Thread ID, tool name, and optional ref_type/ref_id
        ctx: Database session and logger

    Returns:
        Result with the execution ID
    """
    execution = AsyncToolExecution(
        thread_id=params.thread_id,
        completion_id=params.completion_id,
        name=params.name,
        timeout_seconds=params.timeout_seconds,
        ref_type=params.ref_type,
        ref_id=params.ref_id,
        status=AsyncToolExecutionStatus.PENDING.value,
    )
    ctx.db.add(execution)
    await ctx.db.flush()

    execution_id = str(execution.id)
    ctx.logger.debug(
        f"Created async tool execution: id={execution_id}, name={params.name}"
    )

    return Result(execution_id=execution_id)
