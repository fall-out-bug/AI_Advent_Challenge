"""Protocol for token counting services."""

from typing import Protocol


class ITokenCounter(Protocol):
    """Protocol for token counting services.

    Purpose:
        Defines the interface for token counting services used by test agent.
        Infrastructure layer implementations must conform to this protocol.

    Methods:
        count_tokens: Count tokens in a text string
        estimate_prompt_size: Estimate total prompt size including system prompt
    """

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: Input text to count tokens for.

        Returns:
            Number of tokens in the text.
        """
        ...

    def estimate_prompt_size(self, code: str, system_prompt: str) -> int:
        """Estimate total prompt size including system prompt.

        Args:
            code: Code content to include in prompt.
            system_prompt: System prompt to include.

        Returns:
            Estimated total token count for the prompt.
        """
        ...
