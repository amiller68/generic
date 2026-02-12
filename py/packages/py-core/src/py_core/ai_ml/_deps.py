"""Agent dependencies for tool execution context."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AgentDeps:
    """Dependencies injected into agent tools via RunContext.

    These are available in every tool call as ctx.deps.

    Attributes:
        db: Async database session for queries
        logger: Structured logger with request context
        user_id: Current user's ID
        thread_id: Chat thread ID (for conversation continuity)
        completion_id: Current completion ID (for tracking tool calls)
    """

    db: AsyncSession
    logger: Any  # Logger type - use Any to avoid import
    user_id: str
    thread_id: str | None = None
    completion_id: str | None = None

    def with_completion(self, completion_id: str) -> "AgentDeps":
        """Return new AgentDeps with updated completion_id."""
        return AgentDeps(
            db=self.db,
            logger=self.logger,
            user_id=self.user_id,
            thread_id=self.thread_id,
            completion_id=completion_id,
        )
