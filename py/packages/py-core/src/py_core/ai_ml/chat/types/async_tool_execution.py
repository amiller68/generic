"""AsyncToolExecution types for API responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AsyncToolExecution(BaseModel):
    """Async tool execution representation."""

    id: str
    thread_id: str
    completion_id: str | None
    name: str
    status: str  # "pending", "completed", "failed"
    ref_type: str | None
    ref_id: str | None
    result: dict[str, Any] | None
    error_type: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
