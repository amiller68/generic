"""Factory functions for creating tool results.

These functions provide a clean API for tools to return results
without needing to import and construct result classes directly.

Example:
    from py_core.ai_ml.tools import completed, validation_error
    from py_core.ai_ml.types import TextPart

    # Success
    return completed(
        data=MyPayload(items=items),
        message="Found 5 items",
        content_parts=[TextPart(content="Found 5 items")],
    )

    # Validation error
    return validation_error(
        message="Invalid input",
        content_parts=[TextPart(content="Error: Invalid input")],
        details={"field": "query", "reason": "too short"},
    )
"""

from typing import Any, TypeVar

from pydantic import BaseModel

from py_core.ai_ml.types import ContentPart

from ._types.result import (
    CompletedResult,
    PendingResult,
    ErrorResult,
    FailedResult,
)

T = TypeVar("T", bound=BaseModel)


def completed(
    data: T,
    message: str,
    content_parts: list[ContentPart],
) -> CompletedResult[T]:
    """Create a completed result with typed payload.

    Args:
        data: Typed payload (Pydantic model)
        message: Short UI description
        content_parts: Explicit LLM content

    Returns:
        CompletedResult with the payload
    """
    return CompletedResult(
        data=data,
        message=message,
        content_parts=content_parts,
    )


def pending(
    message: str,
    content_parts: list[ContentPart],
    ref_type: str | None = None,
    ref_id: str | None = None,
) -> PendingResult:
    """Create a pending result for async operations.

    Args:
        message: Short UI description
        content_parts: Explicit LLM content
        ref_type: Type of async operation
        ref_id: ID of domain object being processed

    Returns:
        PendingResult indicating background task started
    """
    return PendingResult(
        message=message,
        content_parts=content_parts,
        ref_type=ref_type,
        ref_id=ref_id,
    )


def validation_error(
    message: str,
    content_parts: list[ContentPart],
    details: dict[str, Any] | None = None,
) -> ErrorResult:
    """Create a validation error result.

    Use for invalid input the LLM can learn from and retry.

    Args:
        message: Short UI description
        content_parts: Explicit LLM content
        details: Additional error context

    Returns:
        ErrorResult with validation_error code
    """
    return ErrorResult(
        code="validation_error",
        message=message,
        content_parts=content_parts,
        details=details,
    )


def rate_limit_error(
    message: str,
    content_parts: list[ContentPart],
    details: dict[str, Any] | None = None,
) -> ErrorResult:
    """Create a rate limit error result.

    Args:
        message: Short UI description
        content_parts: Explicit LLM content
        details: Additional error context (e.g., retry_after)

    Returns:
        ErrorResult with rate_limit code
    """
    return ErrorResult(
        code="rate_limit",
        message=message,
        content_parts=content_parts,
        details=details,
    )


def not_found_error(
    message: str,
    content_parts: list[ContentPart],
    details: dict[str, Any] | None = None,
) -> ErrorResult:
    """Create a not found error result.

    Args:
        message: Short UI description
        content_parts: Explicit LLM content
        details: Additional error context

    Returns:
        ErrorResult with not_found code
    """
    return ErrorResult(
        code="not_found",
        message=message,
        content_parts=content_parts,
        details=details,
    )


def permission_error(
    message: str,
    content_parts: list[ContentPart],
    details: dict[str, Any] | None = None,
) -> ErrorResult:
    """Create a permission denied error result.

    Args:
        message: Short UI description
        content_parts: Explicit LLM content
        details: Additional error context

    Returns:
        ErrorResult with permission_denied code
    """
    return ErrorResult(
        code="permission_denied",
        message=message,
        content_parts=content_parts,
        details=details,
    )


def failed(
    code: str,
    message: str,
    content_parts: list[ContentPart],
    details: dict[str, Any] | None = None,
) -> FailedResult:
    """Create a generic failed result.

    Args:
        code: Failure code (internal_error, timeout, unhandled_exception)
        message: Short UI description
        content_parts: Explicit LLM content
        details: Additional failure context

    Returns:
        FailedResult with the specified code
    """
    return FailedResult(
        code=code,  # type: ignore
        message=message,
        content_parts=content_parts,
        details=details,
    )


def internal_error(
    message: str,
    content_parts: list[ContentPart],
    details: dict[str, Any] | None = None,
) -> FailedResult:
    """Create an internal error result.

    Use for unexpected system failures.

    Args:
        message: Short UI description
        content_parts: Explicit LLM content
        details: Additional failure context

    Returns:
        FailedResult with internal_error code
    """
    return FailedResult(
        code="internal_error",
        message=message,
        content_parts=content_parts,
        details=details,
    )


def timeout_error(
    message: str,
    content_parts: list[ContentPart],
    details: dict[str, Any] | None = None,
) -> FailedResult:
    """Create a timeout error result.

    Use when an operation times out.

    Args:
        message: Short UI description
        content_parts: Explicit LLM content
        details: Additional failure context

    Returns:
        FailedResult with timeout code
    """
    return FailedResult(
        code="timeout",
        message=message,
        content_parts=content_parts,
        details=details,
    )
