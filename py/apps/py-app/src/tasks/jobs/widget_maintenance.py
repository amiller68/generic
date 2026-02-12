"""Example cron job: widget maintenance tasks."""

from datetime import timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from py_core.database.models import Widget, WidgetStatus
from py_core.database.utils import utcnow
from py_core.observability import Logger

from src.tasks.cron import cron
from src.tasks.deps import get_db_session, get_logger


@cron("0 */6 * * *", lock_ttl=300)  # Every 6 hours
async def archive_stale_widgets(
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
) -> dict:
    """
    Archive widgets that have been in draft status for more than 30 days.

    This demonstrates a cron job that:
    - Runs on a schedule
    - Performs bulk updates
    - Uses database locking to prevent duplicate runs
    """
    cutoff = utcnow() - timedelta(days=30)

    result = await db.execute(
        update(Widget)
        .where(Widget.status == WidgetStatus.DRAFT.value)
        .where(Widget.updated_at < cutoff)
        .values(status=WidgetStatus.ARCHIVED.value)
    )
    await db.commit()

    archived_count = result.rowcount
    logger.info(f"Archived {archived_count} stale widgets")

    return {"archived_count": archived_count}


@cron("0 3 * * *", lock_ttl=600)  # Daily at 3 AM
async def generate_widget_stats(
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
) -> dict:
    """
    Generate daily widget statistics.

    This demonstrates a daily cron job for reporting/analytics.
    """
    draft_count = await Widget.count_all(
        session=db, status=WidgetStatus.DRAFT, logger=logger
    )
    active_count = await Widget.count_all(
        session=db, status=WidgetStatus.ACTIVE, logger=logger
    )
    archived_count = await Widget.count_all(
        session=db, status=WidgetStatus.ARCHIVED, logger=logger
    )
    total_count = draft_count + active_count + archived_count

    stats = {
        "total": total_count,
        "draft": draft_count,
        "active": active_count,
        "archived": archived_count,
        "generated_at": utcnow().isoformat(),
    }

    logger.info(f"Widget stats: {stats}")

    return stats
