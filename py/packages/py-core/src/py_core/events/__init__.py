"""
Event infrastructure for real-time updates via SSE/WebSocket.

This module provides:
- EventPublisher for sending events to users
- EventEnvelope for wire format
- Widget event types

Usage:
    from py_core.events import EventPublisher, WidgetProcessedEvent

    publisher = EventPublisher(redis_client)
    await publisher.publish(user_id, WidgetProcessedEvent(
        widget_id="123",
        new_status="active",
    ))

+------------------------------------------------------------------------------+
|  ADDING NEW EVENTS                                                            |
|                                                                               |
|  To add a new event:                                                          |
|  1. Create the event dataclass in types.py with a Literal type field         |
|  2. Export from this __init__.py                                              |
+------------------------------------------------------------------------------+
"""

from .base import EventEnvelope
from .publisher import EventPublisher
from .types import (
    # Widget events
    WidgetCreatedEvent,
    WidgetDeletedEvent,
    WidgetProcessedEvent,
    WidgetProcessFailedEvent,
    WidgetProcessingEvent,
    WidgetUpdatedEvent,
    # Thread/Chat events
    ThreadStreamEvent,
    ThreadCompletedEvent,
    ThreadCancelledEvent,
    ThreadFailedEvent,
    # Async tool execution events
    AsyncToolExecutionStartedEvent,
    AsyncToolExecutionCompletedEvent,
    AsyncToolExecutionFailedEvent,
)

__all__ = [
    # Infrastructure
    "EventEnvelope",
    "EventPublisher",
    # Widget events
    "WidgetCreatedEvent",
    "WidgetDeletedEvent",
    "WidgetProcessedEvent",
    "WidgetProcessFailedEvent",
    "WidgetProcessingEvent",
    "WidgetUpdatedEvent",
    # Thread/Chat events
    "ThreadStreamEvent",
    "ThreadCompletedEvent",
    "ThreadCancelledEvent",
    "ThreadFailedEvent",
    # Async tool execution events
    "AsyncToolExecutionStartedEvent",
    "AsyncToolExecutionCompletedEvent",
    "AsyncToolExecutionFailedEvent",
]
