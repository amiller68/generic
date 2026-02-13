"""Tests for agent building."""

import os
from unittest import mock

import pytest

from py_core.ai_ml import AgentSpec, AgentConfig, build_agent


class TestAgentSpec:
    """Tests for AgentSpec dataclass."""

    def test_default_values(self) -> None:
        """AgentSpec has sensible defaults."""
        spec = AgentSpec()
        assert spec.model == "claude-sonnet-4-5"
        assert spec.thinking_enabled is False
        assert spec.thinking_budget_tokens == 4096
        assert spec.system_prompt_builder is None
        assert spec.tools == []

    def test_custom_model(self) -> None:
        """AgentSpec accepts custom model."""
        spec = AgentSpec(model="claude-opus-4-5")
        assert spec.model == "claude-opus-4-5"

    def test_thinking_enabled(self) -> None:
        """AgentSpec can enable thinking mode."""
        spec = AgentSpec(thinking_enabled=True, thinking_budget_tokens=8192)
        assert spec.thinking_enabled is True
        assert spec.thinking_budget_tokens == 8192


class TestBuildAgent:
    """Tests for build_agent factory function."""

    def test_raises_without_api_key(self) -> None:
        """build_agent raises ValueError when API key missing."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = AgentConfig()
            spec = AgentSpec(model="claude-sonnet-4-5")

            with pytest.raises(ValueError) as exc_info:
                build_agent(spec, config)

            assert "API key not available" in str(exc_info.value)

    def test_creates_agent_with_key(self) -> None:
        """build_agent creates Agent instance when API key provided."""
        config = AgentConfig(anthropic_api_key="test-key")
        spec = AgentSpec(model="claude-sonnet-4-5")

        agent = build_agent(spec, config)

        # Agent is created (we can't easily test internals)
        assert agent is not None

    def test_with_system_prompt_builder(self) -> None:
        """build_agent registers system prompt builder."""

        async def my_prompt(ctx) -> str:
            return "You are a helpful assistant."

        config = AgentConfig(anthropic_api_key="test-key")
        spec = AgentSpec(
            model="claude-sonnet-4-5",
            system_prompt_builder=my_prompt,
        )

        agent = build_agent(spec, config)
        assert agent is not None
