"""
Completion model for tracking chat completion requests.

A Completion represents a single LLM completion lifecycle:
- Created when user sends a message
- Tracks status through PENDING -> PROCESSING -> COMPLETED/CANCELLED/FAILED
- Stores full message history for audit trail
- Tracks model and token usage
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from py_core.database.client import Base
from py_core.database.utils import utcnow

if TYPE_CHECKING:
    from .thread import Message, Thread


class CompletionStatus(str, Enum):
    """Status for completion lifecycle."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


CompletionStatusType = PgEnum(
    "pending",
    "processing",
    "completed",
    "cancelled",
    "failed",
    name="completion_status",
    create_type=True,
)


class CompletionErrorType(str, Enum):
    """Error type for failed completions."""

    API = "api"  # Bad request build, validation errors - bug on our part
    OVERLOADED = "overloaded"  # LLM provider overloaded, rate limited
    INTERNAL = "internal"  # Unexpected internal error
    TIMEOUT = "timeout"  # Request or completion timed out


CompletionErrorTypeEnum = PgEnum(
    "api",
    "overloaded",
    "internal",
    "timeout",
    name="completion_error_type",
    create_type=True,
)


class Completion(Base):
    """
    A single LLM completion request and its lifecycle.

    Provides full audit trail of inputs and outputs.

    ID format: UUID7
    """

    __tablename__ = "completions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid7()),
    )

    # Parent thread
    thread_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Denormalized user_id for efficient queries
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status lifecycle
    status: Mapped[str] = mapped_column(
        CompletionStatusType,
        nullable=False,
        default=CompletionStatus.PENDING.value,
    )

    # Input (snapshot at request time)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    message_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Output
    response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Error tracking with structured type, message, and details
    error_type: Mapped[str | None] = mapped_column(
        CompletionErrorTypeEnum,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Model/Usage tracking
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    thread: Mapped["Thread"] = relationship(
        "Thread",
        back_populates="completions",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="completion",
    )
