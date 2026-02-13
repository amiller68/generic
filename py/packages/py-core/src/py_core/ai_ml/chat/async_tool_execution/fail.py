"""Fail async tool execution operation."""

from dataclasses import dataclass

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models.async_tool_execution import (
    AsyncToolExecution,
    AsyncToolExecutionErrorType,
    AsyncToolExecutionStatus,
)
from py_core.database.utils import utcnow
from py_core.observability import Logger


@dataclass
class Params:
    """Parameters for failing an async tool execution."""

    execution_id: str
    error_type: AsyncToolExecutionErrorType
    error_message: str


@dataclass
class Context:
    """Dependencies for failing an async tool execution."""

    db: AsyncSession
    logger: Logger


@dataclass
class Result:
    """Result of failing an async tool execution."""

    updated: bool


async def fail_async_tool_execution(
    params: Params,
    ctx: Context,
) -> Result:
    """
    Mark an AsyncToolExecution as failed.

    Args:
        params: Execution ID, error type, and error message
        ctx: Database session and logger

    Returns:
        Result indicating whether the execution was found and updated
    """
    stmt = (
        update(AsyncToolExecution).where(AsyncToolExecution.id == params.execution_id)
        # Note: Using .value for Core update() - TypeDecorator may not bind automatically
        .values(
            status=AsyncToolExecutionStatus.FAILED.value,
            error_type=params.error_type.value,
            error_message=params.error_message,
            completed_at=utcnow(),
        )
    )
    result = await ctx.db.execute(stmt)
    updated = (getattr(result, "rowcount", 0) or 0) > 0

    if updated:
        ctx.logger.debug(f"Failed async tool execution: {params.execution_id}")
    else:
        ctx.logger.warn(f"No async tool execution found: {params.execution_id}")

    return Result(updated=updated)
