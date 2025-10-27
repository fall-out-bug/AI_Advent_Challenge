"""
Mock configuration for testing.

Provides mock implementations of configuration protocols
for testing token analyzer functionality.
"""

from typing import List

from core.interfaces.protocols import ConfigurationProtocol
from core.token_analyzer import LimitProfile
from models.data_models import ModelLimits


class MockConfiguration(ConfigurationProtocol):
    """Mock configuration for testing."""

    def __init__(self):
        """Initialize mock configuration with test data."""
        self._model_limits = {
            "starcoder": {
                "theoretical": ModelLimits(
                    max_input_tokens=16384,
                    max_output_tokens=2048,
                    max_total_tokens=16384,
                    sliding_window=4096,
                ),
                "practical": ModelLimits(
                    max_input_tokens=4096,
                    max_output_tokens=1024,
                    max_total_tokens=6000,
                    recommended_input=3500,
                ),
            },
            "mistral": {
                "theoretical": ModelLimits(
                    max_input_tokens=32768,
                    max_output_tokens=2048,
                    max_total_tokens=32768,
                ),
                "practical": ModelLimits(
                    max_input_tokens=8192,
                    max_output_tokens=1024,
                    max_total_tokens=10000,
                ),
            },
            "qwen": {
                "theoretical": ModelLimits(
                    max_input_tokens=32768,
                    max_output_tokens=2048,
                    max_total_tokens=32768,
                ),
                "practical": ModelLimits(
                    max_input_tokens=8192,
                    max_output_tokens=1024,
                    max_total_tokens=10000,
                ),
            },
            "tinyllama": {
                "theoretical": ModelLimits(
                    max_input_tokens=2048,
                    max_output_tokens=512,
                    max_total_tokens=2048,
                ),
                "practical": ModelLimits(
                    max_input_tokens=2048,
                    max_output_tokens=512,
                    max_total_tokens=2048,
                ),
            },
        }

    def get_model_limits(self, model_name: str, profile: str) -> ModelLimits:
        """Get model limits for specific model and profile."""
        if model_name not in self._model_limits:
            # Default to starcoder practical limits
            return self._model_limits["starcoder"]["practical"]

        return self._model_limits[model_name][profile]

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return list(self._model_limits.keys())

    def get_available_profiles(self) -> List[str]:
        """Get list of available profiles."""
        return ["theoretical", "practical"]

    def reload(self) -> None:
        """Reload configuration."""
        pass
