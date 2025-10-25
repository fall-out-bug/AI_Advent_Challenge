"""
Text compression module for reducing token count while preserving meaning.

This module provides multiple compression strategies:
1. Truncation: Keep first and last sentences with middle portion
2. Keywords: Extract and keep only important keywords
3. Advanced strategies: Summarization, extractive, semantic chunking
"""

import re
from typing import Optional

from core.advanced_compressor import (
    ExtractiveCompressor,
    SemanticChunker,
    SummarizationCompressor,
)
from core.compressors import CompressionStrategy, CompressionStrategyFactory
from models.data_models import CompressionResult


class SimpleTextCompressor:
    """
    Simple text compressor with basic strategies.

    Provides methods to compress text while attempting to preserve
    the most important information for model processing.
    
    This class acts as a facade for the new compression strategies
    while maintaining backward compatibility.
    """

    def __init__(self, token_counter):
        """
        Initialize compressor with token counter.

        Args:
            token_counter: Instance of token counter
        """
        self.token_counter = token_counter
        self.factory = CompressionStrategyFactory()

    def compress_by_truncation(
        self, text: str, max_tokens: int, model_name: str = "starcoder"
    ) -> CompressionResult:
        """
        Compress text by truncation strategy.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            CompressionResult: Result of compression operation
        """
        compressor = self.factory.create(CompressionStrategy.TRUNCATION, self.token_counter)
        return compressor.compress(text, max_tokens, model_name)

    def compress_by_keywords(
        self, text: str, max_tokens: int, model_name: str = "starcoder"
    ) -> CompressionResult:
        """
        Compress text by extracting keywords.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            CompressionResult: Result of compression operation
        """
        compressor = self.factory.create(CompressionStrategy.KEYWORDS, self.token_counter)
        return compressor.compress(text, max_tokens, model_name)

    def compress_text(
        self,
        text: str,
        max_tokens: int,
        model_name: str = "starcoder",
        strategy: str = "truncation",
    ) -> CompressionResult:
        """
        Compress text using specified strategy.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            strategy: Compression strategy ("truncation" or "keywords")

        Returns:
            CompressionResult: Result of compression operation

        Raises:
            ValueError: If strategy is not supported
        """
        if not self.factory.is_strategy_supported(strategy):
            available = self.factory.get_available_strategies()
            raise ValueError(f"Unsupported compression strategy: {strategy}. Available: {available}")
        
        compression_strategy = CompressionStrategy(strategy)
        compressor = self.factory.create(compression_strategy, self.token_counter)
        return compressor.compress(text, max_tokens, model_name)

    def get_compression_preview(
        self, text: str, max_tokens: int, model_name: str = "starcoder"
    ) -> dict:
        """
        Get preview of compression results for both strategies.

        Args:
            text: Input text
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            dict: Preview results for both strategies
        """
        truncation_result = self.compress_by_truncation(text, max_tokens, model_name)
        keywords_result = self.compress_by_keywords(text, max_tokens, model_name)

        return {
            "truncation": {
                "compression_ratio": truncation_result.compression_ratio,
                "compressed_tokens": truncation_result.compressed_tokens,
                "preview": truncation_result.compressed_text[:200] + "...",
            },
            "keywords": {
                "compression_ratio": keywords_result.compression_ratio,
                "compressed_tokens": keywords_result.compressed_tokens,
                "preview": keywords_result.compressed_text[:200] + "...",
            },
        }


class AdvancedTextCompressor:
    """
    Advanced text compressor with multiple strategies.

    Provides access to all compression strategies including
    LLM-based summarization, extractive summarization, and semantic chunking.
    """

    def __init__(self, token_counter, model_client=None):
        """
        Initialize advanced compressor.

        Args:
            token_counter: Token counter instance
            model_client: Model client for LLM-based strategies (optional)
        """
        self.token_counter = token_counter
        self.model_client = model_client

        # Initialize strategies
        self.strategies = {
            "truncation": SimpleTextCompressor(token_counter),
            "keywords": SimpleTextCompressor(token_counter),
            "extractive": ExtractiveCompressor(token_counter),
            "semantic": SemanticChunker(token_counter),
        }

        # Add LLM-based strategies if model client is available
        if model_client:
            self.strategies["summarization"] = SummarizationCompressor(
                model_client, token_counter
            )

    async def compress(
        self, text: str, max_tokens: int, model_name: str, strategy: str
    ) -> CompressionResult:
        """
        Compress using specified strategy.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            strategy: Compression strategy name

        Returns:
            CompressionResult: Result of compression

        Raises:
            ValueError: If strategy is not supported
        """
        if strategy not in self.strategies:
            available = ", ".join(self.strategies.keys())
            raise ValueError(f"Unknown strategy: {strategy}. Available: {available}")

        compressor = self.strategies[strategy]

        # Handle async strategies
        if strategy == "summarization":
            return await compressor.compress(text, max_tokens, model_name)
        else:
            return compressor.compress(text, max_tokens, model_name)

    def get_available_strategies(self) -> list[str]:
        """
        Get list of available compression strategies.

        Returns:
            list[str]: List of strategy names
        """
        return list(self.strategies.keys())

    async def get_compression_preview(
        self, text: str, max_tokens: int, model_name: str = "starcoder"
    ) -> dict:
        """
        Get preview of all available compression strategies.

        Args:
            text: Input text
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            dict: Preview results for all strategies
        """
        results = {}

        for strategy_name in self.strategies.keys():
            try:
                result = await self.compress(
                    text, max_tokens, model_name, strategy_name
                )
                results[strategy_name] = {
                    "compression_ratio": result.compression_ratio,
                    "compressed_tokens": result.compressed_tokens,
                    "preview": result.compressed_text[:200] + "..."
                    if len(result.compressed_text) > 200
                    else result.compressed_text,
                }
            except Exception as e:
                results[strategy_name] = {
                    "error": str(e),
                    "compression_ratio": 1.0,
                    "compressed_tokens": self.token_counter.count_tokens(
                        text, model_name
                    ).count,
                    "preview": "Error occurred",
                }

        return results
