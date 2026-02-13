"""Admin chat pages - admin-only AI assistant."""

import json

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from py_core.ai_ml.chat import (
    create_thread,
    CreateThreadParams,
    CreateThreadContext,
    send_message,
    SendMessageParams,
    SendMessageContext,
    get_thread,
    GetThreadParams,
    GetThreadContext,
    list_threads,
    ListThreadsParams,
    ListThreadsContext,
    request_cancel,
    CancelParams,
    CancelContext,
)
from py_core.database.models.async_tool_execution import (
    AsyncToolExecution,
    AsyncToolExecutionStatus,
)
from py_core.ai_ml.chat.exceptions import ThreadNotFound
from py_core.ai_ml.types import TextPart
from py_core.database.models import User
from py_core.observability import Logger

from src.server.deps import async_db, logger, redis, require_admin_user
from src.tasks.jobs.complete_thread import complete_thread_task
from src.server.templates import templates

router = APIRouter()


async def dispatch_completion(user_id: str, completion_id: str) -> None:
    """Dispatch the completion task to the worker."""
    await complete_thread_task.kiq(user_id=user_id, completion_id=completion_id)


@router.get("", response_class=HTMLResponse)
async def chat_index(
    request: Request,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Show chat interface with thread list."""
    result = await list_threads(
        params=ListThreadsParams(user_id=str(user.id), limit=20),
        ctx=ListThreadsContext(db=db, logger=log),
    )

    return templates.TemplateResponse(
        "pages/admin/chat/index.html",
        {
            "request": request,
            "user": user,
            "threads": result.threads,
        },
    )


@router.post("/new")
async def new_thread(
    request: Request,
    message: str = Form(...),
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> RedirectResponse:
    """Create a new thread with initial message."""
    result = await create_thread(
        params=CreateThreadParams(
            user_id=str(user.id),
            parts=[TextPart(content=message)],
            dispatch_task=dispatch_completion,
        ),
        ctx=CreateThreadContext(db=db, logger=log),
    )

    # Redirect to the new thread page
    return RedirectResponse(
        url=f"/_admin/chat/{result.thread_id}?completion_id={result.completion_id}",
        status_code=303,
    )


@router.get("/{thread_id}", response_class=HTMLResponse)
async def view_thread(
    request: Request,
    thread_id: str,
    completion_id: str | None = None,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """View an existing thread."""
    try:
        thread = await get_thread(
            params=GetThreadParams(user_id=str(user.id), thread_id=thread_id),
            ctx=GetThreadContext(db=db, logger=log),
        )
    except ThreadNotFound:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Fetch async tool executions for this thread (keyed by id for template lookup)
    result = await db.execute(
        select(AsyncToolExecution).where(AsyncToolExecution.thread_id == thread_id)
    )
    async_tools = {str(t.id): t for t in result.scalars().all()}

    # Parse tool result JSON strings for template access
    # (ToolResultPart.result is a JSON string, not a dict)
    for message in thread.messages:
        for part in message.parts:
            # Handle both dict and Pydantic model parts
            if isinstance(part, dict):
                result = part.get("result")
                if isinstance(result, str):
                    try:
                        part["_parsed_result"] = json.loads(result)
                    except json.JSONDecodeError:
                        part["_parsed_result"] = {}
                else:
                    part["_parsed_result"] = None
            elif hasattr(part, "result") and isinstance(part.result, str):
                try:
                    part._parsed_result = json.loads(part.result)
                except json.JSONDecodeError:
                    part._parsed_result = {}
            else:
                # For Pydantic models without result field
                if hasattr(part, "__dict__"):
                    part._parsed_result = None

    return templates.TemplateResponse(
        "pages/admin/chat/thread.html",
        {
            "request": request,
            "user": user,
            "thread": thread,
            "async_tools": async_tools,
            "completion_id": completion_id,
        },
    )


@router.post("/{thread_id}/send")
async def send_to_thread(
    request: Request,
    thread_id: str,
    message: str = Form(...),
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> RedirectResponse:
    """Send a message to an existing thread."""
    result = await send_message(
        params=SendMessageParams(
            user_id=str(user.id),
            thread_id=thread_id,
            parts=[TextPart(content=message)],
            dispatch_task=dispatch_completion,
        ),
        ctx=SendMessageContext(db=db, logger=log),
    )

    # Redirect to thread page with completion_id for SSE streaming
    return RedirectResponse(
        url=f"/_admin/chat/{thread_id}?completion_id={result.completion_id}",
        status_code=303,
    )


@router.get("/{thread_id}/debug")
async def debug_cancel(
    request: Request,
    thread_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    redis_client: Redis = Depends(redis),
    log: Logger = Depends(logger),
) -> JSONResponse:
    """Debug endpoint to trace cancel flow."""
    from py_core.database.models.completion import Completion, CompletionStatus
    from py_core.database.models.thread import Thread
    from py_core.ai_ml.chat.engine import get_cancel_key

    # Find active completion
    result = await db.execute(
        select(Thread, Completion)
        .outerjoin(
            Completion,
            (Completion.thread_id == Thread.id)
            & Completion.status.in_(
                [CompletionStatus.PENDING.value, CompletionStatus.PROCESSING.value]
            ),
        )
        .where(
            Thread.id == thread_id,
            Thread.user_id == str(user.id),
        )
    )
    row = result.one_or_none()

    if not row:
        return JSONResponse({"error": "Thread not found"})

    thread, completion = row

    if not completion:
        # Check for most recent completion
        recent = await db.execute(
            select(Completion)
            .where(Completion.thread_id == thread_id)
            .order_by(Completion.created_at.desc())
            .limit(1)
        )
        recent_completion = recent.scalar_one_or_none()
        return JSONResponse(
            {
                "thread_id": thread_id,
                "active_completion": None,
                "recent_completion": (
                    {
                        "id": recent_completion.id if recent_completion else None,
                        "status": (
                            recent_completion.status if recent_completion else None
                        ),
                    }
                    if recent_completion
                    else None
                ),
            }
        )

    # Check Redis key
    cancel_key = get_cancel_key(completion.id)
    key_exists = await redis_client.exists(cancel_key)

    # Try setting and reading back
    test_key = f"test:cancel:{completion.id}"
    await redis_client.set(test_key, "test", ex=10)
    test_read = await redis_client.get(test_key)
    await redis_client.delete(test_key)

    # Check if worker set its test key
    worker_test_key = f"task_test:{completion.id}"
    worker_test = await redis_client.get(worker_test_key)

    return JSONResponse(
        {
            "thread_id": thread_id,
            "completion_id": completion.id,
            "completion_status": completion.status,
            "cancel_key": cancel_key,
            "cancel_key_exists": bool(key_exists),
            "redis_test_web": test_read.decode() if test_read else None,
            "redis_test_worker": worker_test.decode() if worker_test else None,
        }
    )


@router.get("/{thread_id}/status")
async def completion_status(
    request: Request,
    thread_id: str,
    completion_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
) -> JSONResponse:
    """Check completion status for polling fallback."""
    from py_core.database.models.completion import Completion

    result = await db.execute(select(Completion).where(Completion.id == completion_id))
    completion = result.scalar_one_or_none()

    if not completion:
        return JSONResponse({"status": "not_found"})

    return JSONResponse({"status": completion.status})


@router.get("/{thread_id}/async-tools")
async def async_tools_status(
    request: Request,
    thread_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
) -> JSONResponse:
    """Check for pending async tool executions."""

    result = await db.execute(
        select(AsyncToolExecution)
        .where(
            AsyncToolExecution.thread_id == thread_id,
            AsyncToolExecution.status == AsyncToolExecutionStatus.PENDING,
        )
        .order_by(AsyncToolExecution.created_at.desc())
    )
    pending_tools = result.scalars().all()

    return JSONResponse(
        {
            "pending_count": len(pending_tools),
            "pending": [
                {"id": t.id, "name": t.name, "created_at": t.created_at.isoformat()}
                for t in pending_tools
            ],
        }
    )


@router.post("/{thread_id}/cancel")
async def cancel_completion(
    request: Request,
    thread_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    redis_client: Redis = Depends(redis),
    log: Logger = Depends(logger),
) -> RedirectResponse:
    """Cancel a running completion."""
    result = await request_cancel(
        params=CancelParams(thread_id=thread_id, user_id=str(user.id)),
        ctx=CancelContext(db=db, redis=redis_client),
    )

    if result.cancelled:
        log.info(f"Requested thread cancellation: thread_id={thread_id}")
    else:
        log.info(
            f"Thread cancellation skipped: thread_id={thread_id}, reason={result.message}"
        )

    # Redirect back to thread without completion_id to stop SSE
    return RedirectResponse(
        url=f"/_admin/chat/{thread_id}",
        status_code=303,
    )
