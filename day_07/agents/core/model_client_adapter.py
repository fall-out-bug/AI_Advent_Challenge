"""Adapter for integrating UnifiedModelClient with agent architecture."""

import os
import sys
from typing import Any, Dict, Optional

# Add shared SDK to path - handle both local development and Docker
shared_path = os.path.join(os.path.dirname(__file__), "../../../shared")
docker_shared_path = "/shared"

if os.path.exists(shared_path):
    sys.path.append(shared_path)
elif os.path.exists(docker_shared_path):
    sys.path.append(docker_shared_path)
else:
    # Try to find shared package in Python path
    try:
        import shared_package
    except ImportError:
        raise ImportError(
            "Could not find shared SDK. Please ensure it's installed or available in the path."
        )

from shared_package.clients.base_client import ModelResponse
from shared_package.clients.unified_client import UnifiedModelClient
from shared_package.exceptions.model_errors import (
    ModelConfigurationError,
    ModelConnectionError,
    ModelRequestError,
    ModelTimeoutError,
)


class ModelClientAdapter:
    """
    Adapter for UnifiedModelClient.

    Following Dependency Inversion Principle: agents depend on
    abstraction (this adapter) rather than concrete implementation.
    """

    def __init__(self, model_name: str = "starcoder", timeout: float = 600.0):
        """
        Initialize the model client adapter.

        Args:
            model_name: Name of the model to use
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.client = UnifiedModelClient(timeout=timeout)

    async def make_request(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> Dict[str, Any]:
        """
        Make request to model through SDK.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            Dict containing response data

        Raises:
            Exception: If model request fails
        """
        try:
            response: ModelResponse = await self.client.make_request(
                model_name=self.model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return {
                "response": response.response,
                "input_tokens": response.input_tokens,
                "response_tokens": response.response_tokens,
                "total_tokens": response.total_tokens,
            }
        except (ModelConnectionError, ModelRequestError, ModelTimeoutError) as e:
            raise Exception(f"Model request failed: {str(e)}")

    async def check_availability(self) -> bool:
        """
        Check if model is available.

        Returns:
            True if model is available
        """
        return await self.client.check_availability(self.model_name)

    async def close(self) -> None:
        """Close client resources."""
        await self.client.close()
