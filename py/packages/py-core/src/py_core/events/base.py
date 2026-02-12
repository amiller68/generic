"""
Base event types.

Events are dataclasses with a `type` field containing a Literal string.
The publisher wraps each event in an EventEnvelope for wire format.

+------------------------------------------------------------------------------+
|  ADDING NEW EVENTS                                                            |
|                                                                               |
|  To add a new event:                                                          |
|  1. Create the event dataclass with a Literal type field                     |
|  2. Export from py_core/events/__init__.py                                   |
+------------------------------------------------------------------------------+
"""

from dataclasses import dataclass


@dataclass
class EventEnvelope:
    """
    Wire format sent over SSE/WebSocket.
    The publisher wraps each event in this envelope.
    """

    type: str  # e.g., "widget.processed", "widget.created"
    timestamp: str  # ISO8601
    payload: dict  # Event fields (minus 'type')
