"""
Task decorator for optional AsyncToolExecution lifecycle handling.

This decorator enables tasks to optionally handle the AsyncToolExecution
lifecycle when called from a chat context. The decision is based on labels
passed at call time via TaskIQ's kicker API.

Usage:
    from taskiq import Context, TaskiqDepends
    from py_core.ai_ml.tools import (
        AsyncToolPayload,
        with_async_tool_lifecycle,
        LABEL_EXECUTION_ID,
    )

    class AnalysisResultPayload(AsyncToolPayload):
        analysis_type: str
        result: dict

        def format_message(self) -> str:
            return f"Analysis complete: {self.analysis_type}"

        def format_content_parts(self) -> list:
            return [TextPart(content=f"Analysis result: {self.result}")]

    @broker.task
    @with_async_tool_lifecycle(payload_cls=AnalysisResultPayload)
    async def run_analysis_task(
        analysis_type: str,
        db: AsyncSession = TaskiqDepends(get_db_session),
        logger: Logger = TaskiqDepends(get_logger),
        events: EventPublisher = TaskiqDepends(get_event_publisher),
        _taskiq_ctx: Context = TaskiqDepends(get_taskiq_context),  # Required!
    ) -> AnalysisResultPayload:
        result = await do_analysis(...)
        return AnalysisResultPayload(...)

Call with execution_id label for chat context:
    await run_analysis_task.kicker().with_labels(
        **{LABEL_EXECUTION_ID: execution.id}
    ).kiq(analysis_type)

Call normally for standalone:
    await run_analysis_task.kiq(analysis_type)
"""

from __future__ import annotations

import functools
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from taskiq import Context

from py_core.ai_ml.chat.async_tool_execution.complete import (
    Context as CompleteContext,
    Params as CompleteParams,
    complete_async_tool_execution,
)
from py_core.ai_ml.chat.async_tool_execution.fail import (
    Context as FailContext,
    Params as FailParams,
    fail_async_tool_execution,
)
from py_core.database.models.async_tool_execution import (
    AsyncToolExecution,
    AsyncToolExecutionErrorType,
)
from py_core.database.models.thread import Thread
from py_core.events import (
    AsyncToolExecutionCompletedEvent,
    AsyncToolExecutionFailedEvent,
)

from .results import completed

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from py_core.events import EventPublisher
    from py_core.observability import Logger

    from ._types import AsyncToolPayload

# Label used to pass execution context at call time
LABEL_EXECUTION_ID = "async_tool_execution_id"

T = TypeVar("T", bound="AsyncToolPayload")


def with_async_tool_lifecycle(
    payload_cls: type[T],
    ref_id_param: str | None = None,
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]
]:
    """
    Task decorator for optional AsyncToolExecution lifecycle handling.

    When the task is called with async_tool_execution_id label, the decorator:
    - Completes or fails the AsyncToolExecution record
    - Publishes AsyncToolExecutionCompleted/Failed events

    When called without labels, the task runs normally (standalone mode).

    Args:
        payload_cls: The AsyncToolPayload subclass this task returns.
                     Used for formatting the result.
        ref_id_param: Optional kwarg name that contains the domain ref_id.

    Returns:
        Decorated task function

    Note:
        The decorated task MUST have these kwargs (with TaskiqDepends):
        - db: AsyncSession
        - logger: Logger
        - events: EventPublisher
        - _taskiq_ctx: Context (via get_taskiq_context)
    """

    def decorator(
        fn: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Get TaskIQ context from kwargs
            taskiq_ctx: Context | None = kwargs.get("_taskiq_ctx")

            # Check for execution_id label to determine mode
            labels = (
                taskiq_ctx.message.labels if taskiq_ctx and taskiq_ctx.message else {}
            )
            execution_id = labels.get(LABEL_EXECUTION_ID)

            if not execution_id:
                # Standalone mode - just run the task
                return await fn(*args, **kwargs)

            # Chat mode - handle AsyncToolExecution lifecycle
            db: AsyncSession = kwargs.get("db")  # type: ignore
            logger: Logger = kwargs.get("logger")  # type: ignore
            events: EventPublisher = kwargs.get("events")  # type: ignore

            if not db or not logger or not events:
                raise ValueError(
                    "with_async_tool_lifecycle requires db, logger, and events kwargs"
                )

            # Load execution record
            execution = await db.get(AsyncToolExecution, execution_id)

            if not execution:
                logger.error(f"AsyncToolExecution not found: {execution_id}")
                return await fn(*args, **kwargs)

            # Load thread for event publishing
            thread = await db.get(Thread, execution.thread_id)

            if not thread:
                logger.error(f"Thread not found: {execution.thread_id}")
                return await fn(*args, **kwargs)

            # Note: ref_id_param is reserved for future use to link executions to domain objects
            _ = kwargs.get(ref_id_param) if ref_id_param else None

            try:
                # Run the actual task
                result: T = await fn(*args, **kwargs)

                # Format result using payload's methods
                result_data = completed(
                    data=result,
                    message=result.format_message(),
                    content_parts=result.format_content_parts(),
                ).to_dict()

                # Complete the execution
                await complete_async_tool_execution(
                    params=CompleteParams(
                        execution_id=execution_id, result=result_data
                    ),
                    ctx=CompleteContext(db=db, logger=logger),
                )
                await db.commit()

                # Publish completion event
                await events.publish(
                    thread.user_id,
                    AsyncToolExecutionCompletedEvent(
                        execution_id=execution_id,
                        thread_id=str(execution.thread_id),
                        tool_name=str(execution.name),
                    ),
                )

                logger.debug(f"AsyncToolExecution completed: {execution_id}")
                return result

            except Exception as e:
                # Fail the execution
                await fail_async_tool_execution(
                    params=FailParams(
                        execution_id=execution_id,
                        error_type=AsyncToolExecutionErrorType.INTERNAL_ERROR,
                        error_message=str(e),
                    ),
                    ctx=FailContext(db=db, logger=logger),
                )
                await db.commit()

                # Publish failure event
                await events.publish(
                    thread.user_id,
                    AsyncToolExecutionFailedEvent(
                        execution_id=execution_id,
                        thread_id=str(execution.thread_id),
                        tool_name=str(execution.name),
                        error=str(e),
                    ),
                )

                logger.error(f"AsyncToolExecution failed: {execution_id}, error={e}")
                raise

        return wrapper

    return decorator
