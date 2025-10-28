"""Base compressor with template method pattern."""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.value_objects.compression_result import (
    CompressionRatio,
    CompressionResult,
)


class BaseCompressor(ABC):
    """Base compressor with template method pattern."""

    def __init__(self, token_analyzer):
        """Initialize base compressor."""
        self.token_analyzer = token_analyzer

    def compress(self, text: str, max_tokens: int, model_name: str = "default") -> CompressionResult:
        """Template method for compression."""
        original_tokens = self._count_original_tokens(text)

        if not self._should_compress(original_tokens, max_tokens):
            return self._no_compression_result(text, original_tokens)

        compressed_text = self._perform_compression(text, max_tokens)
        return self._build_result(text, compressed_text, original_tokens)

    def _count_original_tokens(self, text: str) -> int:
        """Count tokens in original text."""
        return int(self.token_analyzer.count_tokens(text))

    def _should_compress(self, original_tokens: int, max_tokens: int) -> bool:
        """Check if compression is needed."""
        return original_tokens > max_tokens

    def _no_compression_result(self, text: str, original_tokens: int) -> CompressionResult:
        """Create result when no compression is needed."""
        compression_ratio = CompressionRatio(
            original_size=original_tokens, compressed_size=original_tokens, ratio=1.0
        )

        return CompressionResult(
            compression_ratio=compression_ratio, method="no_compression"
        )

    def _build_result(self, original_text: str, compressed_text: str, original_tokens: int) -> CompressionResult:
        """Build final compression result."""
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
        """Perform actual compression."""
        pass

    @abstractmethod
    def _get_strategy_name(self) -> str:
        """Get strategy name for result."""
        pass
