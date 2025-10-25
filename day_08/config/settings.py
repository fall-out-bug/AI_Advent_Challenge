"""
Application settings using environment variables.

This module provides centralized configuration management
with environment variable support and validation.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional


class AppConfig:
    """Application configuration with environment variable support."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Application settings
        self.app_name = os.getenv("APP_NAME", "Token Analysis System")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # Logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_format = os.getenv("LOG_FORMAT", "json")
        self.log_file = os.getenv("LOG_FILE")

        # Token counting settings
        self.token_counter_mode = os.getenv("TOKEN_COUNTER_MODE", "simple")
        self.tokens_per_word_ratio = float(os.getenv("TOKENS_PER_WORD_RATIO", "1.3"))
        self.limit_profile = os.getenv("LIMIT_PROFILE", "practical")

        # ML service settings
        self.ml_service_url = os.getenv("ML_SERVICE_URL", "http://localhost:8004")
        self.ml_service_timeout = int(os.getenv("ML_SERVICE_TIMEOUT", "30"))
        self.ml_service_retry_attempts = int(
            os.getenv("ML_SERVICE_RETRY_ATTEMPTS", "3")
        )

        # Model client settings
        self.model_client_timeout = int(os.getenv("MODEL_CLIENT_TIMEOUT", "60"))
        self.model_client_max_tokens = int(os.getenv("MODEL_CLIENT_MAX_TOKENS", "1000"))
        self.model_client_temperature = float(
            os.getenv("MODEL_CLIENT_TEMPERATURE", "0.7")
        )

        # Experiment settings
        self.experiment_random_seed = int(os.getenv("EXPERIMENT_RANDOM_SEED", "42"))
        self.experiment_deterministic = (
            os.getenv("EXPERIMENT_DETERMINISTIC", "true").lower() == "true"
        )
        self.experiment_safety_margin = float(
            os.getenv("EXPERIMENT_SAFETY_MARGIN", "0.9")
        )

        # Performance settings
        self.max_concurrent_experiments = int(
            os.getenv("MAX_CONCURRENT_EXPERIMENTS", "5")
        )
        self.cache_size = int(os.getenv("CACHE_SIZE", "1000"))

        # File paths
        self.config_dir = Path(os.getenv("CONFIG_DIR", str(Path(__file__).parent)))
        self.model_limits_file = os.getenv("MODEL_LIMITS_FILE", "model_limits.yaml")

        # Validate configuration
        self._validate()

    def _validate(self):
        """Validate configuration values."""
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")

        # Validate token counter mode
        valid_modes = ["simple", "accurate", "hybrid"]
        if self.token_counter_mode not in valid_modes:
            raise ValueError(f"token_counter_mode must be one of {valid_modes}")

        # Validate limit profile
        valid_profiles = ["theoretical", "practical"]
        if self.limit_profile not in valid_profiles:
            raise ValueError(f"limit_profile must be one of {valid_profiles}")

        # Validate app environment
        valid_envs = ["development", "testing", "staging", "production"]
        if self.app_env not in valid_envs:
            raise ValueError(f"app_env must be one of {valid_envs}")

        # Validate tokens per word ratio
        if not 0.5 <= self.tokens_per_word_ratio <= 3.0:
            raise ValueError("tokens_per_word_ratio must be between 0.5 and 3.0")

        # Validate safety margin
        if not 0.1 <= self.experiment_safety_margin <= 1.0:
            raise ValueError("experiment_safety_margin must be between 0.1 and 1.0")

        # Validate temperature
        if not 0.0 <= self.model_client_temperature <= 2.0:
            raise ValueError("model_client_temperature must be between 0.0 and 2.0")

    def get_model_limits_file_path(self) -> Path:
        """Get full path to model limits file."""
        return self.config_dir / self.model_limits_file

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                },
                "text": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level,
                    "formatter": self.log_format,
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "": {  # root logger
                    "level": self.log_level,
                    "handlers": ["console"],
                },
            },
        }


# Global configuration instance
config = AppConfig()
