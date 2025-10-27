"""Model client interface."""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.model_config import ModelConfig


class ModelClient(ABC):
    """Abstract model client interface."""

    @abstractmethod
    async def generate(self, prompt: str, config: Optional[ModelConfig] = None) -> str:
        """
        Generate response from model.

        Args:
            prompt: Input prompt
            config: Optional model configuration

        Returns:
            Generated response
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if model client is healthy.

        Returns:
            True if healthy, False otherwise
        """
        raise NotImplementedError
