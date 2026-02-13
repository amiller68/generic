"""Tool framework for AI agents.

This module provides:
- Result types for tool returns (completed, pending, error, failed)
- Factory functions for creating results
- Tool wrapper decorator for exception handling
- Async tool lifecycle management

Example:
    from py_core.ai_ml.tools import tool, completed, pending, validation_error
    from py_core.ai_ml.types import TextPart

    @tool
    async def search_items(
        ctx: RunContext[AgentDeps],
        query: str,
    ) -> ToolResultBase:
        items = await search(query)
        return completed(
            data=SearchPayload(items=items),
            message=f"Found {len(items)} items",
            content_parts=[TextPart(content=f"Found {len(items)} items")],
        )
"""

from ._types.result import (
    ToolResultBase,
    CompletedResult,
    PendingResult,
    ErrorResult,
    FailedResult,
    Status,
    ErrorCode,
    FailedCode,
)
from ._types.payload import AsyncToolPayload, AsyncToolRefType
from .results import (
    completed,
    pending,
    validation_error,
    rate_limit_error,
    not_found_error,
    permission_error,
    failed,
    internal_error,
    timeout_error,
)
from .wrapper import tool
from .lifecycle import with_async_tool_lifecycle, LABEL_EXECUTION_ID

__all__ = [
    # Result types
    "ToolResultBase",
    "CompletedResult",
    "PendingResult",
    "ErrorResult",
    "FailedResult",
    "Status",
    "ErrorCode",
    "FailedCode",
    # Async tool payload
    "AsyncToolPayload",
    "AsyncToolRefType",
    # Factory functions
    "completed",
    "pending",
    "validation_error",
    "rate_limit_error",
    "not_found_error",
    "permission_error",
    "failed",
    "internal_error",
    "timeout_error",
    # Decorators
    "tool",
    "with_async_tool_lifecycle",
    "LABEL_EXECUTION_ID",
]
