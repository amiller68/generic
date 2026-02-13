"""AI/ML module for LLM integration.

This module provides a framework for building AI agents with:
- Declarative agent specifications
- Tool result types with explicit LLM content
- Async tool execution with lifecycle management
- Dependency injection for tools

Example:
    from py_core.ai_ml import AgentSpec, AgentConfig, build_agent, AgentDeps

    spec = AgentSpec(
        model="claude-sonnet-4-5",
        system_prompt_builder=my_system_prompt,
        tools=[search_tool, process_tool],
    )

    config = AgentConfig()
    agent = build_agent(spec, config)

    result = await agent.run("Hello!", deps=AgentDeps(...))
"""

from ._config import AgentConfig
from ._deps import AgentDeps
from ._spec import AgentSpec
from ._agent import build_agent

__all__ = [
    "AgentConfig",
    "AgentDeps",
    "AgentSpec",
    "build_agent",
]
