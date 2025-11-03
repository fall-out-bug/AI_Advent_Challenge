"""Protocol for LLM clients.

This protocol defines the interface for LLM clients.
Infrastructure layer implementations must conform to this protocol.
"""

from typing import Protocol, Optional


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients.

    Following Clean Architecture, this protocol is defined in domain layer
    while implementations reside in infrastructure layer.

    Methods:
        make_request: Make a request to the LLM
        check_availability: Check if model is available
        close: Close client resources
    """

    async def make_request(
        self,
        model_name: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Make a request to the LLM.

        Args:
            model_name: Name of the model to use
            prompt: Input prompt for the model
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            Model response text

        Raises:
            Exception: If LLM request fails
        """
        ...

    async def check_availability(self, model_name: str) -> bool:
        """Check if model is available.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is available, False otherwise
        """
        ...

    async def close(self) -> None:
        """Close client resources.

        Cleanup any open connections or resources.
        """
        ...

