"""Debug utilities for development and troubleshooting."""

import json
from pathlib import Path
from typing import Any, Dict

from src.infrastructure.config.settings import Settings


class DebugUtils:
    """Utility methods for debugging and development."""

    def __init__(self, settings: Settings):
        """Initialize debug utils."""
        self.settings = settings

    def dump_config(self) -> Dict[str, Any]:
        """Dump current configuration."""
        return {
            "storage_path": str(self.settings.storage_path),
            "agent_storage": str(self.settings.get_agent_storage_path()),
            "experiment_storage": str(self.settings.get_experiment_storage_path()),
            "model_default_name": self.settings.model_default_name,
            "model_default_max_tokens": self.settings.model_default_max_tokens,
            "model_default_temperature": self.settings.model_default_temperature,
        }

    def count_tokens(self, text: str) -> Dict[str, int]:
        """Estimate token count for text."""
        # Simple estimation: ~4 chars per token
        estimated_tokens = len(text) / 4

        # Word count
        words = text.split()
        word_count = len(words)

        return {
            "estimated_tokens": int(estimated_tokens),
            "character_count": len(text),
            "word_count": word_count,
            "tokens_per_word": round(estimated_tokens / word_count, 2)
            if word_count > 0
            else 0,
        }

    def replay_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request for replay.

        Args:
            request_data: Original request data

        Returns:
            Reconstructed request with metadata
        """
        return {
            "original_request": request_data,
            "replay_metadata": {
                "timestamp": self._get_timestamp(),
                "validation_status": self._validate_request(request_data),
                "estimated_tokens": self.count_tokens(str(request_data)),
            },
        }

    def check_dependencies(self) -> Dict[str, Any]:
        """Check installed dependencies.

        Returns:
            Dictionary with dependency info
        """
        dependencies = {}
        packages_to_check = [
            "httpx",
            "fastapi",
            "uvicorn",
            "pydantic",
            "pyyaml",
            "tiktoken",
            "rich",
        ]

        for package in packages_to_check:
            try:
                module = __import__(package)
                dependencies[package] = {
                    "installed": True,
                    "version": getattr(module, "__version__", "unknown"),
                }
            except ImportError:
                dependencies[package] = {"installed": False, "version": None}

        return dependencies

    def export_config_snapshot(self, filepath: str) -> None:
        """Export configuration snapshot.

        Args:
            filepath: Output file path
        """
        snapshot = {
            "configuration": self.dump_config(),
            "dependencies": self.check_dependencies(),
            "timestamp": self._get_timestamp(),
        }

        with Path(filepath).open("w") as f:
            json.dump(snapshot, f, indent=2)

    def _validate_request(self, request_data: Dict[str, Any]) -> str:
        """Validate request data.

        Args:
            request_data: Request data to validate

        Returns:
            Validation status
        """
        if not isinstance(request_data, dict):
            return "invalid"

        required_fields = ["prompt", "model"]
        if all(field in request_data for field in required_fields):
            return "valid"
        return "incomplete"

    def _get_timestamp(self) -> str:
        """Get current timestamp.

        Returns:
            ISO timestamp string
        """
        from datetime import datetime

        return datetime.utcnow().isoformat()
