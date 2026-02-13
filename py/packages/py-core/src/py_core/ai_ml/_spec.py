"""Declarative agent specification."""

from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

# Type alias for system prompt builder function
# Takes RunContext and returns the system prompt string
SystemPromptBuilder = Callable[..., Coroutine[Any, Any, str]]


@dataclass
class AgentSpec:
    """Declarative specification for an AI agent.

    This defines the agent's model, behavior, and capabilities without
    actually constructing the agent. Use build_agent() to create an
    executable agent from a spec.

    Attributes:
        model: Model identifier (e.g., "claude-sonnet-4-5", "claude-opus-4-5")
        thinking_enabled: Enable extended thinking for complex reasoning
        thinking_budget_tokens: Max tokens for thinking (when enabled)
        system_prompt_builder: Async function that builds system prompt from context
        tools: List of tool functions decorated with @tool
    """

    model: str = "claude-sonnet-4-5"
    thinking_enabled: bool = False
    thinking_budget_tokens: int = 4096
    system_prompt_builder: SystemPromptBuilder | None = None
    tools: list[Any] = field(default_factory=list)
