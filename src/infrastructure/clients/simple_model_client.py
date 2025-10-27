"""Simple model client stub implementation."""

from typing import Optional

from src.domain.entities.model_config import ModelConfig
from src.infrastructure.clients.model_client import ModelClient


class SimpleModelClient(ModelClient):
    """Simple stub implementation of model client."""

    async def generate(self, prompt: str, config: Optional[ModelConfig] = None) -> str:
        """
        Generate response from model (stub).

        Args:
            prompt: Input prompt
            config: Optional model configuration

        Returns:
            Generated response
        """
        return f"[STUB] Generated response for prompt: {prompt[:50]}..."

    async def health_check(self) -> bool:
        """
        Check if model client is healthy.

        Returns:
            True if healthy
        """
        return True
