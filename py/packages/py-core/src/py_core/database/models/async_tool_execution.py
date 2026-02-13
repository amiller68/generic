"""
AsyncToolExecution - tracks async tool executions initiated from chat threads.

This table links async background tasks to chat threads. It enables:
- Querying all pending/completed executions for a thread on page load
- Real-time updates via events
- Rendering execution status in the chat UI

Fields:
- `name`: Human-readable tool name (e.g., "process_data", "search")
- `ref_type`: Optional type indicating which domain table contains the full object
- `ref_id`: Optional UUID reference to the domain object

When ref_type and ref_id are set, the execution references a domain object.
When not set, the execution is self-contained and all result data is stored
in the `result` field.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..client import Base
from ..utils import utcnow, uuid7_str, StringEnum


class AsyncToolExecutionStatus(str, Enum):
    """Status for async tool executions."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class AsyncToolExecutionErrorType(str, Enum):
    """Error type for failed async tool executions."""

    TIMEOUT = "timeout"
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"


class AsyncToolExecution(Base):
    """
    Tracks an async tool execution initiated from a chat thread.

    Links a thread to a background task and tracks its lifecycle.
    The result field can store lightweight data for rendering
    without needing to fetch the full domain object.

    ID format: UUID7
    """

    __tablename__ = "async_tool_executions"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid7_str)

    # Parent thread
    thread_id: Mapped[str] = mapped_column(
        ForeignKey("threads.id", ondelete="CASCADE"),
        index=True,
    )

    # Optional: which completion launched this execution
    completion_id: Mapped[str | None] = mapped_column(
        ForeignKey("completions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Human-readable tool name for display (e.g., "process_data", "search")
    name: Mapped[str] = mapped_column()

    # Per-execution timeout in seconds (used by recovery task)
    # When NULL, the recovery task uses a default timeout
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Optional: type indicator for domain objects
    # When set, use ref_type + ref_id to locate the full object.
    # When not set, execution is self-contained (result stored in `result` field).
    ref_type: Mapped[str | None] = mapped_column(nullable=True, index=True)

    # Optional: UUID reference to the domain object
    ref_id: Mapped[str | None] = mapped_column(nullable=True, index=True)

    # Lifecycle status
    status: Mapped[AsyncToolExecutionStatus] = mapped_column(
        StringEnum(AsyncToolExecutionStatus),
        default=AsyncToolExecutionStatus.PENDING,
    )

    # Lightweight result data for rendering (optional)
    # Avoids needing to fetch the full domain object just to show status
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Error type if failed (timeout, internal_error, validation_error, not_found)
    error_type: Mapped[AsyncToolExecutionErrorType | None] = mapped_column(
        StringEnum(AsyncToolExecutionErrorType),
        nullable=True,
    )

    # Error message if failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
