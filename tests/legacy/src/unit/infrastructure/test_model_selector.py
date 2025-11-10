"""Unit tests for model selector.

Following TDD principles and the Zen of Python.
"""

from pathlib import Path

from src.infrastructure.config.model_selector import ModelSelector


class TestModelSelectorInitialization:
    """Test model selector initialization."""

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        selector = ModelSelector()
        assert selector.config_path is not None
        assert selector.config is not None

    def test_init_with_custom_config_path(self):
        """Test initialization with custom config path."""
        custom_path = Path("/tmp/test_models.yml")
        selector = ModelSelector(config_path=custom_path)
        assert selector.config_path == custom_path

    def test_has_default_config(self):
        """Test default configuration exists."""
        selector = ModelSelector()
        assert selector.config is not None
        assert "models" in selector.config


class TestModelSelection:
    """Test model selection logic."""

    def test_selects_by_task_type(self):
        """Test model selection by task type."""
        selector = ModelSelector()

        model = selector.select_model(task_type="code_generation")
        assert model == "starcoder"

    def test_selects_default_when_no_task_type(self):
        """Test selecting default model when no task type."""
        selector = ModelSelector()

        model = selector.select_model()
        assert model == "starcoder"

    def test_selects_preferred_model(self):
        """Test selecting preferred model."""
        selector = ModelSelector()

        model = selector.select_model(preferred_model="mistral")
        assert model == "mistral"

    def test_selects_by_token_constraints(self):
        """Test model selection by token constraints."""
        selector = ModelSelector()

        # Should select model with enough capacity
        model = selector.select_model(max_tokens=3000)
        assert model in ["mistral", "qwen"]

    def test_falls_back_to_default(self):
        """Test falling back to default model."""
        selector = ModelSelector()

        # Invalid task type should use default
        model = selector.select_model(task_type="invalid_task")
        assert model == "starcoder"


class TestModelAvailability:
    """Test model availability checking."""

    def test_checks_model_availability(self):
        """Test checking if model is available."""
        selector = ModelSelector()

        assert selector._is_available("starcoder") is True
        assert selector._is_available("nonexistent") is False

    def test_lists_available_models(self):
        """Test listing available models."""
        selector = ModelSelector()

        models = selector.list_available_models()
        assert len(models) > 0
        assert "starcoder" in models


class TestModelInfo:
    """Test getting model information."""

    def test_gets_model_info(self):
        """Test getting model information."""
        selector = ModelSelector()

        info = selector.get_model_info("starcoder")
        assert info is not None
        assert "name" in info

    def test_gets_none_for_nonexistent_model(self):
        """Test getting None for nonexistent model."""
        selector = ModelSelector()

        info = selector.get_model_info("nonexistent")
        assert info is None


class TestModelConfig:
    """Test getting model configuration."""

    def test_gets_model_config(self):
        """Test getting model configuration."""
        selector = ModelSelector()

        config = selector.get_model_config("starcoder")
        assert config is not None
        assert config.model_name == "starcoder"

    def test_gets_none_for_nonexistent_model(self):
        """Test getting None for nonexistent model."""
        selector = ModelSelector()

        config = selector.get_model_config("nonexistent")
        assert config is None


class TestFallbackOrder:
    """Test fallback order logic."""

    def test_gets_fallback_order(self):
        """Test getting fallback order."""
        selector = ModelSelector()

        order = selector.get_fallback_order()
        assert len(order) > 0
        assert isinstance(order, list)


class TestTaskTypeSelection:
    """Test task type-based selection."""

    def test_selects_code_generation_model(self):
        """Test selecting model for code generation."""
        selector = ModelSelector()

        model = selector._select_by_task_type("code_generation")
        assert model == "starcoder"

    def test_selects_code_review_model(self):
        """Test selecting model for code review."""
        selector = ModelSelector()

        model = selector._select_by_task_type("code_review")
        assert model == "mistral"

    def test_selects_analysis_model(self):
        """Test selecting model for analysis."""
        selector = ModelSelector()

        model = selector._select_by_task_type("analysis")
        # May return None if model not in available list
        assert model is None or model == "qwen"

    def test_returns_none_for_unknown_task_type(self):
        """Test returning None for unknown task type."""
        selector = ModelSelector()

        model = selector._select_by_task_type("unknown_task")
        assert model is None
