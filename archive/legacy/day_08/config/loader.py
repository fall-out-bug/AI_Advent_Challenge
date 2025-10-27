"""
Model limits loader for YAML configuration.

This module provides functionality to load model limits
from YAML configuration files with validation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from models.data_models import ModelLimits


@dataclass
class ModelLimitsConfig:
    """Configuration for model limits."""

    models: Dict[str, Dict[str, ModelLimits]]
    default_profile: str
    safety_margin: float
    tokens_per_word_ratio: float

    @classmethod
    def load_from_file(cls, file_path: Path) -> "ModelLimitsConfig":
        """Load configuration from YAML file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Parse models
        models = {}
        for model_name, profiles in data["models"].items():
            models[model_name] = {}
            for profile_name, limits_data in profiles.items():
                models[model_name][profile_name] = ModelLimits(
                    max_input_tokens=limits_data["max_input_tokens"],
                    max_output_tokens=limits_data["max_output_tokens"],
                    max_total_tokens=limits_data["max_total_tokens"],
                    sliding_window=limits_data.get("sliding_window"),
                    recommended_input=limits_data.get("recommended_input"),
                )

        return cls(
            models=models,
            default_profile=data["defaults"]["profile"],
            safety_margin=data["defaults"]["safety_margin"],
            tokens_per_word_ratio=data["defaults"]["tokens_per_word_ratio"],
        )

    def get_model_limits(self, model_name: str, profile: str) -> Optional[ModelLimits]:
        """Get limits for specific model and profile."""
        if model_name not in self.models:
            return None

        if profile not in self.models[model_name]:
            return None

        return self.models[model_name][profile]

    def get_available_models(self) -> list[str]:
        """Get list of available model names."""
        return list(self.models.keys())

    def get_available_profiles(self, model_name: str) -> list[str]:
        """Get list of available profiles for a model."""
        if model_name not in self.models:
            return []
        return list(self.models[model_name].keys())


class ModelLimitsLoader:
    """Loader for model limits configuration."""

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize loader with optional config file."""
        self.config_file = config_file
        self._config: Optional[ModelLimitsConfig] = None

    def load(self, config_file: Optional[Path] = None) -> ModelLimitsConfig:
        """Load configuration from file."""
        file_path = config_file or self.config_file
        if file_path is None:
            raise ValueError("No config file specified")

        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        self._config = ModelLimitsConfig.load_from_file(file_path)
        return self._config

    def get_config(self) -> ModelLimitsConfig:
        """Get loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load() first.")
        return self._config

    def reload(self) -> ModelLimitsConfig:
        """Reload configuration from file."""
        if self.config_file is None:
            raise ValueError("No config file specified for reload")

        return self.load(self.config_file)
