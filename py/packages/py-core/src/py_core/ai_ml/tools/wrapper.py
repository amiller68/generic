"""Tool wrapper decorator for exception handling.

This decorator wraps tool functions to:
1. Catch unhandled exceptions and return FailedResult
2. Convert ToolResultBase to JSON string for pydantic_ai
3. Log errors with traceback
"""

import functools
import traceback
from typing import Any, Callable, TypeVar

from py_core.ai_ml.types import TextPart

from ._types.result import ToolResultBase, FailedResult

F = TypeVar("F", bound=Callable[..., Any])


def tool(func: F) -> F:
    """Decorator for tool functions that handles exceptions.

    This decorator wraps async tool functions to:
    1. Catch any unhandled exceptions
    2. Convert them to FailedResult with unhandled_exception code
    3. Return JSON string for pydantic_ai compatibility
    4. Log errors via ctx.deps.logger

    Example:
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

    Args:
        func: Async tool function returning ToolResultBase

    Returns:
        Wrapped function that handles exceptions
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            result = await func(*args, **kwargs)

            if isinstance(result, ToolResultBase):
                return result.model_dump_json()

            # If not a ToolResultBase, just return as string
            return str(result)

        except Exception as e:
            # Try to get logger from context
            ctx = args[0] if args else None
            if ctx and hasattr(ctx, "deps") and hasattr(ctx.deps, "logger"):
                ctx.deps.logger.error(
                    f"Tool {func.__name__} failed: {e}\n{traceback.format_exc()}"
                )

            # Return failed result
            failed_result = FailedResult(
                code="unhandled_exception",
                message=f"Tool failed: {type(e).__name__}",
                content_parts=[
                    TextPart(content=f"Error: Tool {func.__name__} failed unexpectedly")
                ],
                details={
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                },
            )
            return failed_result.model_dump_json()

    return wrapper  # type: ignore
