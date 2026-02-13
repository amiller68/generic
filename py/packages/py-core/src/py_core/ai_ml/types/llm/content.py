"""
LLM content part types.

These types define the structure of content parts that can be included
in messages. Supports text, tool calls, and tool results.
"""

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, RootModel


class TextPart(BaseModel):
    """A text content part."""

    kind: Literal["text"] = "text"
    content: str


class ToolCallPart(BaseModel):
    """A tool call/function invocation part.

    Represents when the LLM invokes a tool during processing.
    """

    kind: Literal["tool_call"] = "tool_call"
    call_id: str  # Unique ID for matching with result
    tool_name: str  # Name of the tool being called
    arguments: dict[str, Any]  # Tool arguments as JSON


class ToolResultPart(BaseModel):
    """Result of a tool call.

    Links back to the original tool call via call_id.
    """

    kind: Literal["tool_result"] = "tool_result"
    call_id: str  # Links to original ToolCallPart.call_id
    tool_name: str  # Name of the tool
    result: str  # JSON string result from tool


# Union of all supported content part types
ContentPart = Annotated[
    Union[TextPart, ToolCallPart, ToolResultPart],
    Field(discriminator="kind"),
]


class ContentPartList(RootModel[list[ContentPart]]):
    """List of content parts - used for type-safe JSONB storage."""

    root: list[ContentPart]

    def __iter__(self):
        return iter(self.root)

    def __len__(self):
        return len(self.root)


def extract_text_content(raw_parts: list[dict]) -> str:
    """
    Extract text content from raw message parts.

    Args:
        raw_parts: Raw JSONB parts from database

    Returns:
        Concatenated text content from all text parts
    """
    parts = ContentPartList.model_validate(raw_parts)
    text_parts = [p.content for p in parts if isinstance(p, TextPart)]
    return " ".join(text_parts)
