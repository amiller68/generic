"""Complete async tool execution operation."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models.async_tool_execution import (
    AsyncToolExecution,
    AsyncToolExecutionStatus,
)
from py_core.database.utils import utcnow
from py_core.observability import Logger


@dataclass
class Params:
    """Parameters for completing an async tool execution."""

    execution_id: str
    result: dict[str, Any] | None = None


@dataclass
class Context:
    """Dependencies for completing an async tool execution."""

    db: AsyncSession
    logger: Logger


@dataclass
class Result:
    """Result of completing an async tool execution."""

    updated: bool


async def complete_async_tool_execution(
    params: Params,
    ctx: Context,
) -> Result:
    """
    Mark an AsyncToolExecution as completed.

    Args:
        params: Execution ID and optional result data
        ctx: Database session and logger

    Returns:
        Result indicating whether the execution was found and updated
    """
    stmt = (
        update(AsyncToolExecution)
        .where(AsyncToolExecution.id == params.execution_id)
        .values(
            status=AsyncToolExecutionStatus.COMPLETED.value,
            result=params.result,
            completed_at=utcnow(),
        )
    )
    result = await ctx.db.execute(stmt)
    updated = (getattr(result, "rowcount", 0) or 0) > 0

    if updated:
        ctx.logger.debug(f"Completed async tool execution: {params.execution_id}")
    else:
        ctx.logger.warn(f"No async tool execution found: {params.execution_id}")

    return Result(updated=updated)
