"""Token counting service for test agent using Qwen tokenizer."""

from typing import Optional

try:
    import tiktoken
except ImportError:
    tiktoken = None  # type: ignore

from src.domain.test_agent.interfaces.token_counter import ITokenCounter
from src.infrastructure.logging import get_logger

# Qwen uses tiktoken with cl100k_base encoding (same as GPT-4)
QWEN_ENCODING = "cl100k_base"

# Safety buffer: use 90% of max tokens to account for discrepancies
SAFETY_BUFFER = 0.9


class TokenCounter:
    """
    Token counting service using Qwen-compatible tokenization.

    Purpose:
        Counts tokens in code strings to ensure chunks fit within context window.
        Uses tiktoken with cl100k_base encoding (Qwen-compatible).

    Example:
        >>> counter = TokenCounter()
        >>> count = counter.count_tokens("def hello(): pass")
        >>> count > 0
        True
    """

    def __init__(self) -> None:
        """Initialize token counter with Qwen tokenizer."""
        self.logger = get_logger("test_agent.token_counter")
        self._tiktoken_encoding: Optional[tiktoken.Encoding] = None

        # Initialize Qwen tokenizer (tiktoken with cl100k_base)
        if tiktoken is not None:
            try:
                self._tiktoken_encoding = tiktoken.get_encoding(QWEN_ENCODING)
                self.logger.debug(
                    f"Using tiktoken with Qwen-compatible encoding: {QWEN_ENCODING}"
                )
            except Exception as e:
                self.logger.warning(
                    f"Failed to load tiktoken encoding: {e}. "
                    "Using character-based approximation"
                )
        else:
            self.logger.warning(
                "tiktoken not available. Using character-based approximation"
            )

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: Input text to count tokens for.

        Returns:
            Number of tokens in the text.

        Example:
            >>> counter = TokenCounter()
            >>> counter.count_tokens("Hello world")
            2
        """
        if not text:
            return 0

        # Use Qwen tokenizer (tiktoken with cl100k_base)
        if self._tiktoken_encoding is not None:
            try:
                return len(self._tiktoken_encoding.encode(text))
            except Exception as e:
                self.logger.warning(f"Token counting failed: {e}. Using approximation")
                return self._approximate_tokens(text)

        return self._approximate_tokens(text)

    def estimate_prompt_size(self, code: str, system_prompt: str) -> int:
        """Estimate total prompt size including system prompt.

        Args:
            code: Code content to include in prompt.
            system_prompt: System prompt to include.

        Returns:
            Estimated total token count for the prompt.

        Example:
            >>> counter = TokenCounter()
            >>> size = counter.estimate_prompt_size("def test(): pass", "Generate tests")
            >>> size > 0
            True
        """
        code_tokens = self.count_tokens(code)
        system_tokens = self.count_tokens(system_prompt)

        # Add overhead for prompt formatting (approximately 10 tokens)
        formatting_overhead = 10

        total = code_tokens + system_tokens + formatting_overhead

        # Apply safety buffer (90% of max to account for discrepancies)
        return int(total / SAFETY_BUFFER)

    def _approximate_tokens(self, text: str) -> int:
        """Approximate token count using character-based heuristic.

        Args:
            text: Input text.

        Returns:
            Approximate token count (4 characters per token for Qwen/cl100k_base).
        """
        # Fallback: approximate 1 token = 4 characters
        # This is a rough estimate for Qwen/cl100k_base encoding with English/Python code
        return max(1, len(text) // 4)
