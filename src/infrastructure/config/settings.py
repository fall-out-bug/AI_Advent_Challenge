"""Configuration management."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """
    Application settings.

    Attributes:
        storage_path: Path to data storage
        model_default_name: Default model name
        model_default_max_tokens: Default max tokens
        model_default_temperature: Default temperature
    """

    storage_path: Path = Path("data")
    model_default_name: str = "gpt-4"
    model_default_max_tokens: int = 4096
    model_default_temperature: float = 0.7

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Create settings from environment variables.

        Returns:
            Settings instance
        """
        import os

        return cls(
            storage_path=Path(os.getenv("STORAGE_PATH", "data")),
            model_default_name=os.getenv("MODEL_NAME", "gpt-4"),
            model_default_max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "4096")),
            model_default_temperature=float(os.getenv("MODEL_TEMPERATURE", "0.7")),
        )

    def get_agent_storage_path(self) -> Path:
        """
        Get path for agent task storage.

        Returns:
            Storage path for agent tasks
        """
        return self.storage_path / "agents.json"

    def get_experiment_storage_path(self) -> Path:
        """
        Get path for experiment storage.

        Returns:
            Storage path for experiments
        """
        return self.storage_path / "experiments.json"
