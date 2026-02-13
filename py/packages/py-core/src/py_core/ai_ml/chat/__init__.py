"""
Chat module for persistent chat threads.

This module provides operations for managing chat threads and messages:
- Creating threads with an initial user message
- Sending messages to existing threads
- Getting and listing threads
- Cancelling running completions
- Events for real-time updates

Example:
    from py_core.ai_ml.chat import (
        create_thread,
        CreateThreadParams,
        CreateThreadContext,
    )
    from py_core.ai_ml.types import TextPart

    result = await create_thread(
        params=CreateThreadParams(
            user_id="user-123",
            parts=[TextPart(content="Hello!")],
            dispatch_task=my_dispatch_fn,
        ),
        ctx=CreateThreadContext(db=session, logger=logger),
    )
"""

# Exceptions
from .exceptions import (
    CompletionInProgress,
    CompletionNotFound,
    ThreadCancelled,
    ThreadNotFound,
)

# Async tool execution operations
from .async_tool_execution import (
    # Create
    CreateContext as CreateAsyncToolExecutionContext,
    CreateParams as CreateAsyncToolExecutionParams,
    CreateResult as CreateAsyncToolExecutionResult,
    create_async_tool_execution,
    # Complete
    CompleteContext as CompleteAsyncToolExecutionContext,
    CompleteParams as CompleteAsyncToolExecutionParams,
    CompleteResult as CompleteAsyncToolExecutionResult,
    complete_async_tool_execution,
    # Fail
    FailContext as FailAsyncToolExecutionContext,
    FailParams as FailAsyncToolExecutionParams,
    FailResult as FailAsyncToolExecutionResult,
    fail_async_tool_execution,
)

# Types
from .types import (
    AsyncToolExecution,
    Message,
    Thread,
    ThreadListItem,
)

# Engine
from .engine import (
    ChatEngine,
    EngineConfig,
    EngineContext,
    ThreadManager,
    get_cancel_key,
    serialize_message_history,
)

# Operations
from .cancel_thread import (
    CancelResult,
    Context as CancelContext,
    Params as CancelParams,
    request_cancel,
)
from .create_thread import (
    Context as CreateThreadContext,
    Params as CreateThreadParams,
    Result as CreateThreadResult,
    create_thread,
    DispatchCompletionTask,
)
from .get_thread import (
    Context as GetThreadContext,
    Params as GetThreadParams,
    get_thread,
)
from .list_threads import (
    Context as ListThreadsContext,
    Params as ListThreadsParams,
    Result as ListThreadsResult,
    list_threads,
)
from .send_message import (
    Context as SendMessageContext,
    Params as SendMessageParams,
    Result as SendMessageResult,
    send_message,
)

__all__ = [
    # Exceptions
    "ThreadNotFound",
    "CompletionNotFound",
    "CompletionInProgress",
    "ThreadCancelled",
    # Types
    "Message",
    "AsyncToolExecution",
    "Thread",
    "ThreadListItem",
    # Async tool execution operations
    "create_async_tool_execution",
    "CreateAsyncToolExecutionParams",
    "CreateAsyncToolExecutionContext",
    "CreateAsyncToolExecutionResult",
    "complete_async_tool_execution",
    "CompleteAsyncToolExecutionParams",
    "CompleteAsyncToolExecutionContext",
    "CompleteAsyncToolExecutionResult",
    "fail_async_tool_execution",
    "FailAsyncToolExecutionParams",
    "FailAsyncToolExecutionContext",
    "FailAsyncToolExecutionResult",
    # Engine
    "ChatEngine",
    "EngineConfig",
    "EngineContext",
    "ThreadManager",
    "get_cancel_key",
    "serialize_message_history",
    # Create thread
    "create_thread",
    "CreateThreadContext",
    "CreateThreadParams",
    "CreateThreadResult",
    "DispatchCompletionTask",
    # Send message
    "send_message",
    "SendMessageContext",
    "SendMessageParams",
    "SendMessageResult",
    # Get thread
    "get_thread",
    "GetThreadContext",
    "GetThreadParams",
    # List threads
    "list_threads",
    "ListThreadsContext",
    "ListThreadsParams",
    "ListThreadsResult",
    # Cancel thread
    "request_cancel",
    "CancelResult",
    "CancelContext",
    "CancelParams",
]
