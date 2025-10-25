"""
Text compression module for reducing token count while preserving meaning.

This module provides multiple compression strategies:
1. Truncation: Keep first and last sentences with middle portion
2. Keywords: Extract and keep only important keywords
3. Advanced strategies: Summarization, extractive, semantic chunking

Example:
    Basic usage with truncation strategy:
    
    ```python
    from core.text_compressor import SimpleTextCompressor
    from core.token_analyzer import SimpleTokenCounter
    from models.data_models import CompressionResult
    
    token_counter = SimpleTokenCounter()
    compressor = SimpleTextCompressor(token_counter)
    
    text = "This is a very long text that needs compression..."
    result = compressor.compress_by_truncation(text, max_tokens=100)
    print(f"Compressed: {result.compressed_text}")
    print(f"Ratio: {result.compression_ratio}")
    ```
    
    Using different compression strategies:
    
    ```python
    # Keywords strategy
    result = compressor.compress_by_keywords(text, max_tokens=100)
    
    # General compression (auto-selects best strategy)
    result = compressor.compress_text(text, max_tokens=100, strategy="truncation")
    ```
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

    Attributes:
        token_counter: Instance of token counter for counting tokens
        factory: Factory for creating compression strategy instances

    Example:
        ```python
        from core.text_compressor import SimpleTextCompressor
        from core.token_analyzer import SimpleTokenCounter
        from models.data_models import CompressionResult
        
        # Initialize compressor
        token_counter = SimpleTokenCounter()
        compressor = SimpleTextCompressor(token_counter)
        
        # Compress text using different strategies
        text = "This is a very long text that needs compression..."
        
        # Truncation strategy
        result = compressor.compress_by_truncation(text, max_tokens=100)
        
        # Keywords strategy  
        result = compressor.compress_by_keywords(text, max_tokens=100)
        
        # General compression
        result = compressor.compress_text(text, max_tokens=100, strategy="truncation")
        ```
    """

    def __init__(self, token_counter):
        """
        Initialize compressor with token counter.

        Args:
            token_counter: Instance of token counter for counting tokens

        Example:
            ```python
            from core.text_compressor import SimpleTextCompressor
            from core.token_analyzer import SimpleTokenCounter
            
            token_counter = SimpleTokenCounter()
            compressor = SimpleTextCompressor(token_counter)
            ```
        """
        self.token_counter = token_counter
        self.factory = CompressionStrategyFactory()

    def compress_by_truncation(
        self, text: str, max_tokens: int, model_name: str = "starcoder"
    ) -> CompressionResult:
        """
        Compress text by truncation strategy.

        Uses truncation strategy to compress text by keeping the beginning
        and end portions while removing the middle section. This preserves
        the most important information at the start and conclusion.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens for the compressed text
            model_name: Name of the model (default: "starcoder")

        Returns:
            CompressionResult: Result containing compressed text, token count, and ratio

        Example:
            ```python
            from core.text_compressor import SimpleTextCompressor
            from core.token_analyzer import SimpleTokenCounter
            
            token_counter = SimpleTokenCounter()
            compressor = SimpleTextCompressor(token_counter)
            
            text = "This is a very long text that needs compression..."
            result = compressor.compress_by_truncation(text, max_tokens=100)
            
            print(f"Original tokens: {result.original_tokens}")
            print(f"Compressed tokens: {result.compressed_tokens}")
            print(f"Compression ratio: {result.compression_ratio}")
            ```
        """
        compressor = self.factory.create(CompressionStrategy.TRUNCATION, self.token_counter)
        return compressor.compress(text, max_tokens, model_name)

    def compress_by_keywords(
        self, text: str, max_tokens: int, model_name: str = "starcoder"
    ) -> CompressionResult:
        """
        Compress text by extracting keywords.

        Uses keyword extraction strategy to compress text by identifying
        and keeping only the most important keywords and phrases. This
        preserves semantic meaning while significantly reducing token count.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens for the compressed text
            model_name: Name of the model (default: "starcoder")

        Returns:
            CompressionResult: Result containing compressed text, token count, and ratio

        Example:
            ```python
            from core.text_compressor import SimpleTextCompressor
            from core.token_analyzer import SimpleTokenCounter
            
            token_counter = SimpleTokenCounter()
            compressor = SimpleTextCompressor(token_counter)
            
            text = "Machine learning is a subset of artificial intelligence..."
            result = compressor.compress_by_keywords(text, max_tokens=50)
            
            print(f"Compressed text: {result.compressed_text}")
            print(f"Compression ratio: {result.compression_ratio}")
            ```
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

        Provides a unified interface for text compression with different
        strategies. Automatically selects the appropriate compression
        method based on the strategy parameter.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens for the compressed text
            model_name: Name of the model (default: "starcoder")
            strategy: Compression strategy ("truncation", "keywords", "extractive", "semantic")

        Returns:
            CompressionResult: Result containing compressed text, token count, and ratio

        Raises:
            ValueError: If strategy is not supported

        Example:
            ```python
            from core.text_compressor import SimpleTextCompressor
            from core.token_analyzer import SimpleTokenCounter
            
            token_counter = SimpleTokenCounter()
            compressor = SimpleTextCompressor(token_counter)
            
            text = "This is a very long text that needs compression..."
            
            # Use different strategies
            result1 = compressor.compress_text(text, max_tokens=100, strategy="truncation")
            result2 = compressor.compress_text(text, max_tokens=100, strategy="keywords")
            
            print(f"Truncation ratio: {result1.compression_ratio}")
            print(f"Keywords ratio: {result2.compression_ratio}")
            ```
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
