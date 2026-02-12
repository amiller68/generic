"""
EventPublisher - publishes events to Redis pub/sub.

Usage:
    publisher = EventPublisher(redis_client)
    await publisher.publish(user_id, WidgetProcessedEvent(
        widget_id="123",
        new_status="active",
    ))

Events are dataclasses with a `type` field (Literal string).
The publisher is generic - any dataclass with a `type` field works.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from redis.asyncio import Redis

from .base import EventEnvelope


class EventPublisher:
    """
    Generic event publisher.

    Publishes events to Redis pub/sub channels for real-time delivery
    to connected SSE/WebSocket clients.

    Events should be dataclasses with a `type` field containing a string
    identifier (e.g., "widget.created", "widget.processed").
    """

    def __init__(self, redis: Redis):
        self._redis = redis

    async def publish(self, user_id: str, event: Any) -> None:
        """
        Publish an event to the user's channel.

        Args:
            user_id: The user to send the event to
            event: A dataclass event with a `type` field
        """
        # Convert event to dict, extract type field
        event_dict = asdict(event)
        event_type = event_dict.pop("type")

        # Wrap in envelope with timestamp
        envelope = EventEnvelope(
            type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=event_dict,
        )

        # Publish to user's channel
        channel = f"events:user:{user_id}"
        await self._redis.publish(channel, json.dumps(asdict(envelope)))
