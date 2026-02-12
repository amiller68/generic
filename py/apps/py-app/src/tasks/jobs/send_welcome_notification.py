"""Example background task: send welcome notification when user is approved."""

from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from py_core.database.models import User
from py_core.observability import Logger

from src.tasks import broker
from src.tasks.deps import get_db_session, get_logger


@broker.task
async def send_welcome_notification(
    user_id: str,
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
) -> dict:
    """Log a welcome message when user is approved."""
    user = await User.read(id=user_id, session=db, logger=logger)
    if user:
        logger.info(f"Welcome notification for {user.email}")
    return {"user_id": user_id, "status": "sent"}
