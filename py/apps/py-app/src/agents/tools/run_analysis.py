"""
Async tool example: Run background analysis.

Dispatches a background job and returns pending status.
Results delivered via events when complete.
"""

from pydantic_ai import RunContext

from py_core.ai_ml import AgentDeps
from py_core.ai_ml.chat.async_tool_execution import (
    CreateContext,
    CreateParams,
    create_async_tool_execution,
)
from py_core.ai_ml.tools import (
    LABEL_EXECUTION_ID,
    AsyncToolRefType,
    ToolResultBase,
    pending,
    tool,
    validation_error,
)
from py_core.ai_ml.types import TextPart

from src.tasks.jobs.run_analysis import AnalysisResultPayload, run_analysis_task

VALID_ANALYSIS_TYPES = ["user_activity", "widget_usage"]


@tool
async def run_analysis(
    ctx: RunContext[AgentDeps],
    analysis_type: str,
    days: int = 7,
) -> ToolResultBase:
    """
    Run a background analysis task.

    Args:
        ctx: Pydantic AI run context
        analysis_type: Type of analysis ("user_activity" or "widget_usage")
        days: Number of days to analyze (default 7)

    Returns:
        PendingResult - results delivered via events when complete
    """
    # Validate analysis type
    if analysis_type not in VALID_ANALYSIS_TYPES:
        return validation_error(
            message=f"Invalid analysis type: {analysis_type}",
            content_parts=[
                TextPart(
                    content=f"Error: analysis_type must be one of {VALID_ANALYSIS_TYPES}"
                )
            ],
        )

    # Validate days
    if days < 1 or days > 365:
        return validation_error(
            message="Days must be between 1 and 365",
            content_parts=[TextPart(content="Error: days must be between 1 and 365")],
        )

    # Create async tool execution record using library function
    if not ctx.deps.thread_id:
        return validation_error(
            message="Thread context required for async operations",
            content_parts=[TextPart(content="Error: missing thread context")],
        )

    exec_result = await create_async_tool_execution(
        params=CreateParams(
            thread_id=ctx.deps.thread_id,
            completion_id=ctx.deps.completion_id,
            name="run_analysis",
            timeout_seconds=300,  # 5 min timeout
            ref_type=AsyncToolRefType.ANALYSIS.value,
        ),
        ctx=CreateContext(
            db=ctx.deps.db,
            logger=ctx.deps.logger,
        ),
    )

    # Commit before dispatching task
    await ctx.deps.db.commit()

    # Dispatch background task with execution_id label
    await run_analysis_task.kicker().with_labels(
        **{LABEL_EXECUTION_ID: exec_result.execution_id}
    ).kiq(
        analysis_type=analysis_type,
        days=days,
    )

    ctx.deps.logger.info(
        f"Dispatched analysis: execution_id={exec_result.execution_id}, type={analysis_type}"
    )

    return pending(
        message=AnalysisResultPayload.format_pending_message(),
        content_parts=AnalysisResultPayload.format_pending_content_parts(),
        ref_type=AsyncToolRefType.ANALYSIS.value,
        ref_id=exec_result.execution_id,
    )
