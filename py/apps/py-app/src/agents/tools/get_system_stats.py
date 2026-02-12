"""
Sync tool example: Get system statistics.

Returns immediately with data.
"""

from pydantic import BaseModel
from pydantic_ai import RunContext
from sqlalchemy import select, func

from py_core.ai_ml import AgentDeps
from py_core.ai_ml.tools import ToolResultBase, completed, tool
from py_core.ai_ml.types import TextPart
from py_core.database.models import User, Widget


class SystemStatsPayload(BaseModel):
    """Payload for system stats."""

    total_users: int
    approved_users: int
    total_widgets: int
    active_widgets: int


@tool
async def get_system_stats(ctx: RunContext[AgentDeps]) -> ToolResultBase:
    """Get current system statistics."""
    db = ctx.deps.db

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    approved_users = (
        await db.execute(select(func.count(User.id)).where(User.approved.is_(True)))
    ).scalar() or 0
    total_widgets = (await db.execute(select(func.count(Widget.id)))).scalar() or 0
    active_widgets = (
        await db.execute(select(func.count(Widget.id)).where(Widget.status == "active"))
    ).scalar() or 0

    payload = SystemStatsPayload(
        total_users=total_users,
        approved_users=approved_users,
        total_widgets=total_widgets,
        active_widgets=active_widgets,
    )

    summary = f"Users: {total_users} ({approved_users} approved), Widgets: {total_widgets} ({active_widgets} active)"

    return completed(
        data=payload,
        message="Stats retrieved",
        content_parts=[TextPart(content=summary)],
    )
