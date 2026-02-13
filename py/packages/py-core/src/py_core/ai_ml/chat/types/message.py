"""Message types for API responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Message(BaseModel):
    """Message representation."""

    id: str
    thread_id: str
    role: str  # "user" or "assistant"
    parts: list[dict[str, Any]]
    created_at: datetime
    completion_id: str | None = None

    class Config:
        from_attributes = True
