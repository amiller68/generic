from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models import User, Widget, WidgetStatus
from src.server.deps import require_logged_in_user, async_db, logger
from src.server.handlers.page import PageResponse
from py_core.observability import Logger

# Create page response helper
page = PageResponse(template="pages/app/dashboard.html", layout="layouts/app.html")


async def handler(
    request: Request,
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    logger: Logger = Depends(logger),
):
    """Dashboard page - requires authentication

    Args:
        request: The incoming request
        user: Current authenticated user (auto-injected via deps)
        db: Database session
        logger: Request span for logging

    Returns:
        HTMLResponse with full layout or just content for HTMX
    """
    logger.info(f"Dashboard access by user: {user.email}")

    # Fetch widget stats for the user
    total_widgets = await Widget.count_all(session=db, owner_id=str(user.id))
    active_widgets = await Widget.count_all(
        session=db, owner_id=str(user.id), status=WidgetStatus.ACTIVE
    )
    draft_widgets = await Widget.count_all(
        session=db, owner_id=str(user.id), status=WidgetStatus.DRAFT
    )

    # Fetch recent widgets
    recent_widgets = await Widget.list_all(session=db, owner_id=str(user.id), limit=5)

    return page.render(
        request,
        {
            "user": user,
            "total_widgets": total_widgets,
            "active_widgets": active_widgets,
            "draft_widgets": draft_widgets,
            "recent_widgets": recent_widgets,
        },
    )
