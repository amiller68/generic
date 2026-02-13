"""Agent factory for creating Pydantic AI agents."""

import os
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

from ._config import AgentConfig
from ._deps import AgentDeps
from ._spec import AgentSpec


def build_agent(spec: AgentSpec, config: AgentConfig) -> Agent[AgentDeps, str]:
    """Create a configured Pydantic AI Agent from spec.

    Args:
        spec: Agent specification defining model, tools, and behavior
        config: Configuration with API keys

    Returns:
        Configured Agent instance ready to run

    Raises:
        ValueError: If API key is not available

    Example:
        spec = AgentSpec(
            model="claude-sonnet-4-5",
            system_prompt_builder=my_prompt_builder,
            tools=[search_tool],
        )
        config = AgentConfig()
        agent = build_agent(spec, config)
        result = await agent.run("Hello!", deps=deps)
    """
    config.validate()

    # Build model configuration
    model_settings: dict[str, Any] = {}

    if spec.thinking_enabled:
        model_settings["extra_headers"] = {
            "anthropic-beta": "interleaved-thinking-2025-05-14"
        }
        model_settings["max_tokens"] = spec.thinking_budget_tokens

    # Set API key in environment for pydantic-ai to use
    # (pydantic-ai reads ANTHROPIC_API_KEY from env)
    if config.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = config.anthropic_api_key

    # Create the Anthropic model
    model = AnthropicModel(spec.model)

    # Build agent kwargs
    agent_kwargs: dict[str, Any] = {
        "model": model,
        "deps_type": AgentDeps,
        "output_type": str,
    }

    if model_settings:
        agent_kwargs["model_settings"] = model_settings

    # Create the agent
    agent: Agent[AgentDeps, str] = Agent(**agent_kwargs)

    # Register system prompt if provided
    if spec.system_prompt_builder:
        builder = spec.system_prompt_builder  # Capture for closure

        @agent.system_prompt
        async def system_prompt(ctx: Any) -> str:
            return await builder(ctx)

    # Register tools
    for tool in spec.tools:
        agent.tool()(tool)

    return agent
