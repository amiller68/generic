"""
Thread and Message models for persistent chat.

A Thread belongs to a user and contains Messages.
Messages are ordered and have a role (user or assistant).

Note: Message.parts is stored as raw JSONB. The chat engine
handles validation/parsing into ContentPartList.
This keeps the DB layer decoupled from chat types.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from py_core.database.client import Base
from py_core.database.utils import utcnow

if TYPE_CHECKING:
    from .completion import Completion


class MessageRole(str, Enum):
    """Message role types."""

    user = "user"
    assistant = "assistant"


MessageRoleType = PgEnum(MessageRole, name="message_role", create_type=True)


class Thread(Base):
    """
    A chat thread owned by a user.

    ID format: UUID7
    """

    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid7()),
    )

    # Owner
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional title for display
    title: Mapped[str | None] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="thread",
        order_by="Message.created_at",
        cascade="all, delete-orphan",
    )
    completions: Mapped[list["Completion"]] = relationship(
        "Completion",
        back_populates="thread",
        order_by="Completion.created_at",
        cascade="all, delete-orphan",
    )


class Message(Base):
    """
    A single message in a thread.

    ID format: UUID7
    """

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid7()),
    )

    # Parent thread
    thread_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional link to completion (assistant messages only)
    completion_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("completions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Message content
    role: Mapped[MessageRole] = mapped_column(MessageRoleType, nullable=False)
    # Parts stored as raw JSONB - validated by chat engine on read/write
    parts: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    # Relationships
    thread: Mapped[Thread] = relationship(
        "Thread",
        back_populates="messages",
    )
    completion: Mapped["Completion | None"] = relationship(
        "Completion",
        back_populates="messages",
    )
