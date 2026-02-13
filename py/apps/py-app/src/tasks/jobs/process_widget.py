"""Background task: process a widget asynchronously.

This demonstrates the proper pattern:
1. Task receives dependencies via TaskiqDepends
2. Task creates callbacks that publish typed events
3. Task calls library function with callbacks
4. Library function does NOT know about events - it uses callbacks

Events are published via the injected EventPublisher dependency,
which sends typed events to per-user Redis pub/sub channels.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from py_core.database.models import Widget, WidgetStatus
from py_core.events import (
    EventPublisher,
    WidgetProcessedEvent,
    WidgetProcessFailedEvent,
    WidgetProcessingEvent,
    WidgetUpdatedEvent,
)
from py_core.observability import Logger
from py_core.widget import process

from src.tasks import broker
from src.tasks.deps import get_db_session, get_event_publisher, get_logger


@broker.task
async def process_widget_task(
    widget_id: str,
    user_id: str,
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
    events: EventPublisher = TaskiqDepends(get_event_publisher),
) -> dict:
    """
    Background task that processes a widget.

    This task:
    1. Creates callbacks that publish typed events
    2. Calls the library function with those callbacks
    3. Library function notifies via callbacks, not events directly

    Args:
        widget_id: ID of the widget to process
        user_id: ID of the user who owns the widget (for events)

    Events published (via callbacks):
        - WidgetProcessingEvent when task starts
        - WidgetProcessedEvent on success
        - WidgetProcessFailedEvent on error

    Usage:
        await process_widget_task.kiq(widget_id="some-uuid", user_id="user-uuid")
    """

    # Create callbacks that publish events
    async def on_started(wid: str, message: str) -> None:
        await events.publish(
            user_id,
            WidgetProcessingEvent(widget_id=wid, message=message),
        )

    async def on_complete(wid: str, new_status: str, message: str) -> None:
        await events.publish(
            user_id,
            WidgetProcessedEvent(
                widget_id=wid,
                new_status=new_status,
                message=message,
            ),
        )

    async def on_failed(wid: str, error: str) -> None:
        await events.publish(
            user_id,
            WidgetProcessFailedEvent(widget_id=wid, error=error),
        )

    # Call library function with callbacks
    ctx = process.Context(db=db, logger=logger)
    params = process.Params(
        widget_id=widget_id,
        on_started=on_started,  # type: ignore[arg-type]
        on_complete=on_complete,  # type: ignore[arg-type]
        on_failed=on_failed,  # type: ignore[arg-type]
    )

    try:
        result = await process.process_widget(params, ctx)
        await db.commit()

        return {
            "widget_id": result.widget_id,
            "name": result.name,
            "status": result.new_status,
        }

    except ValueError as e:
        # Widget not found
        return {"widget_id": widget_id, "status": "not_found", "error": str(e)}

    except Exception:
        await db.rollback()
        raise


@broker.task
async def archive_widget_task(
    widget_id: str,
    user_id: str,
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
    events: EventPublisher = TaskiqDepends(get_event_publisher),
) -> dict:
    """
    Archive a widget asynchronously.

    Args:
        widget_id: ID of the widget to archive
        user_id: ID of the user who owns the widget (for events)

    Usage:
        await archive_widget_task.kiq(widget_id="some-uuid", user_id="user-uuid")
    """
    widget = await Widget.read(id=widget_id, session=db, logger=logger)

    if not widget:
        logger.warn(f"Widget {widget_id} not found")
        return {"widget_id": widget_id, "status": "not_found"}

    logger.info(f"Archiving widget: {widget.name}")

    await widget.set_status(WidgetStatus.ARCHIVED, session=db, logger=logger)
    await db.commit()

    # Publish event for real-time UI update
    await events.publish(user_id, WidgetUpdatedEvent(widget_id=widget_id))

    return {
        "widget_id": widget_id,
        "name": widget.name,
        "status": "archived",
    }
