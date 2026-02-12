"""
Admin chat agent specification.

This agent is only accessible to users with admin role.
"""

from pydantic_ai import RunContext

from py_core.ai_ml import AgentDeps, AgentSpec


async def _system_prompt(ctx: RunContext[AgentDeps]) -> str:
    """Build system prompt for admin chat agent."""
    return """You are an admin assistant helping manage the application.

## Tools

### get_system_stats
Get current system statistics (users, widgets, etc). Sync - returns immediately.

### run_analysis
Run a background analysis. Async - dispatches a background job.
Parameters: analysis_type ("user_activity" | "widget_usage"), days (default 7)

Be concise and helpful. Only admins can access this assistant."""


def get_admin_chat_agent_spec() -> AgentSpec:
    """Build admin chat agent spec."""
    from src.agents.tools import get_system_stats, run_analysis

    return AgentSpec(
        model="claude-sonnet-4-5",
        system_prompt_builder=_system_prompt,
        tools=[get_system_stats, run_analysis],
    )
