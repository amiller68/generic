"""
ChatEngine: Executes chat completions with streaming.

Handles the complete lifecycle:
- Completion loading and status management
- LLM streaming with cancellation
- Message persistence
- Event publishing
- Error handling and cleanup
- Usage metrics tracking
"""

import json
import time
from dataclasses import dataclass, field

from pydantic_ai.messages import (
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
)
from pydantic_ai.messages import (
    TextPart as PydanticTextPart,
)
from pydantic_ai.messages import (
    ToolCallPart as PydanticToolCallPart,
)
from pydantic_ai.messages import (
    ToolReturnPart as PydanticToolReturnPart,
)
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.ai_ml import AgentConfig, AgentDeps, AgentSpec, build_agent
from py_core.ai_ml.chat.exceptions import CompletionNotFound, ThreadCancelled
from py_core.ai_ml.types.llm import (
    ContentPart,
    TextPart,
    ToolCallPart,
    ToolResultPart,
)
from py_core.database.models.completion import (
    Completion,
    CompletionErrorType,
    CompletionStatus,
)
from py_core.database.models.thread import MessageRole
from py_core.database.utils import utcnow
from py_core.events import (
    EventPublisher,
    ThreadCancelledEvent,
    ThreadFailedEvent,
    ThreadStreamEvent,
)
from py_core.observability import Logger

from .thread_manager import ThreadManager


def get_cancel_key(completion_id: str) -> str:
    """Redis key for cancellation signal."""
    return f"completion:cancel:{completion_id}"


@dataclass
class EngineConfig:
    """Configuration for the chat engine."""

    agent_spec: AgentSpec


@dataclass
class EngineContext:
    """Runtime dependencies for the engine."""

    db: AsyncSession
    logger: Logger
    events: EventPublisher
    redis: Redis
    user_id: str
    completion_id: str


