"""Shared SDK model client integration."""

import sys
from pathlib import Path
from typing import Optional

from src.domain.entities.model_config import ModelConfig
from src.infrastructure.clients.model_client import ModelClient

# Add shared to path for imports
shared_path = Path(__file__).parent.parent.parent.parent / "shared"
if shared_path.exists():
    sys.path.insert(0, str(shared_path))

try:
    from shared_package.clients.unified_client import UnifiedModelClient
    from shared_package.config.models import ModelConfig as SDKModelConfig

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


class SharedSDKModelClient(ModelClient):
    """
    Model client using shared SDK.

    Integrates shared package unified client with new architecture.
    """

    def __init__(self) -> None:
        """Initialize client with shared SDK."""
        if not SDK_AVAILABLE:
            raise ImportError("Shared SDK not available")

        self.client = UnifiedModelClient()

    async def generate(self, prompt: str, config: Optional[ModelConfig] = None) -> str:
        """
        Generate response using shared SDK.

        Args:
            prompt: Input prompt
            config: Optional model configuration

        Returns:
            Generated response
        """
        model_config = None
        if config:
            model_config = SDKModelConfig(
                model_name=config.model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

        response = await self.client.generate(prompt=prompt, config=model_config)
        return response

    async def health_check(self) -> bool:
        """
        Check if shared SDK client is healthy.

        Returns:
            True if healthy
        """
        return SDK_AVAILABLE and self.client is not None
