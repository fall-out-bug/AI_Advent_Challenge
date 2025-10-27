"""
Tests for configuration module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from config.loader import ModelLimitsConfig, ModelLimitsLoader
from config.settings import AppConfig
from models.data_models import ModelLimits


class TestAppConfig:
    """Test AppConfig functionality."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AppConfig()

        assert config.app_name == "Token Analysis System"
        assert config.app_version == "1.0.0"
        assert config.app_env == "development"
        assert config.debug is False
        assert config.log_level == "WARNING"
        assert config.token_counter_mode == "simple"
        assert config.tokens_per_word_ratio == 1.3
        assert config.limit_profile == "practical"

    def test_environment_override(self):
        """Test environment variable override."""
        with patch.dict(
            "os.environ",
            {
                "APP_NAME": "Test App",
                "LOG_LEVEL": "DEBUG",
                "TOKEN_COUNTER_MODE": "accurate",
            },
        ):
            config = AppConfig()

            assert config.app_name == "Test App"
            assert config.log_level == "DEBUG"
            assert config.token_counter_mode == "accurate"

    def test_validation_log_level(self):
        """Test log level validation."""
        with patch.dict("os.environ", {"LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValueError, match="log_level must be one of"):
                AppConfig()

    def test_validation_token_counter_mode(self):
        """Test token counter mode validation."""
        with patch.dict("os.environ", {"TOKEN_COUNTER_MODE": "invalid"}):
            with pytest.raises(ValueError, match="token_counter_mode must be one of"):
                AppConfig()

    def test_validation_limit_profile(self):
        """Test limit profile validation."""
        with patch.dict("os.environ", {"LIMIT_PROFILE": "invalid"}):
            with pytest.raises(ValueError, match="limit_profile must be one of"):
                AppConfig()

    def test_validation_tokens_per_word_ratio(self):
        """Test tokens per word ratio validation."""
        with patch.dict("os.environ", {"TOKENS_PER_WORD_RATIO": "5.0"}):
            with pytest.raises(
                ValueError, match="tokens_per_word_ratio must be between"
            ):
                AppConfig()

    def test_validation_safety_margin(self):
        """Test safety margin validation."""
        with patch.dict("os.environ", {"EXPERIMENT_SAFETY_MARGIN": "2.0"}):
            with pytest.raises(
                ValueError, match="experiment_safety_margin must be between"
            ):
                AppConfig()

    def test_validation_temperature(self):
        """Test temperature validation."""
        with patch.dict("os.environ", {"MODEL_CLIENT_TEMPERATURE": "5.0"}):
            with pytest.raises(
                ValueError, match="model_client_temperature must be between"
            ):
                AppConfig()

    def test_environment_checkers(self):
        """Test environment checker methods."""
        config = AppConfig()

        assert config.is_development() is True
        assert config.is_production() is False

        with patch.dict("os.environ", {"APP_ENV": "production"}):
            config = AppConfig()
            assert config.is_development() is False
            assert config.is_production() is True

    def test_get_model_limits_file_path(self):
        """Test model limits file path generation."""
        config = AppConfig()
        path = config.get_model_limits_file_path()

        assert isinstance(path, Path)
        assert path.name == "model_limits.yaml"

    def test_get_log_config(self):
        """Test log configuration generation."""
        config = AppConfig()
        log_config = config.get_log_config()

        assert "version" in log_config
        assert "formatters" in log_config
        assert "handlers" in log_config
        assert "loggers" in log_config


class TestModelLimitsLoader:
    """Test ModelLimitsLoader functionality."""

    def test_load_from_file(self):
        """Test loading configuration from YAML file."""
        config_file = Path(__file__).parent.parent / "config" / "model_limits.yaml"

        loader = ModelLimitsLoader(config_file)
        config = loader.load()

        assert isinstance(config, ModelLimitsConfig)
        assert config.default_profile == "practical"
        assert config.safety_margin == 0.9
        assert config.tokens_per_word_ratio == 1.3

        # Check models are loaded
        assert "starcoder" in config.models
        assert "mistral" in config.models
        assert "qwen" in config.models
        assert "tinyllama" in config.models

    def test_get_model_limits(self):
        """Test getting model limits."""
        config_file = Path(__file__).parent.parent / "config" / "model_limits.yaml"
        loader = ModelLimitsLoader(config_file)
        config = loader.load()

        # Test StarCoder practical limits
        limits = config.get_model_limits("starcoder", "practical")
        assert limits is not None
        assert limits.max_input_tokens == 4096
        assert limits.max_output_tokens == 1024
        assert limits.max_total_tokens == 6000
        assert limits.recommended_input == 3500

        # Test StarCoder theoretical limits
        limits = config.get_model_limits("starcoder", "theoretical")
        assert limits is not None
        assert limits.max_input_tokens == 16384
        assert limits.max_output_tokens == 2048

        # Test non-existent model
        limits = config.get_model_limits("nonexistent", "practical")
        assert limits is None

        # Test non-existent profile
        limits = config.get_model_limits("starcoder", "nonexistent")
        assert limits is None

    def test_get_available_models(self):
        """Test getting available models."""
        config_file = Path(__file__).parent.parent / "config" / "model_limits.yaml"
        loader = ModelLimitsLoader(config_file)
        config = loader.load()

        models = config.get_available_models()
        expected_models = ["starcoder", "mistral", "qwen", "tinyllama"]

        assert set(models) == set(expected_models)

    def test_get_available_profiles(self):
        """Test getting available profiles."""
        config_file = Path(__file__).parent.parent / "config" / "model_limits.yaml"
        loader = ModelLimitsLoader(config_file)
        config = loader.load()

        profiles = config.get_available_profiles("starcoder")
        expected_profiles = ["theoretical", "practical"]

        assert set(profiles) == set(expected_profiles)

        # Test non-existent model
        profiles = config.get_available_profiles("nonexistent")
        assert profiles == []

    def test_file_not_found(self):
        """Test handling of missing config file."""
        loader = ModelLimitsLoader(Path("nonexistent.yaml"))

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_no_config_file_specified(self):
        """Test handling of no config file."""
        loader = ModelLimitsLoader()

        with pytest.raises(ValueError, match="No config file specified"):
            loader.load()

    def test_reload(self):
        """Test configuration reload."""
        config_file = Path(__file__).parent.parent / "config" / "model_limits.yaml"
        loader = ModelLimitsLoader(config_file)

        config1 = loader.load()
        config2 = loader.reload()

        assert config1.default_profile == config2.default_profile
        assert config1.safety_margin == config2.safety_margin

    def test_get_config_without_load(self):
        """Test getting config without loading."""
        config_file = Path(__file__).parent.parent / "config" / "model_limits.yaml"
        loader = ModelLimitsLoader(config_file)

        with pytest.raises(RuntimeError, match="Configuration not loaded"):
            loader.get_config()