@dataclass
class ChatEngine:
    """
    Executes chat completions with streaming.

    Handles the complete lifecycle:
    - Completion loading and status management
    - LLM streaming with cancellation
    - Message persistence
    - Event publishing
    - Error handling and cleanup
    - Usage metrics tracking
    """

    config: EngineConfig
    ctx: EngineContext
    _thread: ThreadManager | None = field(default=None, init=False)
    _completion: Completion | None = field(default=None, init=False)
    _partial_response: str = field(default="", init=False)
    _response_parts: list[ContentPart] = field(default_factory=list, init=False)
    _start_time: float = field(default=0.0, init=False)
    _input_tokens: int = field(default=0, init=False)
    _output_tokens: int = field(default=0, init=False)

    async def run(self) -> dict:
        """
        Run a completion on the thread.

        1. Load completion and thread
        2. Set status to PROCESSING
        3. Stream LLM response
        4. Save assistant message
        5. Set status to COMPLETED with metrics
        6. Publish done event

        Returns:
            Dict with thread_id, completion_id, message_id, response

        Raises:
            CompletionNotFound: If completion doesn't exist
            Exception: Any other error during processing
        """
        try:
            # Load completion
            completion = await self._load_completion()
            self._completion = completion
            thread_id = completion.thread_id

            # Load thread
            self._thread = await ThreadManager.load(
                self.ctx.db, thread_id, self.ctx.user_id
            )

            if not self._thread.prompt:
                raise ValueError("No user message to process")

            # Set status to PROCESSING
            completion.status = CompletionStatus.PROCESSING
            completion.started_at = utcnow()
            self._start_time = time.time()
            await self.ctx.db.flush()

            self.ctx.logger.info(
                f"Starting chat completion: thread_id={thread_id}, "
                f"completion_id={self.ctx.completion_id}"
            )

            # Stream completion - returns parts including tool calls
            self._response_parts = await self._stream_completion()

            # Extract text for response string
            self._partial_response = "".join(
                p.content for p in self._response_parts if isinstance(p, TextPart)
            )

            # Save response with all parts (text + tool calls + tool results)
            message = await self._thread.append_message_with_parts(
                self.ctx.db,
                MessageRole.assistant,
                self._response_parts,
                completion_id=self.ctx.completion_id,
            )

            # Update completion with success
            await self._complete_success()

            # Commit all changes
            await self.ctx.db.commit()

            # Publish done event
            await self._publish_done()

            self.ctx.logger.info(f"Chat completed: thread_id={thread_id}")

            return {
                "thread_id": thread_id,
                "completion_id": self.ctx.completion_id,
                "message_id": message.id,
                "response": self._partial_response,
            }

        except ThreadCancelled:
            await self._handle_cancellation()
            return {
                "thread_id": (
                    self._completion.thread_id if self._completion else "unknown"
                ),
                "completion_id": self.ctx.completion_id,
                "cancelled": True,
            }

        except Exception as e:
            await self._handle_error(e)
            raise

    async def _load_completion(self) -> Completion:
        """Load the completion record."""
        result = await self.ctx.db.execute(
            select(Completion).where(Completion.id == self.ctx.completion_id)
        )
        completion = result.scalar_one_or_none()
        if not completion:
            raise CompletionNotFound(f"Completion {self.ctx.completion_id} not found")
        return completion

    async def _complete_success(self) -> None:
        """Update completion record with success status and metrics."""
        if not self._completion:
            return

        self._completion.status = CompletionStatus.COMPLETED
        self._completion.response = self._partial_response
        self._completion.completed_at = utcnow()
        self._completion.latency_ms = int((time.time() - self._start_time) * 1000)
        self._completion.input_tokens = self._input_tokens
        self._completion.output_tokens = self._output_tokens

    async def _stream_completion(self) -> list[ContentPart]:
        """
        Stream LLM response with tool call support, checking for cancellation.

        Uses agent.iter() to properly handle tool calls - the agent will:
        1. Stream model responses (text deltas)
        2. Execute tool calls when the model requests them
        3. Continue with follow-up model responses
        4. Repeat until the agent reaches a final text output

        Returns:
            List of ContentPart (text, tool calls, tool results)

        Raises:
            ThreadCancelled: If user requested cancellation
        """
        if not self._thread:
            raise RuntimeError("Thread not loaded")
        if not self._completion:
            raise RuntimeError("Completion not loaded")

        config = AgentConfig()
        agent = build_agent(self.config.agent_spec, config)
        deps = AgentDeps(
            db=self.ctx.db,
            logger=self.ctx.logger,
            user_id=self.ctx.user_id,
            thread_id=self._completion.thread_id,
            completion_id=self.ctx.completion_id,
        )

        parts: list[ContentPart] = []
        current_text = ""
        cancel_key = get_cancel_key(self.ctx.completion_id)

        # Use agent.iter() for proper tool call handling
        async with agent.iter(
            self._thread.prompt,
            deps=deps,
            message_history=self._thread.message_history,
        ) as agent_run:
            async for node in agent_run:
                # Check for cancellation before processing each node
                if await self.ctx.redis.exists(cancel_key):
                    await self.ctx.redis.delete(cancel_key)
                    # Save partial text if any
                    if current_text:
                        parts.append(TextPart(content=current_text))
                    self._response_parts = parts
                    raise ThreadCancelled()

                # Handle model request nodes - these contain the streamed response
                if agent.is_model_request_node(node):
                    # Track text parts by index to handle out-of-order events
                    text_parts_by_index: dict[int, str] = {}

                    # Stream text from this model request
                    async with node.stream(agent_run.ctx) as request_stream:
                        async for event in request_stream:
                            # Check for cancellation during streaming
                            if await self.ctx.redis.exists(cancel_key):
                                await self.ctx.redis.delete(cancel_key)
                                # Collect text from all indices
                                for idx in sorted(text_parts_by_index.keys()):
                                    text = text_parts_by_index[idx]
                                    if text:
                                        current_text += text
                                if current_text:
                                    parts.append(TextPart(content=current_text))
                                    current_text = ""
                                self._response_parts = parts
                                raise ThreadCancelled()

                            if isinstance(event, PartStartEvent):
                                if isinstance(event.part, PydanticTextPart):
                                    initial_content = event.part.content
                                    text_parts_by_index[event.index] = initial_content
                                    if initial_content:
                                        await self.ctx.events.publish(
                                            self.ctx.user_id,
                                            ThreadStreamEvent(
                                                completion_id=self.ctx.completion_id,
                                                chunk=initial_content,
                                                done=False,
                                            ),
                                        )

                            elif isinstance(event, PartDeltaEvent):
                                if isinstance(event.delta, TextPartDelta):
                                    chunk = event.delta.content_delta
                                    if chunk:
                                        if event.index not in text_parts_by_index:
                                            text_parts_by_index[event.index] = ""
                                        text_parts_by_index[event.index] += chunk
                                        await self.ctx.events.publish(
                                            self.ctx.user_id,
                                            ThreadStreamEvent(
                                                completion_id=self.ctx.completion_id,
                                                chunk=chunk,
                                                done=False,
                                            ),
                                        )

                    for idx in sorted(text_parts_by_index.keys()):
                        text = text_parts_by_index[idx]
                        if text:
                            current_text += text

            # Get usage from the completed run
            if agent_run.result:
                usage = agent_run.result.usage()
                self._input_tokens = usage.request_tokens or 0
                self._output_tokens = usage.response_tokens or 0

                # Extract all parts from new_messages() in the correct order
                for msg in agent_run.result.new_messages():
                    for part in msg.parts:
                        if isinstance(part, PydanticTextPart):
                            parts.append(TextPart(content=part.content))
                        elif isinstance(part, PydanticToolCallPart):
                            args: dict = {}
                            if hasattr(part, "args_as_dict"):
                                args = part.args_as_dict()
                            elif part.args:
                                try:
                                    args = (
                                        json.loads(part.args)
                                        if isinstance(part.args, str)
                                        else dict(part.args)
                                    )
                                except (json.JSONDecodeError, TypeError):
                                    args = {"raw": str(part.args)}
                            parts.append(
                                ToolCallPart(
                                    call_id=part.tool_call_id,
                                    tool_name=part.tool_name,
                                    arguments=args,
                                )
                            )
                        elif isinstance(part, PydanticToolReturnPart):
                            parts.append(
                                ToolResultPart(
                                    call_id=part.tool_call_id,
                                    tool_name=part.tool_name,
                                    result=str(part.content),
                                )
                            )

        return parts

    async def _publish_done(self) -> None:
        """Publish stream completion event."""
        await self.ctx.events.publish(
            self.ctx.user_id,
            ThreadStreamEvent(
                completion_id=self.ctx.completion_id,
                chunk="",
                done=True,
            ),
        )

    async def _handle_cancellation(self) -> None:
        """Handle user cancellation - save partial, update status, commit, publish."""
        thread_id = self._completion.thread_id if self._completion else "unknown"
        self.ctx.logger.info(f"Thread cancelled: thread_id={thread_id}")

        if self._response_parts and self._thread:
            parts_to_save = list(self._response_parts)
            for i in range(len(parts_to_save) - 1, -1, -1):
                if isinstance(parts_to_save[i], TextPart):
                    parts_to_save[i] = TextPart(
                        content=parts_to_save[i].content + " [stopped]"
                    )
                    break
            else:
                parts_to_save.append(TextPart(content="[stopped]"))

            await self._thread.append_message_with_parts(
                self.ctx.db,
                MessageRole.assistant,
                parts_to_save,
                completion_id=self.ctx.completion_id,
            )

            self._partial_response = "".join(
                p.content for p in parts_to_save if isinstance(p, TextPart)
            )

        if self._completion:
            self._completion.status = CompletionStatus.CANCELLED
            self._completion.response = self._partial_response or None
            self._completion.completed_at = utcnow()
            if self._start_time:
                self._completion.latency_ms = int(
                    (time.time() - self._start_time) * 1000
                )

        await self.ctx.db.commit()

        await self.ctx.events.publish(
            self.ctx.user_id,
            ThreadCancelledEvent(completion_id=self.ctx.completion_id),
        )

    async def _handle_error(self, error: Exception) -> None:
        """Handle errors - update status, commit, publish failure."""
        import traceback

        import anthropic

        thread_id = self._completion.thread_id if self._completion else "unknown"
        self.ctx.logger.error(f"Thread failed: thread_id={thread_id}, error={error}")

        error_type = self._classify_error(error)
        error_message = str(error)
        error_details = {
            "exception_type": type(error).__name__,
            "exception_module": type(error).__module__,
            "traceback": traceback.format_exc(),
        }

        if isinstance(error, anthropic.APIError):
            if hasattr(error, "request_id") and error.request_id:
                error_details["request_id"] = error.request_id

        if self._completion:
            self._completion.status = CompletionStatus.FAILED
            self._completion.error_type = error_type
            self._completion.error_message = error_message
            self._completion.error_details = error_details
            self._completion.completed_at = utcnow()
            if self._start_time:
                self._completion.latency_ms = int(
                    (time.time() - self._start_time) * 1000
                )

        await self.ctx.db.commit()

        await self.ctx.events.publish(
            self.ctx.user_id,
            ThreadFailedEvent(
                completion_id=self.ctx.completion_id,
                error_type=error_type.value,
                error=error_message,
            ),
        )

    def _classify_error(self, error: Exception) -> CompletionErrorType:
        """Classify an exception into a CompletionErrorType."""
        import asyncio

        import anthropic
        import httpcore

        if isinstance(
            error,
            (
                asyncio.TimeoutError,
                httpcore.TimeoutException,
                anthropic.APITimeoutError,
            ),
        ):
            return CompletionErrorType.TIMEOUT

        if isinstance(error, anthropic.RateLimitError):
            return CompletionErrorType.OVERLOADED
        if isinstance(error, anthropic.InternalServerError):
            return CompletionErrorType.OVERLOADED

        if isinstance(
            error,
            (
                anthropic.BadRequestError,
                anthropic.UnprocessableEntityError,
                anthropic.APIResponseValidationError,
            ),
        ):
            return CompletionErrorType.API

        return CompletionErrorType.INTERNAL
