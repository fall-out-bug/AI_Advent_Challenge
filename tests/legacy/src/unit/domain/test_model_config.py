"""Unit tests for model configuration entity."""

import pytest

from src.domain.entities.model_config import ModelConfig


def test_model_config_creation() -> None:
    """Test model configuration creation."""
    config = ModelConfig(
        config_id="config_1",
        model_name="gpt-4",
        provider="openai",
    )
    assert config.config_id == "config_1"
    assert config.model_name == "gpt-4"
    assert config.is_active


def test_model_config_validation() -> None:
    """Test model configuration validation."""
    # Valid config
    config = ModelConfig(
        config_id="config_1",
        model_name="gpt-4",
        provider="openai",
        max_tokens=4096,
        temperature=0.7,
    )
    assert config.max_tokens == 4096
    assert config.temperature == 0.7


def test_model_config_invalid_temperature() -> None:
    """Test invalid temperature validation."""
    with pytest.raises(ValueError, match="Temperature must be between"):
        ModelConfig(
            config_id="config_1",
            model_name="gpt-4",
            provider="openai",
            temperature=3.0,
        )


def test_model_config_activate() -> None:
    """Test activating configuration."""
    config = ModelConfig(
        config_id="config_1",
        model_name="gpt-4",
        provider="openai",
        is_active=False,
    )
    config.activate()
    assert config.is_active


def test_model_config_deactivate() -> None:
    """Test deactivating configuration."""
    config = ModelConfig(
        config_id="config_1",
        model_name="gpt-4",
        provider="openai",
    )
    config.deactivate()
    assert not config.is_active


def test_model_config_update_temperature() -> None:
    """Test updating temperature."""
    config = ModelConfig(
        config_id="config_1",
        model_name="gpt-4",
        provider="openai",
        temperature=0.7,
    )
    config.update_temperature(0.9)
    assert config.temperature == 0.9
