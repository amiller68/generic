"""
ThreadManager: Central lifecycle manager for chat threads.

The ThreadManager class is the single authority for:
- Building message history (pydantic_ai format)
- Updating thread state (adding messages)
- Creating and managing completions
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart as PydanticTextPart,
    ToolCallPart as PydanticToolCallPart,
    ToolReturnPart as PydanticToolReturnPart,
    UserPromptPart,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.ai_ml.chat.exceptions import CompletionInProgress, ThreadNotFound
from py_core.ai_ml.types.llm import (
    ContentPart,
    ContentPartList,
    TextPart,
    ToolCallPart,
    ToolResultPart,
    extract_text_content,
)
from py_core.database.models.completion import Completion, CompletionStatus
from py_core.database.models.thread import Message, MessageRole, Thread as ThreadModel
from py_core.database.models.async_tool_execution import AsyncToolExecution

if TYPE_CHECKING:
    pass


def _serialize_parts(parts: ContentPartList) -> list[dict]:
    """Serialize ContentPartList to raw JSONB format."""
    return parts.model_dump()


def serialize_message_history(history: list[ModelMessage]) -> list[dict]:
    """
    Serialize pydantic_ai message history using canonical format.

    Uses ModelMessagesTypeAdapter for round-trip serialization - the stored
    format can be deserialized back to pydantic_ai message objects.
    """
    return ModelMessagesTypeAdapter.dump_python(history, mode="json")


@dataclass
class ThreadManager:
    """
    Central lifecycle manager for chat threads.

    Owns:
    - Thread and message loading
    - Message history building (pydantic_ai format)
    - Thread state updates (adding messages)
    - Completion creation and lifecycle
    """

    thread: ThreadModel
    messages: list[Message]
    operations: list[AsyncToolExecution]  # Completed async tool executions
    message_history: list[ModelMessage]  # Pydantic AI format
    prompt: str  # Last user message to process

    # -------------------------------------------------------------------------
    # Class methods for thread creation and loading
    # -------------------------------------------------------------------------

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        user_id: str,
        parts: list[ContentPart],
    ) -> tuple["ThreadManager", Completion]:
        """
        Create a new thread with initial user message and pending completion.

        Args:
            db: Database session
            user_id: Owner's user ID
            parts: Content parts for initial message

        Returns:
            Tuple of (ThreadManager, Completion) - caller must commit and kick off task
        """
        # Create thread
        thread = ThreadModel(user_id=user_id)
        db.add(thread)
        await db.flush()

        # Create initial user message
        content_parts = ContentPartList(root=list(parts))
        message = Message(
            thread_id=thread.id,
            role=MessageRole.user,
            parts=_serialize_parts(content_parts),
        )
        db.add(message)
        await db.flush()

        # Extract prompt and create completion
        prompt = extract_text_content(content_parts.model_dump())
        completion = Completion(
            thread_id=thread.id,
            user_id=user_id,
            status=CompletionStatus.PENDING,
            prompt=prompt,
            message_history=[],  # Empty for first message
        )
        db.add(completion)
        await db.flush()

        return (
            cls(
                thread=thread,
                messages=[message],
                operations=[],  # New thread has no operations yet
                message_history=[],
                prompt=prompt,
            ),
            completion,
        )

    @classmethod
    async def load(
        cls,
        db: AsyncSession,
        thread_id: str,
        user_id: str,
    ) -> "ThreadManager":
        """
        Load a thread for completion execution (extracts last user message as prompt).

        Also loads completed async operations and injects their results into the
        prompt context so the agent can reference them.

        Args:
            db: Database session
            thread_id: ID of the thread to load
            user_id: User ID (for authorization)

        Returns:
            Loaded ThreadManager with formatted history, prompt, and operation context

        Raises:
            ThreadNotFound: If thread doesn't exist or wrong user
        """
        thread, messages = await cls._load_thread_and_messages(db, thread_id, user_id)

        # Load completed async tool executions for this thread
        ops_result = await db.execute(
            select(AsyncToolExecution)
            .where(AsyncToolExecution.thread_id == thread_id)
            .where(AsyncToolExecution.status.in_(["completed", "failed"]))
            .order_by(AsyncToolExecution.completed_at)
        )
        operations = list(ops_result.scalars().all())

        history, prompt = cls._build_history_with_prompt(messages)

        # Inject operation context into the prompt if there are completed operations
        if operations:
            context_parts = []
            for op in operations:
                if op.status == "completed" and op.result:
                    context_parts.append(f"## {op.name} (id: {op.ref_id})\n{op.result}")
                elif op.status == "failed" and op.error_message:
                    context_parts.append(
                        f"## {op.name} (id: {op.ref_id})\n**Status:** FAILED\n**Error:** {op.error_message}"
                    )

            if context_parts:
                context_text = "\n\n".join(context_parts)
                prompt = f"{context_text}\n\n---\n\nUser message: {prompt}"

        return cls(
            thread=thread,
            messages=messages,
            operations=operations,
            message_history=history,
            prompt=prompt,
        )

    @classmethod
    async def load_for_send(
        cls,
        db: AsyncSession,
        thread_id: str,
        user_id: str,
    ) -> "ThreadManager":
        """
        Load a thread for sending a new message (no prompt extraction).

        Args:
            db: Database session
            thread_id: ID of the thread to load
            user_id: User ID (for authorization)

        Returns:
            Loaded ThreadManager with messages

        Raises:
            ThreadNotFound: If thread doesn't exist or wrong user
        """
        thread, messages = await cls._load_thread_and_messages(db, thread_id, user_id)
        return cls(
            thread=thread,
            messages=messages,
            operations=[],  # Not needed for send, will be loaded on completion
            message_history=[],
            prompt="",
        )

    @classmethod
    async def _load_thread_and_messages(
        cls,
        db: AsyncSession,
        thread_id: str,
        user_id: str,
    ) -> tuple[ThreadModel, list[Message]]:
        """Load thread model and messages from database."""
        result = await db.execute(
            select(ThreadModel).where(
                ThreadModel.id == thread_id,
                ThreadModel.user_id == user_id,
            )
        )
        thread = result.scalar_one_or_none()
        if not thread:
            raise ThreadNotFound(f"Thread {thread_id} not found")

        messages_result = await db.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at)
        )
        messages = list(messages_result.scalars().all())
        return thread, messages

    # -------------------------------------------------------------------------
    # Instance methods for thread state management
    # -------------------------------------------------------------------------

    async def add_message_and_complete(
        self,
        db: AsyncSession,
        parts: list[ContentPart],
    ) -> tuple[Message, Completion]:
        """
        Add user message and create pending completion.

        Args:
            db: Database session
            parts: Content parts for the message

        Returns:
            Tuple of (Message, Completion) - caller must commit and kick off task

        Raises:
            CompletionInProgress: If thread already has an active completion
        """
        # Check no active completion
        active = await db.execute(
            select(Completion).where(
                Completion.thread_id == self.thread.id,
                Completion.status.in_(
                    [CompletionStatus.PENDING, CompletionStatus.PROCESSING]
                ),
            )
        )
        if active.scalar_one_or_none():
            raise CompletionInProgress(
                f"Thread {self.thread.id} has an active completion"
            )

        # Build full history from existing messages
        full_history = self._build_full_history()

        # Create user message
        content_parts = ContentPartList(root=list(parts))
        message = Message(
            thread_id=self.thread.id,
            role=MessageRole.user,
            parts=_serialize_parts(content_parts),
        )
        db.add(message)
        await db.flush()
        self.messages.append(message)

        # Create completion
        prompt = extract_text_content(content_parts.model_dump())
        completion = Completion(
            thread_id=self.thread.id,
            user_id=self.thread.user_id,
            status=CompletionStatus.PENDING,
            prompt=prompt,
            message_history=serialize_message_history(full_history),
        )
        db.add(completion)
        await db.flush()

        return message, completion

    async def append_message(
        self,
        db: AsyncSession,
        role: MessageRole,
        content: str,
        completion_id: str | None = None,
        suffix: str = "",
    ) -> Message:
        """
        Add a text-only message to the thread.

        Args:
            db: Database session
            role: Message role (user or assistant)
            content: Message content
            completion_id: Optional completion ID (for assistant messages)
            suffix: Optional suffix to append (e.g., " [stopped]")

        Returns:
            The created Message
        """
        parts = [TextPart(content=content + suffix)]
        return await self.append_message_with_parts(db, role, parts, completion_id)

    async def append_message_with_parts(
        self,
        db: AsyncSession,
        role: MessageRole,
        parts: list[ContentPart],
        completion_id: str | None = None,
    ) -> Message:
        """
        Add a message with structured parts to the thread.

        Supports text, tool calls, and tool results.

        Args:
            db: Database session
            role: Message role (user or assistant)
            parts: Content parts (TextPart, ToolCallPart, ToolResultPart)
            completion_id: Optional completion ID (for assistant messages)

        Returns:
            The created Message
        """
        content_parts = ContentPartList(root=list(parts))
        message = Message(
            thread_id=self.thread.id,
            role=role,
            parts=_serialize_parts(content_parts),
            completion_id=completion_id,
        )
        db.add(message)
        await db.flush()
        self.messages.append(message)
        return message

    # -------------------------------------------------------------------------
    # History building utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_history_with_prompt(
        messages: list[Message],
    ) -> tuple[list[ModelMessage], str]:
        """
        Convert DB messages to Pydantic AI format, extracting last user message as prompt.

        Returns:
            Tuple of (message_history, last_user_prompt)
        """
        if not messages:
            return [], ""

        history: list[ModelMessage] = []

        # Process all messages except the last one (which becomes the prompt)
        for msg in messages[:-1]:
            content = extract_text_content(msg.parts)
            if msg.role == MessageRole.user:
                history.append(ModelRequest(parts=[UserPromptPart(content=content)]))
            elif msg.role == MessageRole.assistant:
                history.append(ModelResponse(parts=[PydanticTextPart(content=content)]))

        # Return history and last user message as prompt
        last_msg = messages[-1]
        last_content = extract_text_content(last_msg.parts)
        return history, last_content if last_msg.role == MessageRole.user else ""

    def _build_full_history(self) -> list[ModelMessage]:
        """Build pydantic_ai history from ALL messages with full part details."""
        history: list[ModelMessage] = []
        for msg in self.messages:
            parts_list = ContentPartList.model_validate(msg.parts)
            pydantic_parts: list = []

            for part in parts_list:
                if isinstance(part, TextPart):
                    if msg.role == MessageRole.user:
                        pydantic_parts.append(UserPromptPart(content=part.content))
                    else:
                        pydantic_parts.append(PydanticTextPart(content=part.content))
                elif isinstance(part, ToolCallPart):
                    pydantic_parts.append(
                        PydanticToolCallPart(
                            tool_name=part.tool_name,
                            args=part.arguments,
                            tool_call_id=part.call_id,
                        )
                    )
                elif isinstance(part, ToolResultPart):
                    pydantic_parts.append(
                        PydanticToolReturnPart(
                            tool_name=part.tool_name,
                            content=part.result,
                            tool_call_id=part.call_id,
                        )
                    )

            if pydantic_parts:
                if msg.role == MessageRole.user:
                    history.append(ModelRequest(parts=pydantic_parts))
                elif msg.role == MessageRole.assistant:
                    history.append(ModelResponse(parts=pydantic_parts))

        return history
