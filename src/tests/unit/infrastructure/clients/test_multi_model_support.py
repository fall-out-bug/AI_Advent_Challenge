"""Tests for multi-model client support.

Following TDD approach:
- Write tests first (red)
- Implement minimal code (green)
- Refactor for clarity (refactor)
"""

import pytest

from src.infrastructure.clients.multi_model_client import MultiModelSupport


class TestMultiModelSupport:
    """Test multi-model support functionality."""

    def test_can_list_available_models(self):
        """Test that client can list available models."""
        multi_model = MultiModelSupport()

        models = multi_model.get_available_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "starcoder" in models

    def test_can_select_model_by_name(self):
        """Test that client can select a specific model."""
        multi_model = MultiModelSupport()

        success = multi_model.select_model("mistral")

        assert success is True
        assert multi_model.get_current_model() == "mistral"

    def test_can_switch_between_models(self):
        """Test that client can switch between different models."""
        multi_model = MultiModelSupport()

        multi_model.select_model("qwen")
        assert multi_model.get_current_model() == "qwen"

        multi_model.select_model("tinyllama")
        assert multi_model.get_current_model() == "tinyllama"

    def test_can_get_model_info(self):
        """Test that client can retrieve model information."""
        multi_model = MultiModelSupport()

        info = multi_model.get_model_info("starcoder")

        assert info is not None
        assert "name" in info
        assert "max_tokens" in info
        assert "recommended_tokens" in info

    def test_can_validate_model_availability(self):
        """Test that client can check if model is available."""
        multi_model = MultiModelSupport()

        assert multi_model.validate_model_availability("starcoder") is True
        assert multi_model.validate_model_availability("unknown") is False

    def test_supports_model_specific_config(self):
        """Test that client can use model-specific configurations."""
        multi_model = MultiModelSupport()

        max_tokens = multi_model.get_max_tokens("mistral")
        recommended_tokens = multi_model.get_recommended_tokens("mistral")

        assert max_tokens > 0
        assert recommended_tokens > 0
        assert recommended_tokens <= max_tokens
