"""Tests for AgentConfig."""

import os
from unittest import mock

import pytest

from py_core.ai_ml import AgentConfig


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_values(self) -> None:
        """AgentConfig has None default when env var not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = AgentConfig()
            assert config.anthropic_api_key is None

    def test_loads_from_env(self) -> None:
        """AgentConfig loads ANTHROPIC_API_KEY from environment."""
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            config = AgentConfig()
            assert config.anthropic_api_key == "env-key"

    def test_explicit_key_overrides_env(self) -> None:
        """Explicit key parameter takes precedence."""
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            config = AgentConfig(anthropic_api_key="explicit-key")
            assert config.anthropic_api_key == "explicit-key"

    def test_validate_raises_without_key(self) -> None:
        """validate() raises ValueError when API key missing."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = AgentConfig()
            with pytest.raises(ValueError) as exc_info:
                config.validate()
            assert "API key not available" in str(exc_info.value)

    def test_validate_passes_with_key(self) -> None:
        """validate() passes when API key is set."""
        config = AgentConfig(anthropic_api_key="test-key")
        config.validate()  # Should not raise
