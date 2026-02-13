"""Admin dashboard page."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from redis.asyncio import Redis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models import User, Widget
from py_core.database.models.cron_job_run import CronJobRun
from py_core.observability import Logger

from src.server.deps import async_db, logger, redis, require_admin_user
from src.server.templates import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def admin_index(
    request: Request,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
) -> HTMLResponse:
    """Render the admin dashboard."""
    stats = await get_system_stats(db)

    return templates.TemplateResponse(
        "pages/admin/dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
        },
    )


@router.get("/partials/health", response_class=HTMLResponse)
async def health_partial(
    request: Request,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    redis_client: Redis = Depends(redis),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """HTMX partial for health status refresh."""
    health = await check_all_health(db, redis_client, log)

    return templates.TemplateResponse(
        "pages/admin/partials/health_status.html",
        {
            "request": request,
            "health": health,
        },
    )


async def get_system_stats(db: AsyncSession) -> dict[str, Any]:
    """Get system statistics."""
    try:
        user_count_result = await db.execute(select(func.count(User.id)))
        user_count = user_count_result.scalar() or 0

        pending_count_result = await db.execute(
            select(func.count(User.id)).where(User.approved == False)  # noqa: E712
        )
        pending_count = pending_count_result.scalar() or 0

        widget_count_result = await db.execute(select(func.count(Widget.id)))
        widget_count = widget_count_result.scalar() or 0

        active_widget_count_result = await db.execute(
            select(func.count(Widget.id)).where(Widget.status == "active")
        )
        active_widget_count = active_widget_count_result.scalar() or 0

        cron_count_result = await db.execute(select(func.count(CronJobRun.id)))
        cron_count = cron_count_result.scalar() or 0

        return {
            "user_count": user_count,
            "pending_count": pending_count,
            "widget_count": widget_count,
            "active_widget_count": active_widget_count,
            "cron_count": cron_count,
        }
    except Exception:
        return {
            "user_count": "?",
            "pending_count": "?",
            "widget_count": "?",
            "active_widget_count": "?",
            "cron_count": "?",
        }


async def check_all_health(
    db: AsyncSession,
    redis_client: Redis,
    log: Logger,
) -> dict[str, dict[str, Any]]:
    """Check health of all services."""
    health: dict[str, dict[str, Any]] = {}

    # Database health
    try:
        await db.execute(text("SELECT 1"))
        health["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        log.error(f"Database health check failed: {e}")
        health["database"] = {"status": "unhealthy", "message": str(e)}

    # Redis health
    try:
        result = redis_client.ping()
        if hasattr(result, "__await__"):
            await result
        health["redis"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        log.error(f"Redis health check failed: {e}")
        health["redis"] = {"status": "unhealthy", "message": str(e)}

    return health
