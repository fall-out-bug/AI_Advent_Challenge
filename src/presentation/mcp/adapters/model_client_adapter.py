"""Model client adapter for agent compatibility."""

from typing import Any

from shared_package.clients.unified_client import UnifiedModelClient


class ModelClientAdapter:
    """Adapter to make UnifiedModelClient compatible with BaseAgent interface.

    Following the Adapter pattern from scripts/day_07_workflow.py.
    """

    def __init__(self, unified_client: UnifiedModelClient, model_name: str = "mistral"):
        """Initialize adapter.

        Args:
            unified_client: UnifiedModelClient instance
            model_name: Name of the model to use
        """
        self.unified_client = unified_client
        self.model_name = model_name

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Generate response compatible with BaseAgent interface.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens
            temperature: Temperature

        Returns:
            Dictionary with response and tokens
        """
        response = await self.unified_client.make_request(
            model_name=self.model_name,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return {
            "response": response.response,
            "total_tokens": response.total_tokens,
            "input_tokens": response.input_tokens,
            "response_tokens": response.response_tokens,
        }
