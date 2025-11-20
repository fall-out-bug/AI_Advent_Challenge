"""
Tests for agent configuration module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest
from shared_package.config.agents import (
    AGENT_CONFIGS,
    CODE_GENERATOR_PROMPT_TEMPLATE,
    CODE_REVIEWER_PROMPT_TEMPLATE,
    DEFAULT_GENERATOR_CONFIG,
    DEFAULT_REVIEWER_CONFIG,
    MODEL_AGENT_COMPATIBILITY,
    AgentConfig,
    CodeGeneratorConfig,
    CodeReviewerConfig,
    get_agent_config,
    get_compatible_models,
    get_model_config_for_agent,
    get_prompt_template,
    get_recommended_models,
    is_model_recommended_for_agent,
)


class TestAgentConfig:
    """Test AgentConfig dataclass."""

    def test_default_agent_config(self):
        """Test default agent configuration."""
        config = AgentConfig()
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.max_retries == 3
        assert config.timeout == 600.0

    def test_custom_agent_config(self):
        """Test custom agent configuration."""
        config = AgentConfig(max_tokens=3000, temperature=0.5)
        assert config.max_tokens == 3000
        assert config.temperature == 0.5
        assert config.max_retries == 3  # Default value


class TestCodeGeneratorConfig:
    """Test CodeGeneratorConfig dataclass."""

    def test_default_generator_config(self):
        """Test default code generator configuration."""
        config = CodeGeneratorConfig()
        assert config.max_tokens == 4000
        assert config.temperature == 0.7
        assert config.max_retries == 3
        assert isinstance(config.supported_languages, list)
        assert "python" in config.supported_languages

    def test_custom_generator_config(self):
        """Test custom code generator configuration."""
        config = CodeGeneratorConfig(
            max_tokens=5000, supported_languages=["python", "rust"]
        )
        assert config.max_tokens == 5000
        assert config.supported_languages == ["python", "rust"]


class TestCodeReviewerConfig:
    """Test CodeReviewerConfig dataclass."""

    def test_default_reviewer_config(self):
        """Test default code reviewer configuration."""
        config = CodeReviewerConfig()
        assert config.max_tokens == 2000
        assert config.temperature == 0.3
        assert config.check_pep8 is True
        assert config.check_complexity is True
        assert config.check_security is True

    def test_custom_reviewer_config(self):
        """Test custom code reviewer configuration."""
        config = CodeReviewerConfig(max_tokens=3000, check_pep8=False)
        assert config.max_tokens == 3000
        assert config.check_pep8 is False


class TestDefaultConfigs:
    """Test default agent configurations."""

    def test_default_generator_config_instance(self):
        """Test default generator config instance."""
        assert DEFAULT_GENERATOR_CONFIG.max_tokens == 4000
        assert DEFAULT_GENERATOR_CONFIG.temperature == 0.7

    def test_default_reviewer_config_instance(self):
        """Test default reviewer config instance."""
        assert DEFAULT_REVIEWER_CONFIG.max_tokens == 2000
        assert DEFAULT_REVIEWER_CONFIG.temperature == 0.3


class TestAgentConfigs:
    """Test AGENT_CONFIGS dictionary."""

    def test_agent_configs_contains_agents(self):
        """Test AGENT_CONFIGS contains both agents."""
        assert "code_generator" in AGENT_CONFIGS
        assert "code_reviewer" in AGENT_CONFIGS

    def test_agent_configs_types(self):
        """Test AGENT_CONFIGS contains correct types."""
        assert isinstance(AGENT_CONFIGS["code_generator"], CodeGeneratorConfig)
        assert isinstance(AGENT_CONFIGS["code_reviewer"], CodeReviewerConfig)


class TestModelAgentCompatibility:
    """Test MODEL_AGENT_COMPATIBILITY matrix."""

    def test_compatibility_contains_models(self):
        """Test compatibility matrix contains models."""
        assert "qwen" in MODEL_AGENT_COMPATIBILITY
        assert "mistral" in MODEL_AGENT_COMPATIBILITY
        assert "starcoder" in MODEL_AGENT_COMPATIBILITY

    def test_compatibility_structure(self):
        """Test compatibility matrix structure."""
        qwen_config = MODEL_AGENT_COMPATIBILITY["qwen"]
        assert "code_generator" in qwen_config
        assert "code_reviewer" in qwen_config

        generator_config = qwen_config["code_generator"]
        assert "recommended" in generator_config
        assert "config" in generator_config

    def test_compatibility_config_values(self):
        """Test compatibility configuration values."""
        starcoder_generator = MODEL_AGENT_COMPATIBILITY["starcoder"]["code_generator"]
        assert starcoder_generator["recommended"] is True
        assert "max_tokens" in starcoder_generator["config"]
        assert "temperature" in starcoder_generator["config"]


class TestGetAgentConfig:
    """Test get_agent_config function."""

    def test_get_generator_config(self):
        """Test getting generator config."""
        config = get_agent_config("code_generator")
        assert isinstance(config, CodeGeneratorConfig)
        assert config.max_tokens == 4000

    def test_get_reviewer_config(self):
        """Test getting reviewer config."""
        config = get_agent_config("code_reviewer")
        assert isinstance(config, CodeReviewerConfig)
        assert config.max_tokens == 2000

    def test_get_unknown_agent(self):
        """Test getting unknown agent raises error."""
        with pytest.raises(KeyError, match="Unknown agent"):
            get_agent_config("unknown_agent")


class TestGetModelConfigForAgent:
    """Test get_model_config_for_agent function."""

    def test_get_qwen_generator_config(self):
        """Test getting Qwen generator config."""
        config = get_model_config_for_agent("qwen", "code_generator")
        assert config["recommended"] is True
        assert "max_tokens" in config["config"]

    def test_get_mistral_reviewer_config(self):
        """Test getting Mistral reviewer config."""
        config = get_model_config_for_agent("mistral", "code_reviewer")
        assert config["recommended"] is True
        assert "temperature" in config["config"]

    def test_get_unknown_model(self):
        """Test getting unknown model raises error."""
        with pytest.raises(KeyError):
            get_model_config_for_agent("unknown_model", "code_generator")

    def test_get_incompatible_combination(self):
        """Test getting incompatible model-agent combination."""
        with pytest.raises(KeyError):
            # Assuming a non-existent agent for test
            get_model_config_for_agent("qwen", "invalid_agent")


class TestIsModelRecommendedForAgent:
    """Test is_model_recommended_for_agent function."""

    def test_qwen_generator_recommended(self):
        """Test Qwen is recommended for code generation."""
        assert is_model_recommended_for_agent("qwen", "code_generator") is True

    def test_starcoder_reviewer_recommended(self):
        """Test StarCoder is recommended for code review."""
        assert is_model_recommended_for_agent("starcoder", "code_reviewer") is True

    def test_tinyllama_not_recommended(self):
        """Test TinyLlama is not recommended."""
        assert is_model_recommended_for_agent("tinyllama", "code_generator") is False


class TestGetCompatibleModels:
    """Test get_compatible_models function."""

    def test_compatible_models_for_generator(self):
        """Test getting compatible models for generator."""
        models = get_compatible_models("code_generator")
        assert len(models) > 0
        assert "qwen" in models
        assert "mistral" in models

    def test_compatible_models_for_reviewer(self):
        """Test getting compatible models for reviewer."""
        models = get_compatible_models("code_reviewer")
        assert len(models) > 0
        assert "qwen" in models
        assert "starcoder" in models


class TestGetRecommendedModels:
    """Test get_recommended_models function."""

    def test_recommended_models_for_generator(self):
        """Test getting recommended models for generator."""
        models = get_recommended_models("code_generator")
        assert len(models) > 0
        assert "qwen" in models
        assert "starcoder" in models
        assert "tinyllama" not in models  # Not recommended

    def test_recommended_models_for_reviewer(self):
        """Test getting recommended models for reviewer."""
        models = get_recommended_models("code_reviewer")
        assert len(models) > 0
        assert "qwen" in models
        assert "mistral" in models


class TestGetPromptTemplate:
    """Test get_prompt_template function."""

    def test_get_generator_template(self):
        """Test getting generator prompt template."""
        template = get_prompt_template("code_generator")
        assert isinstance(template, str)
        assert "{language}" in template
        assert "{task}" in template
        assert template == CODE_GENERATOR_PROMPT_TEMPLATE

    def test_get_reviewer_template(self):
        """Test getting reviewer prompt template."""
        template = get_prompt_template("code_reviewer")
        assert isinstance(template, str)
        assert "{language}" in template
        assert "{code}" in template
        assert template == CODE_REVIEWER_PROMPT_TEMPLATE

    def test_get_unknown_agent_template(self):
        """Test getting unknown agent template raises error."""
        with pytest.raises(KeyError):
            get_prompt_template("unknown_agent")


class TestPromptTemplates:
    """Test prompt templates."""

    def test_generator_template_content(self):
        """Test generator template content."""
        assert "Generate" in CODE_GENERATOR_PROMPT_TEMPLATE
        assert "Requirements" in CODE_GENERATOR_PROMPT_TEMPLATE
        assert "Code:" in CODE_GENERATOR_PROMPT_TEMPLATE

    def test_reviewer_template_content(self):
        """Test reviewer template content."""
        assert "Review" in CODE_REVIEWER_PROMPT_TEMPLATE
        assert "quality" in CODE_REVIEWER_PROMPT_TEMPLATE
        assert "PEP8" in CODE_REVIEWER_PROMPT_TEMPLATE

    def test_template_formatting(self):
        """Test prompt template formatting."""
        formatted = CODE_GENERATOR_PROMPT_TEMPLATE.format(
            language="python", task="Create a hello world function"
        )
        assert "python" in formatted
        assert "Create a hello world function" in formatted
