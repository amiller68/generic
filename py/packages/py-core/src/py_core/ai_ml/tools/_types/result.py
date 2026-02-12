"""Tool result types for LLM tool responses.

This module defines a hierarchy of result types that tools can return.
Each result type has:
- status: Discriminator for the result type
- message: Short UI description (NOT sent to LLM)
- content_parts: Explicit content for LLM context

The separation of message and content_parts allows:
- UI to show user-friendly messages
- LLM to receive precise, engineered content
"""

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from py_core.ai_ml.types import ContentPart
from py_core.database.utils import utcnow

# Status discriminator
Status = Literal["pending", "completed", "error", "failed"]

# Error codes for known, handled errors
ErrorCode = Literal[
    "validation_error",
    "rate_limit",
    "not_found",
    "permission_denied",
]

# Failed codes for system failures
FailedCode = Literal[
    "internal_error",
    "timeout",
    "unhandled_exception",
]


class ToolResultBase(BaseModel):
    """Base class for all tool results.

    All tool results share these fields:
    - status: Discriminator for polymorphic handling
    - message: Short description for UI (not sent to LLM)
    - content_parts: Explicit content for LLM context
    - timestamp: When the result was created
    """

    status: Status
    message: str = Field(description="Short UI description (NOT for LLM)")
    content_parts: list[ContentPart] = Field(description="Explicit LLM representation")
    timestamp: datetime = Field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolResultBase":
        """Create from dictionary."""
        return cls.model_validate(data)


T = TypeVar("T", bound=BaseModel)


class CompletedResult(ToolResultBase, Generic[T]):
    """Sync tool completed successfully with typed payload.

    Use this for tools that complete immediately and return data.

    Attributes:
        data: Typed payload with result data (Pydantic model)
    """

    status: Literal["completed"] = "completed"
    data: T


class PendingResult(ToolResultBase):
    """Async tool dispatched to background.

    Use this for tools that start a background task and return immediately.
    The client should poll or subscribe for completion.

    Attributes:
        ref_type: Type of async operation (e.g., "search", "analysis")
        ref_id: ID of the domain object being processed
    """

    status: Literal["pending"] = "pending"
    ref_type: str | None = None
    ref_id: str | None = None


class ErrorResult(ToolResultBase):
    """Known, handled error (validation, rate limit, etc.).

    Use this for errors the LLM can learn from and potentially retry
    with different inputs.

    Attributes:
        code: Categorized error code
        details: Additional error context
    """

    status: Literal["error"] = "error"
    code: ErrorCode
    details: dict[str, Any] | None = None


class FailedResult(ToolResultBase):
    """System failure (crash, timeout, unhandled exception).

    Use this for unexpected failures. The LLM should not retry
    the same operation immediately.

    Attributes:
        code: Categorized failure code
        details: Additional failure context
    """

    status: Literal["failed"] = "failed"
    code: FailedCode
    details: dict[str, Any] | None = None
