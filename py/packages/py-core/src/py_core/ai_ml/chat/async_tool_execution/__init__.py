"""
Async tool execution operations.

Operations for creating and updating AsyncToolExecution records
that track async operations initiated from chat threads.

Each operation follows the library pattern:
- Params: Input parameters dataclass
- Context: Dependencies dataclass (db, logger)
- Result: Output dataclass
- Async function: (params, ctx) -> Result
"""

from .complete import (
    Context as CompleteContext,
    Params as CompleteParams,
    Result as CompleteResult,
    complete_async_tool_execution,
)
from .create import (
    Context as CreateContext,
    Params as CreateParams,
    Result as CreateResult,
    create_async_tool_execution,
)
from .fail import (
    Context as FailContext,
    Params as FailParams,
    Result as FailResult,
    fail_async_tool_execution,
)

__all__ = [
    # Create
    "create_async_tool_execution",
    "CreateParams",
    "CreateContext",
    "CreateResult",
    # Complete
    "complete_async_tool_execution",
    "CompleteParams",
    "CompleteContext",
    "CompleteResult",
    # Fail
    "fail_async_tool_execution",
    "FailParams",
    "FailContext",
    "FailResult",
]
