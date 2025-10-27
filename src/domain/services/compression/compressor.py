"""Compression service interface.

Following the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
"""

from src.domain.services.compression.strategies.keyword_compressor import (
    KeywordCompressor,
)
from src.domain.services.compression.strategies.truncation_compressor import (
    TruncationCompressor,
)
from src.domain.services.token_analyzer import TokenAnalyzer


class CompressionService:
    """
    Compression service with multiple strategies.

    Provides a simple interface for text compression
    using various strategies.
    """

    def __init__(self):
        """Initialize compression service."""
        self.token_analyzer = TokenAnalyzer()
        self.strategies = {
            "truncation": TruncationCompressor(self.token_analyzer),
            "keywords": KeywordCompressor(self.token_analyzer),
        }

    def compress(
        self, text: str, max_tokens: int, strategy: str = "truncation"
    ) -> dict:
        """
        Compress text using specified strategy.

        Args:
            text: Text to compress
            max_tokens: Maximum tokens allowed
            strategy: Compression strategy to use

        Returns:
            Dictionary with compression results

        Raises:
            ValueError: If strategy not found
        """
        if strategy not in self.strategies:
            available = ", ".join(self.strategies.keys())
            raise ValueError(f"Unknown strategy: {strategy}. Available: {available}")

        compressor = self.strategies[strategy]
        result = compressor.compress(text, max_tokens)

        return {
            "original_text": result.original_text,
            "compressed_text": result.compressed_text,
            "original_tokens": result.original_tokens,
            "compressed_tokens": result.compressed_tokens,
            "compression_ratio": result.compression_ratio.ratio,
            "method": result.method,
        }

    def get_available_strategies(self) -> list:
        """
        Get list of available compression strategies.

        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())
