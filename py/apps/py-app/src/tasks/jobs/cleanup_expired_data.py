"""Example cron job: clean up expired cron job run records."""

from datetime import timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from py_core.database.models.cron_job_run import CronJobRun
from py_core.database.utils import utcnow
from py_core.observability import Logger

from src.tasks.cron import cron
from src.tasks.deps import get_db_session, get_logger


@cron("*/5 * * * *", lock_ttl=120)
async def cleanup_expired_data(
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
) -> dict:
    """Clean up expired cron job run records older than 7 days."""
    cutoff = utcnow() - timedelta(days=7)
    result = await db.execute(delete(CronJobRun).where(CronJobRun.created_at < cutoff))
    await db.commit()
    deleted_count = result.rowcount
    logger.info(f"Cleaned up {deleted_count} expired cron job runs")
    return {"deleted_count": deleted_count}
