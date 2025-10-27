"""Model repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.model_config import ModelConfig


class ModelRepository(ABC):
    """Abstract repository for model configurations."""

    @abstractmethod
    async def save(self, config: ModelConfig) -> None:
        """
        Save or update a model configuration.

        Args:
            config: Model configuration entity
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, config_id: str) -> Optional[ModelConfig]:
        """
        Get model configuration by ID.

        Args:
            config_id: Configuration identifier

        Returns:
            Model configuration entity or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[ModelConfig]:
        """
        Get all model configurations.

        Returns:
            List of model configuration entities
        """
        raise NotImplementedError

    @abstractmethod
    async def get_active(self) -> List[ModelConfig]:
        """
        Get all active model configurations.

        Returns:
            List of active model configuration entities
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, config_id: str) -> bool:
        """
        Delete a model configuration.

        Args:
            config_id: Configuration identifier

        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError
