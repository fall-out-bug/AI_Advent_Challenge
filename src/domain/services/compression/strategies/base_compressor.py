"""Base compressor with template method pattern.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.value_objects.compression_result import (
    CompressionRatio,
    CompressionResult,
)


class BaseCompressor(ABC):
    """
    Base compressor with template method pattern.

    Provides common compression logic and delegates
    specific compression strategies to subclasses.

    Following the Template Method pattern for clear,
    maintainable code.
    """

    def __init__(self, token_analyzer):
        """
        Initialize base compressor.

        Args:
            token_analyzer: Token analyzer instance
        """
        self.token_analyzer = token_analyzer

    def compress(
        self, text: str, max_tokens: int, model_name: str = "default"
    ) -> CompressionResult:
        """
        Template method for compression.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            CompressionResult: Result of compression operation
        """
        original_tokens = self._count_original_tokens(text)

        if not self._should_compress(original_tokens, max_tokens):
            return self._no_compression_result(text, original_tokens)

        compressed_text = self._perform_compression(text, max_tokens)
        return self._build_result(text, compressed_text, original_tokens)

    def _count_original_tokens(self, text: str) -> int:
        """
        Count tokens in original text.

        Args:
            text: Text to count tokens in

        Returns:
            Number of tokens
        """
        return int(self.token_analyzer.count_tokens(text))

    def _should_compress(self, original_tokens: int, max_tokens: int) -> bool:
        """
        Check if compression is needed.

        Args:
            original_tokens: Number of tokens in original text
            max_tokens: Maximum allowed tokens

        Returns:
            True if compression is needed
        """
        return original_tokens > max_tokens

    def _no_compression_result(
        self, text: str, original_tokens: int
    ) -> CompressionResult:
        """
        Create result when no compression is needed.

        Args:
            text: Original text
            original_tokens: Number of tokens

        Returns:
            CompressionResult indicating no compression was performed
        """
        compression_ratio = CompressionRatio(
            original_size=original_tokens, compressed_size=original_tokens, ratio=1.0
        )

        return CompressionResult(
            compression_ratio=compression_ratio, method="no_compression"
        )

    def _build_result(
        self, original_text: str, compressed_text: str, original_tokens: int
    ) -> CompressionResult:
        """
        Build final compression result.

        Args:
            original_text: Original text
            compressed_text: Compressed text
            original_tokens: Number of tokens in original

        Returns:
            CompressionResult with compression details
        """
        compressed_tokens = self._count_original_tokens(compressed_text)
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        compression_ratio = CompressionRatio(
            original_size=original_tokens,
            compressed_size=compressed_tokens,
            ratio=ratio,
        )

        return CompressionResult(
            compression_ratio=compression_ratio,
            method=self._get_strategy_name(),
            metadata={
                "original_text": original_text,
                "compressed_text": compressed_text,
            },
        )

    @abstractmethod
    def _perform_compression(self, text: str, max_tokens: int) -> str:
        """
        Perform actual compression.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens

        Returns:
            Compressed text
        """
        pass

    @abstractmethod
    def _get_strategy_name(self) -> str:
        """
        Get strategy name for result.

        Returns:
            Strategy name
        """
        pass
