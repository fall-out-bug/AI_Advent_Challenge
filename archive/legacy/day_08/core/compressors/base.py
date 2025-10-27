"""
Base compressor class with template method pattern.

Provides common compression logic and abstract methods
for specific compression strategies.

Example:
    Creating a custom compressor:
    
    ```python
    from core.compressors.base import BaseCompressor
    from core.interfaces.protocols import TokenCounterProtocol
    from models.data_models import CompressionResult
    
    class CustomCompressor(BaseCompressor):
        def _compress_impl(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
            # Implement custom compression logic
            compressed_text = self._custom_compression(text, max_tokens)
            return self._build_result(text, compressed_text, model_name)
        
        def _custom_compression(self, text: str, max_tokens: int) -> str:
            # Custom compression implementation
            return text[:max_tokens]  # Simple truncation example
    ```
"""

from abc import ABC, abstractmethod
from typing import Optional

from core.interfaces.protocols import CompressorProtocol, TokenCounterProtocol
from models.data_models import CompressionResult


class BaseCompressor(ABC, CompressorProtocol):
    """
    Base compressor with template method pattern.

    Provides common compression logic and delegates
    specific compression strategies to subclasses.

    This class implements the Template Method pattern, providing
    a common structure for compression while allowing subclasses
    to implement specific compression algorithms.

    Attributes:
        token_counter (TokenCounterProtocol): Token counter for counting tokens

    Example:
        ```python
        from core.compressors.base import BaseCompressor
        from core.token_analyzer import SimpleTokenCounter
        from models.data_models import CompressionResult

        class MyCompressor(BaseCompressor):
            def _compress_impl(self, text: str, max_tokens: int, model_name: str) -> CompressionResult:
                # Implement compression logic
                compressed = text[:max_tokens * 4]  # Rough character limit
                return self._build_result(text, compressed, model_name)

        # Use the compressor
        token_counter = SimpleTokenCounter()
        compressor = MyCompressor(token_counter)
        result = compressor.compress("Long text...", max_tokens=100)
        ```
    """

    def __init__(self, token_counter: TokenCounterProtocol):
        """
        Initialize base compressor.

        Args:
            token_counter: Token counter instance
        """
        self.token_counter = token_counter

    def compress(
        self, text: str, max_tokens: int, model_name: str = "starcoder"
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
        original_tokens = self._count_original_tokens(text, model_name)

        if not self._should_compress(original_tokens, max_tokens):
            return self._no_compression_result(text, original_tokens, model_name)

        compressed_text = self._perform_compression(text, max_tokens, model_name)
        return self._build_result(text, compressed_text, model_name)

    def _count_original_tokens(self, text: str, model_name: str) -> int:
        """Count tokens in original text."""
        return self.token_counter.count_tokens(text, model_name).count

    def _should_compress(self, original_tokens: int, max_tokens: int) -> bool:
        """Check if compression is needed."""
        return original_tokens > max_tokens

    def _no_compression_result(
        self, text: str, original_tokens: int, model_name: str
    ) -> CompressionResult:
        """Create result when no compression is needed."""
        return CompressionResult(
            original_text=text,
            compressed_text=text,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            compression_ratio=1.0,
            strategy_used="no_compression",
        )

    def _build_result(
        self, original_text: str, compressed_text: str, model_name: str
    ) -> CompressionResult:
        """Build final compression result."""
        original_tokens = self._count_original_tokens(original_text, model_name)
        compressed_tokens = self._count_original_tokens(compressed_text, model_name)

        return CompressionResult(
            original_text=original_text,
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens
            if original_tokens > 0
            else 1.0,
            strategy_used=self._get_strategy_name(),
        )

    @abstractmethod
    def _perform_compression(self, text: str, max_tokens: int, model_name: str) -> str:
        """
        Perform actual compression.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            str: Compressed text
        """
        pass

    @abstractmethod
    def _get_strategy_name(self) -> str:
        """
        Get strategy name for result.

        Returns:
            str: Strategy name
        """
        pass
