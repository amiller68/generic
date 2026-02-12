"""Chat SSE events for real-time thread updates.

Provides SSE streaming for:
- Thread stream events (AI response chunks)
- Thread completion/cancellation/failure events
- Async tool execution events

Event format for HTMX SSE:
    event: <event-name>
    data: <html-content>

Connect from HTMX with:
    <div hx-ext="sse"
         sse-connect="/_events/chat/{thread_id}?completion_id={completion_id}"
         sse-swap="message">
        <!-- Streaming content goes here -->
    </div>
"""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from redis.asyncio import Redis
from sse_starlette.sse import EventSourceResponse

from py_core.database.models import User
from py_core.observability import Logger

from src.server.deps import logger, redis, require_admin_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def chat_event_generator(
    request: Request,
    redis_client: Redis,
    user: User,
    thread_id: str,
    completion_id: str,
    log: Logger,
) -> AsyncGenerator[dict, None]:
    """
    Generate SSE events for chat thread updates.

    Subscribes to the user's personal Redis pub/sub channel and yields
    formatted SSE events for streaming AI responses.
    """
    pubsub = redis_client.pubsub()
    user_channel = f"events:user:{user.id}"
    await pubsub.subscribe(user_channel)

    # Track if we've received completion/cancel/fail
    stream_complete = False
    accumulated_text = ""

    # Send initial connection event
    yield {
        "event": "connected",
        "data": "Chat stream connected",
    }

    try:
        while not stream_complete:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Wait for message with timeout
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message and message["type"] == "message":
                try:
                    # Parse the EventEnvelope format
                    envelope = json.loads(message["data"])
                    event_type = envelope.get("type", "unknown")
                    payload = envelope.get("payload", {})

                    # Only process events for this completion
                    event_completion_id = payload.get("completion_id")
                    if event_completion_id != completion_id:
                        continue

                    log.debug(f"Chat event: {event_type}")

                    if event_type == "thread.stream":
                        # Streaming chunk - accumulate and send
                        chunk = payload.get("chunk", "")
                        accumulated_text += chunk
                        done = payload.get("done", False)

                        # Send just the text content - target replaces innerHTML
                        yield {
                            "event": "message",
                            "data": accumulated_text,
                        }

                        if done:
                            # Send completed event so client knows to refresh
                            yield {
                                "event": "completed",
                                "data": json.dumps(
                                    {
                                        "thread_id": thread_id,
                                        "completion_id": completion_id,
                                    }
                                ),
                            }
                            stream_complete = True

                    elif event_type == "thread.completed":
                        # Completion finished - refresh the full thread
                        yield {
                            "event": "completed",
                            "data": json.dumps(
                                {
                                    "thread_id": payload.get("thread_id"),
                                    "completion_id": completion_id,
                                }
                            ),
                        }
                        stream_complete = True

                    elif event_type == "thread.cancelled":
                        yield {
                            "event": "cancelled",
                            "data": "<span class='text-warning'>Cancelled</span>",
                        }
                        stream_complete = True

                    elif event_type == "thread.failed":
                        error = payload.get("error", "Unknown error")
                        yield {
                            "event": "failed",
                            "data": f"<span class='text-destructive'>Error: {error}</span>",
                        }
                        stream_complete = True

                    elif event_type == "async_tool.started":
                        # Async tool started - show pending indicator
                        tool_name = payload.get("tool_name", "tool")
                        yield {
                            "event": "tool-started",
                            "data": f"""
                            <div class="p-2 bg-muted rounded text-sm text-muted-foreground">
                                <span class="animate-pulse">Running {tool_name}...</span>
                            </div>
                            """,
                        }

                    elif event_type == "async_tool.completed":
                        # Async tool completed - will be shown in thread refresh
                        tool_name = payload.get("tool_name", "tool")
                        yield {
                            "event": "tool-completed",
                            "data": json.dumps(
                                {
                                    "tool_name": tool_name,
                                    "execution_id": payload.get("execution_id"),
                                }
                            ),
                        }

                    elif event_type == "async_tool.failed":
                        tool_name = payload.get("tool_name", "tool")
                        error = payload.get("error", "Unknown error")
                        yield {
                            "event": "tool-failed",
                            "data": f"""
                            <div class="p-2 bg-destructive/10 rounded text-sm text-destructive">
                                {tool_name} failed: {error}
                            </div>
                            """,
                        }

                except json.JSONDecodeError:
                    log.warn(f"Invalid JSON in chat event: {message['data']}")

            # Small delay to prevent busy loop
            await asyncio.sleep(0.1)

    finally:
        await pubsub.unsubscribe(user_channel)
        await pubsub.close()


@router.get("/{thread_id}")
async def chat_stream(
    request: Request,
    thread_id: str,
    completion_id: str,
    user: User = Depends(require_admin_user),
    redis_client: Redis = Depends(redis),
    log: Logger = Depends(logger),
) -> EventSourceResponse:
    """
    SSE endpoint for real-time chat streaming.

    Subscribes to the user's personal channel: events:user:{user_id}
    Filters events by completion_id to only show relevant updates.

    Connect from HTMX with:
        <div hx-ext="sse"
             sse-connect="/_events/chat/{thread_id}?completion_id={completion_id}"
             sse-swap="message">
            ...
        </div>

    Events emitted:
        - connected: Initial connection confirmation
        - message: Streaming message chunk (HTML)
        - completed: Completion finished successfully
        - cancelled: Completion was cancelled
        - failed: Completion failed with error
        - tool-started: Async tool started
        - tool-completed: Async tool finished
        - tool-failed: Async tool failed
    """
    return EventSourceResponse(
        chat_event_generator(
            request, redis_client, user, thread_id, completion_id, log
        ),
        ping=15,
    )
