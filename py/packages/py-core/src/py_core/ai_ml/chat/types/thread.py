"""Thread types for API responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Thread(BaseModel):
    """Full thread representation."""

    id: str
    user_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list["Message"] = []

    class Config:
        from_attributes = True


class ThreadListItem(BaseModel):
    """Thread summary for list views."""

    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_preview: str | None = None

    class Config:
        from_attributes = True


from .message import Message  # noqa: E402

Thread.model_rebuild()
