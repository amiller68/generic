"""Widget event type definitions.

Events are dataclasses with a `type` field containing a Literal string.
They are published to per-user channels and delivered via WebSocket/SSE.

+------------------------------------------------------------------------------+
|  FRONTEND SYNC REQUIRED                                                       |
|                                                                               |
|  When modifying events, you should update frontend TypeScript types          |
+------------------------------------------------------------------------------+
"""

from dataclasses import dataclass, field
from typing import Literal

# ============ Widget Events ============


@dataclass
class WidgetCreatedEvent:
    """Published when a widget is created."""

    type: Literal["widget.created"] = field(default="widget.created", init=False)
    widget_id: str


@dataclass
class WidgetUpdatedEvent:
    """Published when a widget is updated."""

    type: Literal["widget.updated"] = field(default="widget.updated", init=False)
    widget_id: str


@dataclass
class WidgetDeletedEvent:
    """Published when a widget is deleted."""

    type: Literal["widget.deleted"] = field(default="widget.deleted", init=False)
    widget_id: str


@dataclass
class WidgetProcessingEvent:
    """Published when widget processing starts."""

    type: Literal["widget.processing"] = field(default="widget.processing", init=False)
    widget_id: str
    message: str = "Processing started"


@dataclass
class WidgetProcessedEvent:
    """Published when widget processing completes."""

    type: Literal["widget.processed"] = field(default="widget.processed", init=False)
    widget_id: str
    new_status: str
    message: str = "Processing complete"


@dataclass
class WidgetProcessFailedEvent:
    """Published when widget processing fails."""

    type: Literal["widget.process_failed"] = field(
        default="widget.process_failed", init=False
    )
    widget_id: str
    error: str


# ============ Thread/Chat Events ============


@dataclass
class ThreadStreamEvent:
    """Published for each streaming chunk during completion."""

    type: Literal["thread.stream"] = field(default="thread.stream", init=False)
    completion_id: str
    chunk: str
    done: bool = False


@dataclass
class ThreadCompletedEvent:
    """Published when a completion finishes successfully."""

    type: Literal["thread.completed"] = field(default="thread.completed", init=False)
    completion_id: str
    thread_id: str


@dataclass
class ThreadCancelledEvent:
    """Published when a completion is cancelled by the user."""

    type: Literal["thread.cancelled"] = field(default="thread.cancelled", init=False)
    completion_id: str


@dataclass
class ThreadFailedEvent:
    """Published when a completion fails."""

    type: Literal["thread.failed"] = field(default="thread.failed", init=False)
    completion_id: str
    error_type: str
    error: str


# ============ Async Tool Execution Events ============


@dataclass
class AsyncToolExecutionStartedEvent:
    """Published when an async tool execution starts."""

    type: Literal["async_tool.started"] = field(
        default="async_tool.started", init=False
    )
    execution_id: str
    thread_id: str
    tool_name: str


@dataclass
class AsyncToolExecutionCompletedEvent:
    """Published when an async tool execution completes."""

    type: Literal["async_tool.completed"] = field(
        default="async_tool.completed", init=False
    )
    execution_id: str
    thread_id: str
    tool_name: str


@dataclass
class AsyncToolExecutionFailedEvent:
    """Published when an async tool execution fails."""

    type: Literal["async_tool.failed"] = field(default="async_tool.failed", init=False)
    execution_id: str
    thread_id: str
    tool_name: str
    error: str
