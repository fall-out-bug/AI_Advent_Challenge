"""Model versioning and registry for ML models.

Following ML Engineering best practices: model versioning and reproducibility.
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for tracking deployed ML models.

    Single responsibility: track model versions and metadata.
    """

    def __init__(self) -> None:
        """Initialize model registry."""
        self._models: Dict[str, Dict[str, any]] = {}

    def register_model(
        self,
        model_name: str,
        version: str,
        model_hash: Optional[str] = None,
        metadata: Optional[Dict[str, any]] = None,
    ) -> None:
        """Register a model version.

        Args:
            model_name: Name of the model (e.g., "mistral", "qwen")
            version: Version string (e.g., "v1.0.0", "2024-01-01")
            model_hash: Optional hash of model weights/config
            metadata: Optional metadata dictionary
        """
        if model_hash is None:
            model_hash = self._generate_hash(f"{model_name}:{version}")

        self._models[model_name] = {
            "version": version,
            "hash": model_hash,
            "deployed_at": datetime.utcnow().isoformat(),
            "deployed_at_timestamp": datetime.utcnow().timestamp(),
            "metadata": metadata or {},
        }

        logger.info(
            f"Registered model {model_name} version {version} "
            f"(hash: {model_hash[:8]}...)"
        )

    def get_model_info(self, model_name: str) -> Optional[Dict[str, any]]:
        """Get model information.

        Args:
            model_name: Name of the model

        Returns:
            Model info dictionary or None if not found
        """
        return self._models.get(model_name)

    def get_model_version(self, model_name: str) -> Optional[str]:
        """Get current model version.

        Args:
            model_name: Name of the model

        Returns:
            Version string or None if not found
        """
        info = self.get_model_info(model_name)
        return info.get("version") if info else None

    def get_model_hash(self, model_name: str) -> Optional[str]:
        """Get model hash.

        Args:
            model_name: Name of the model

        Returns:
            Hash string or None if not found
        """
        info = self.get_model_info(model_name)
        return info.get("hash") if info else None

    def list_models(self) -> list[str]:
        """List all registered models.

        Returns:
            List of model names
        """
        return list(self._models.keys())

    def _generate_hash(self, text: str) -> str:
        """Generate hash for model identification.

        Args:
            text: Text to hash

        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(text.encode()).hexdigest()


# Global registry instance
_model_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    """Get global model registry instance.

    Returns:
        ModelRegistry instance
    """
    return _model_registry
