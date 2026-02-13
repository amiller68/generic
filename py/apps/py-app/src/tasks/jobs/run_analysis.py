"""
Background task for run_analysis tool.

Uses @with_async_tool_lifecycle to automatically handle:
- Completing the AsyncToolExecution record
- Publishing completion/failure events
"""

import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import Context, TaskiqDepends

from py_core.ai_ml.tools import AsyncToolPayload, with_async_tool_lifecycle
from py_core.ai_ml.types import ContentPart, TextPart
from py_core.database.models import User, Widget
from py_core.events import EventPublisher
from py_core.observability import Logger

from src.tasks import broker
from src.tasks.deps import (
    get_db_session,
    get_event_publisher,
    get_logger,
    get_taskiq_context,
)


class AnalysisResultPayload(AsyncToolPayload):
    """Result payload for analysis task."""

    analysis_type: str
    days: int
    summary: str
    data: dict

    # Pending state (class methods - no data yet)
    @classmethod
    def format_pending_message(cls) -> str:
        return "Analysis started..."

    @classmethod
    def format_pending_content_parts(cls) -> list[ContentPart]:
        return [
            TextPart(
                content="Analysis is running in the background. Results will be delivered when complete."
            )
        ]

    # Completed state (instance methods - has data)
    def format_message(self) -> str:
        return f"Analysis complete: {self.analysis_type}"

    def format_content_parts(self) -> list[ContentPart]:
        return [TextPart(content=self.summary)]


@broker.task
@with_async_tool_lifecycle(payload_cls=AnalysisResultPayload)
async def run_analysis_task(
    analysis_type: str,
    days: int = 7,
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
    events: EventPublisher = TaskiqDepends(get_event_publisher),
    _taskiq_ctx: Context = TaskiqDepends(get_taskiq_context),
) -> AnalysisResultPayload:
    """
    Run analysis in background.

    The @with_async_tool_lifecycle decorator handles:
    - Completing the AsyncToolExecution record
    - Publishing completion/failure events

    Args:
        analysis_type: "user_activity" or "widget_usage"
        days: Number of days to analyze
    """
    logger.info(f"Running {analysis_type} analysis for {days} days")

    # Simulate some work
    await asyncio.sleep(2)

    # Run actual analysis
    if analysis_type == "user_activity":
        data = await _analyze_user_activity(db, days)
    elif analysis_type == "widget_usage":
        data = await _analyze_widget_usage(db, days)
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")

    logger.info(f"Analysis complete: {analysis_type}")

    return AnalysisResultPayload(
        analysis_type=analysis_type,
        days=days,
        summary=data["summary"],
        data=data,
    )


async def _analyze_user_activity(db: AsyncSession, days: int) -> dict:
    """Analyze user activity."""
    total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    approved = (
        await db.execute(select(func.count(User.id)).where(User.approved.is_(True)))
    ).scalar() or 0

    rate = f"{(approved / total * 100):.1f}%" if total > 0 else "N/A"
    summary = (
        f"Analyzed {total} users over {days} days. {approved} approved ({rate} approval rate)."
        if total > 0
        else "No users found."
    )

    return {
        "analysis_type": "user_activity",
        "days": days,
        "total_users": total,
        "approved_users": approved,
        "approval_rate": rate,
        "summary": summary,
    }


async def _analyze_widget_usage(db: AsyncSession, days: int) -> dict:
    """Analyze widget usage."""
    total = (await db.execute(select(func.count(Widget.id)))).scalar() or 0
    active = (
        await db.execute(select(func.count(Widget.id)).where(Widget.status == "active"))
    ).scalar() or 0
    draft = (
        await db.execute(select(func.count(Widget.id)).where(Widget.status == "draft"))
    ).scalar() or 0

    rate = f"{(active / total * 100):.1f}%" if total > 0 else "N/A"
    summary = (
        f"Analyzed {total} widgets over {days} days. {active} active ({rate}), {draft} draft."
        if total > 0
        else "No widgets found."
    )

    return {
        "analysis_type": "widget_usage",
        "days": days,
        "total_widgets": total,
        "active_widgets": active,
        "draft_widgets": draft,
        "activation_rate": rate,
        "summary": summary,
    }
