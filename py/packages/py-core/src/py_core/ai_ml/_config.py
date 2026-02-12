"""Agent configuration for LLM providers."""

import os
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Configuration for AI agent.

    Loads API keys from environment variables if not provided directly.

    Attributes:
        anthropic_api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env var.
    """

    anthropic_api_key: str | None = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY")
    )

    def validate(self) -> None:
        """Validate configuration has required values."""
        if not self.anthropic_api_key:
            raise ValueError(
                "API key not available. Set ANTHROPIC_API_KEY environment variable "
                "or provide anthropic_api_key parameter."
            )
