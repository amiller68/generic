"""Async tool payload base class.

This defines the interface for async tool results that background
tasks return. Each payload knows how to format itself for both
the pending state (before data is available) and completed state.
"""

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel

from py_core.ai_ml.types import ContentPart


class AsyncToolRefType(str, Enum):
    """Reference types for async tool executions.

    Add new types here as you add async tools.
    """

    SEARCH = "search"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    PROCESSING = "processing"


class AsyncToolPayload(BaseModel, ABC):
    """Self-describing async result payload.

    Implement this for each async tool to define how results
    are formatted for both UI and LLM.

    Class methods (pending state - no data yet):
    - format_pending_message(): UI message when task starts
    - format_pending_content_parts(): LLM content when task starts

    Instance methods (completed state - has data):
    - format_message(): UI message when complete
    - format_content_parts(): LLM content when complete
    """

    # Pending state (class methods - no data yet)
    @classmethod
    @abstractmethod
    def format_pending_message(cls) -> str:
        """UI message when task starts."""
        ...

    @classmethod
    @abstractmethod
    def format_pending_content_parts(cls) -> list[ContentPart]:
        """LLM content when task starts."""
        ...

    # Completed state (instance methods - has data)
    @abstractmethod
    def format_message(self) -> str:
        """UI message when complete."""
        ...

    @abstractmethod
    def format_content_parts(self) -> list[ContentPart]:
        """LLM content when complete."""
        ...
