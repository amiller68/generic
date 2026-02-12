"""Widget SSE events for real-time updates.

This demonstrates how to use Server-Sent Events with HTMX for live updates.
The pattern:
1. Client connects to SSE endpoint (per-user channel)
2. Background tasks publish typed events via EventPublisher
3. SSE handler receives events from user's channel
4. HTMX swaps content based on event names

Event format for HTMX SSE:
    event: <event-name>
    data: <html-content>

The client subscribes with:
    <div hx-ext="sse" sse-connect="/_events/widgets">
        <div sse-swap="widget-updated-{id}">...</div>
    </div>

Events are published to per-user channels: events:user:{user_id}
"""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from redis.asyncio import Redis
from sse_starlette.sse import EventSourceResponse

from py_core.database.models import User, Widget
from py_core.events import EventPublisher, WidgetUpdatedEvent
from py_core.observability import Logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.server.deps import (
    async_db,
    logger,
    redis,
    require_admin_user,
    require_logged_in_user,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def publish_widget_event(
    redis_client: Redis,
    event_type: str,
    widget_id: str,
    user_id: str | None = None,
    data: dict | None = None,
) -> None:
    """
    Publish a widget event to Redis pub/sub.

    Call this after widget CRUD operations to notify connected clients.
    For background tasks, use EventPublisher directly with typed events instead.

    Args:
        redis_client: Redis connection
        event_type: Event name (created, updated, deleted, processing, etc.)
        widget_id: The widget ID
        user_id: The user ID (required for per-user events)
        data: Optional additional data
    """
    if user_id:
        # Use typed events for per-user channels
        publisher = EventPublisher(redis_client)
        await publisher.publish(user_id, WidgetUpdatedEvent(widget_id=widget_id))
    else:
        # Fallback to global channel for legacy/admin events
        message = json.dumps(
            {
                "type": event_type,
                "widget_id": widget_id,
                "data": data or {},
            }
        )
        await redis_client.publish("widget:events", message)


async def widget_event_generator(
    request: Request,
    redis_client: Redis,
    db: AsyncSession,
    user: User,
    log: Logger,
    template_prefix: str = "pages/app/widgets",
) -> AsyncGenerator[dict, None]:
    """
    Generate SSE events for widget updates.

    Subscribes to the user's personal Redis pub/sub channel and yields
    formatted SSE events that HTMX can use to swap content.
    """
    pubsub = redis_client.pubsub()
    user_channel = f"events:user:{user.id}"
    await pubsub.subscribe(user_channel)

    # Send initial connection event
    yield {
        "event": "connected",
        "data": "Widget events connected",
    }

    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Wait for message with timeout
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message and message["type"] == "message":
                try:
                    # Parse the EventEnvelope format
                    envelope = json.loads(message["data"])
                    event_type = envelope.get("type", "unknown")
                    payload = envelope.get("payload", {})
                    widget_id = payload.get("widget_id")

                    log.debug(f"Widget event: {event_type} for {widget_id}")

                    if event_type == "widget.deleted":
                        # For deleted widgets, send empty content to remove the row
                        yield {
                            "event": f"widget-deleted-{widget_id}",
                            "data": "",
                        }

                    elif event_type == "widget.processing":
                        # For processing widgets, send a processing indicator
                        widget = await Widget.read(id=widget_id, session=db, logger=log)
                        if widget:
                            html = templates.get_template(
                                f"{template_prefix}/row.html"
                            ).render(
                                request=request,
                                user=user,
                                widget=widget,
                                processing=True,
                            )
                            yield {
                                "event": f"widget-updated-{widget_id}",
                                "data": html,
                            }

                    elif event_type in (
                        "widget.created",
                        "widget.updated",
                        "widget.processed",
                    ):
                        # Fetch the updated widget and render its row
                        widget = await Widget.read(id=widget_id, session=db, logger=log)
                        if widget:
                            # Render the row template
                            html = templates.get_template(
                                f"{template_prefix}/row.html"
                            ).render(
                                request=request,
                                user=user,
                                widget=widget,
                                processing=False,
                            )

                            # Send event for this specific widget
                            yield {
                                "event": f"widget-updated-{widget_id}",
                                "data": html,
                            }

                            # Also send a generic event for listeners
                            yield {
                                "event": "widget-changed",
                                "data": json.dumps(
                                    {
                                        "type": event_type,
                                        "widget_id": widget_id,
                                    }
                                ),
                            }

                    elif event_type == "widget.process_failed":
                        # For failed processing, re-render the widget row with error state
                        widget = await Widget.read(id=widget_id, session=db, logger=log)
                        if widget:
                            html = templates.get_template(
                                f"{template_prefix}/row.html"
                            ).render(
                                request=request,
                                user=user,
                                widget=widget,
                                processing=False,
                                error=payload.get("error"),
                            )
                            yield {
                                "event": f"widget-updated-{widget_id}",
                                "data": html,
                            }

                except json.JSONDecodeError:
                    log.warn(f"Invalid JSON in widget event: {message['data']}")

            # Small delay to prevent busy loop
            await asyncio.sleep(0.1)

    finally:
        await pubsub.unsubscribe(user_channel)
        await pubsub.close()


@router.get("")
async def widget_events_user(
    request: Request,
    user: User = Depends(require_logged_in_user),
    redis_client: Redis = Depends(redis),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> EventSourceResponse:
    """
    SSE endpoint for real-time widget updates (user-facing).

    Subscribes to the user's personal channel: events:user:{user_id}

    Connect from HTMX with:
        <tr hx-ext="sse"
            sse-connect="/_events/widgets"
            sse-swap="widget-updated-{widget.id}"
            hx-swap="outerHTML">
            ...
        </tr>

    Events emitted:
        - connected: Initial connection confirmation
        - widget-updated-{id}: Widget was updated, data is new HTML row
        - widget-deleted-{id}: Widget was deleted, data is empty
        - widget-changed: Generic event with JSON payload
    """
    return EventSourceResponse(
        widget_event_generator(
            request,
            redis_client,
            db,
            user,
            log,
            template_prefix="pages/app/widgets",
        ),
        ping=15,
    )


@router.get("/admin")
async def widget_events_admin(
    request: Request,
    user: User = Depends(require_admin_user),
    redis_client: Redis = Depends(redis),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> EventSourceResponse:
    """
    SSE endpoint for real-time widget updates (admin panel).

    Note: Admin still uses their own user channel for events.
    """
    return EventSourceResponse(
        widget_event_generator(
            request,
            redis_client,
            db,
            user,
            log,
            template_prefix="pages/admin/widgets",
        ),
        ping=15,
    )
