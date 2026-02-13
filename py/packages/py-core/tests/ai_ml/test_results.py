"""Tests for tool result types and factory functions."""

from pydantic import BaseModel

from py_core.ai_ml.tools import (
    completed,
    pending,
    validation_error,
    not_found_error,
    internal_error,
    timeout_error,
    CompletedResult,
    PendingResult,
    ErrorResult,
    FailedResult,
)
from py_core.ai_ml.types import TextPart


class SamplePayload(BaseModel):
    """Sample payload for testing."""

    items: list[str]
    count: int


class TestCompletedResult:
    """Tests for completed results."""

    def test_completed_creates_result(self) -> None:
        """completed() creates CompletedResult with payload."""
        payload = SamplePayload(items=["a", "b"], count=2)
        result = completed(
            data=payload,
            message="Found 2 items",
            content_parts=[TextPart(content="Found 2 items")],
        )

        assert isinstance(result, CompletedResult)
        assert result.status == "completed"
        assert result.data.items == ["a", "b"]
        assert result.data.count == 2
        assert result.message == "Found 2 items"
        assert len(result.content_parts) == 1

    def test_completed_to_dict(self) -> None:
        """CompletedResult can be serialized to dict."""
        payload = SamplePayload(items=["a"], count=1)
        result = completed(
            data=payload,
            message="Found 1 item",
            content_parts=[TextPart(content="Found 1 item")],
        )

        data = result.to_dict()
        assert data["status"] == "completed"
        assert data["data"]["items"] == ["a"]
        assert data["data"]["count"] == 1

    def test_completed_to_json(self) -> None:
        """CompletedResult can be serialized to JSON."""
        payload = SamplePayload(items=["a"], count=1)
        result = completed(
            data=payload,
            message="Found 1 item",
            content_parts=[TextPart(content="Found 1 item")],
        )

        json_str = result.model_dump_json()
        assert '"status":"completed"' in json_str
        assert '"items":["a"]' in json_str


class TestPendingResult:
    """Tests for pending results."""

    def test_pending_creates_result(self) -> None:
        """pending() creates PendingResult."""
        result = pending(
            message="Search started",
            content_parts=[TextPart(content="Search in progress...")],
            ref_type="search",
            ref_id="search-123",
        )

        assert isinstance(result, PendingResult)
        assert result.status == "pending"
        assert result.ref_type == "search"
        assert result.ref_id == "search-123"

    def test_pending_without_refs(self) -> None:
        """pending() works without ref_type and ref_id."""
        result = pending(
            message="Processing",
            content_parts=[TextPart(content="Processing...")],
        )

        assert result.ref_type is None
        assert result.ref_id is None


class TestErrorResult:
    """Tests for error results."""

    def test_validation_error(self) -> None:
        """validation_error() creates ErrorResult with correct code."""
        result = validation_error(
            message="Invalid input",
            content_parts=[TextPart(content="Error: Invalid input")],
            details={"field": "query"},
        )

        assert isinstance(result, ErrorResult)
        assert result.status == "error"
        assert result.code == "validation_error"
        assert result.details == {"field": "query"}

    def test_not_found_error(self) -> None:
        """not_found_error() creates ErrorResult with not_found code."""
        result = not_found_error(
            message="Item not found",
            content_parts=[TextPart(content="Error: Item not found")],
        )

        assert result.code == "not_found"


class TestFailedResult:
    """Tests for failed results."""

    def test_internal_error(self) -> None:
        """internal_error() creates FailedResult."""
        result = internal_error(
            message="Unexpected error",
            content_parts=[TextPart(content="Error: Unexpected error")],
            details={"exception": "ValueError"},
        )

        assert isinstance(result, FailedResult)
        assert result.status == "failed"
        assert result.code == "internal_error"
        assert result.details == {"exception": "ValueError"}

    def test_timeout_error(self) -> None:
        """timeout_error() creates FailedResult with timeout code."""
        result = timeout_error(
            message="Operation timed out",
            content_parts=[TextPart(content="Error: Timeout")],
        )

        assert result.code == "timeout"
