"""
Tests for shared.config.models module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest
from shared_package.config.models import (
    LOCAL_MODELS,
    MODEL_CONFIGS,
    MODEL_PORTS,
    ModelName,
    ModelPort,
    ModelType,
    get_local_models,
    get_model_config,
    get_model_port,
    is_local_model,
)


class TestModelEnums:
    """Test model enums."""

    def test_model_type_enum(self):
        """Test ModelType enum values."""
        assert ModelType.LOCAL.value == "local"
        assert ModelType.EXTERNAL.value == "external"

    def test_model_name_enum(self):
        """Test ModelName enum values."""
        assert ModelName.QWEN.value == "qwen"
        assert ModelName.MISTRAL.value == "mistral"
        assert ModelName.TINYLLAMA.value == "tinyllama"
        assert ModelName.PERPLEXITY.value == "perplexity"
        assert ModelName.CHADGPT.value == "chadgpt"

    def test_model_port_enum(self):
        """Test ModelPort enum values."""
        assert ModelPort.QWEN.value == 8000
        assert ModelPort.MISTRAL.value == 8001
        assert ModelPort.TINYLLAMA.value == 8002


class TestModelConfigs:
    """Test model configurations."""

    def test_model_configs_structure(self):
        """Test MODEL_CONFIGS structure."""
        assert len(MODEL_CONFIGS) == 6

        # Test local models
        assert "qwen" in MODEL_CONFIGS
        assert "mistral" in MODEL_CONFIGS
        assert "tinyllama" in MODEL_CONFIGS
        assert "starcoder" in MODEL_CONFIGS

        # Test external models
        assert "perplexity" in MODEL_CONFIGS
        assert "chadgpt" in MODEL_CONFIGS

    def test_local_model_config(self):
        """Test local model configuration."""
        qwen_config = MODEL_CONFIGS["qwen"]

        assert qwen_config["type"] == "local"
        assert qwen_config["port"] == 8000
        assert qwen_config["url"] == "http://localhost:8000"
        assert qwen_config["display_name"] == "Qwen-4B"
        assert "description" in qwen_config
        assert qwen_config.get("openai_compatible", False) is True

    def test_openai_compatible_flag(self):
        """Test OpenAI compatibility flag for local models."""
        local_models = ["qwen", "mistral", "tinyllama", "starcoder"]

        for model_name in local_models:
            config = MODEL_CONFIGS[model_name]
            assert (
                config.get("openai_compatible", False) is True
            ), f"Model {model_name} should have openai_compatible=True"

    def test_external_model_config(self):
        """Test external model configuration."""
        perplexity_config = MODEL_CONFIGS["perplexity"]

        assert perplexity_config["type"] == "external"
        assert perplexity_config["url"] == "https://api.perplexity.ai/chat/completions"
        assert perplexity_config["display_name"] == "Perplexity Sonar"
        assert "description" in perplexity_config


class TestBackwardCompatibility:
    """Test backward compatibility mappings."""

    def test_model_ports_mapping(self):
        """Test MODEL_PORTS mapping."""
        assert MODEL_PORTS["qwen"] == 8000
        assert MODEL_PORTS["mistral"] == 8001
        assert MODEL_PORTS["tinyllama"] == 8002

    def test_local_models_mapping(self):
        """Test LOCAL_MODELS mapping."""
        assert LOCAL_MODELS["qwen"] == "http://localhost:8000"
        assert LOCAL_MODELS["mistral"] == "http://localhost:8001"
        assert LOCAL_MODELS["tinyllama"] == "http://localhost:8002"


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_model_config_success(self):
        """Test get_model_config with valid model."""
        config = get_model_config("qwen")
        assert config["type"] == "local"
        assert config["port"] == 8000

    def test_get_model_config_invalid(self):
        """Test get_model_config with invalid model."""
        with pytest.raises(KeyError, match="Unknown model"):
            get_model_config("invalid_model")

    def test_get_local_models(self):
        """Test get_local_models function."""
        local_models = get_local_models()
        assert len(local_models) == 4
        assert "qwen" in local_models
        assert "mistral" in local_models
        assert "tinyllama" in local_models
        assert "starcoder" in local_models

    def test_get_model_port_local(self):
        """Test get_model_port with local model."""
        port = get_model_port("qwen")
        assert port == 8000

    def test_get_model_port_external(self):
        """Test get_model_port with external model."""
        with pytest.raises(KeyError, match="is not local"):
            get_model_port("perplexity")

    def test_get_model_port_invalid(self):
        """Test get_model_port with invalid model."""
        with pytest.raises(KeyError, match="Unknown model"):
            get_model_port("invalid_model")

    def test_is_local_model_local(self):
        """Test is_local_model with local model."""
        assert is_local_model("qwen") is True
        assert is_local_model("mistral") is True
        assert is_local_model("tinyllama") is True

    def test_is_local_model_external(self):
        """Test is_local_model with external model."""
        assert is_local_model("perplexity") is False
        assert is_local_model("chadgpt") is False

    def test_is_local_model_invalid(self):
        """Test is_local_model with invalid model."""
        assert is_local_model("invalid_model") is False
