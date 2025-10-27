"""
Token Service - Business logic for token operations.

This module contains the core business logic for token counting,
text compression, and related operations, separated from HTTP handling.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.accurate_token_counter import AccurateTokenCounter
from core.advanced_compressor import (
    ExtractiveCompressor,
    SemanticChunker,
    SummarizationCompressor,
)
from core.interfaces.protocols import TokenCounterProtocol
from models.data_models import CompressionResult, TokenInfo
from utils.logging import LoggerFactory


@dataclass
class TokenCountRequest:
    """Request for token counting operation."""

    text: str
    model_name: str = "starcoder"


@dataclass
class TokenCountResponse:
    """Response from token counting operation."""

    count: int
    model_name: str
    estimated_cost: float = 0.0


@dataclass
class CompressionRequest:
    """Request for text compression operation."""

    text: str
    max_tokens: int
    strategy: str
    model_name: str = "starcoder"


@dataclass
class CompressionResponse:
    """Response from text compression operation."""

    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: str


@dataclass
class BatchTokenCountRequest:
    """Request for batch token counting operation."""

    texts: List[str]
    model_name: str = "starcoder"


@dataclass
class BatchTokenCountResponse:
    """Response from batch token counting operation."""

    results: List[TokenCountResponse]


class TokenService:
    """
    Business logic service for token operations.

    This service handles the core business logic for token counting,
    text compression, and related operations without HTTP concerns.
    """

    def __init__(self, token_counter: Optional[TokenCounterProtocol] = None):
        """
        Initialize the token service.

        Args:
            token_counter: Optional token counter implementation.
                          If None, creates AccurateTokenCounter.
        """
        self.logger = LoggerFactory.create_logger(__name__)

        # Initialize token counter
        if token_counter is None:
            self.token_counter = AccurateTokenCounter()
        else:
            self.token_counter = token_counter

        # Initialize compressors
        self.extractive_compressor = ExtractiveCompressor(self.token_counter)
        self.semantic_chunker = SemanticChunker(self.token_counter)

        self.logger.info("TokenService initialized successfully")

    async def count_tokens(self, request: TokenCountRequest) -> TokenCountResponse:
        """
        Count tokens in text using accurate tokenizers.

        Args:
            request: Token counting request

        Returns:
            Token counting response

        Raises:
            ValueError: If text is empty or invalid
            RuntimeError: If token counting fails
        """
        self.logger.debug(f"Counting tokens for model: {request.model_name}")

        if not request.text.strip():
            raise ValueError("Text cannot be empty")

        try:
            token_info = self.token_counter.count_tokens(
                request.text, request.model_name
            )

            response = TokenCountResponse(
                count=token_info.count,
                model_name=token_info.model_name,
                estimated_cost=token_info.estimated_cost,
            )

            self.logger.info(f"Token count completed: {response.count} tokens")
            return response

        except Exception as e:
            self.logger.error(f"Token counting failed: {e}")
            raise RuntimeError(f"Failed to count tokens: {e}") from e

    async def batch_count_tokens(
        self, request: BatchTokenCountRequest
    ) -> BatchTokenCountResponse:
        """
        Count tokens for multiple texts in batch.

        Args:
            request: Batch token counting request

        Returns:
            Batch token counting response

        Raises:
            ValueError: If texts list is empty
            RuntimeError: If batch processing fails
        """
        self.logger.debug(f"Batch counting tokens for {len(request.texts)} texts")

        if not request.texts:
            raise ValueError("Texts list cannot be empty")

        try:
            results = []
            for i, text in enumerate(request.texts):
                if not text.strip():
                    self.logger.warning(f"Skipping empty text at index {i}")
                    continue

                token_request = TokenCountRequest(
                    text=text, model_name=request.model_name
                )
                token_response = await self.count_tokens(token_request)
                results.append(token_response)

            response = BatchTokenCountResponse(results=results)
            self.logger.info(f"Batch token counting completed: {len(results)} results")
            return response

        except Exception as e:
            self.logger.error(f"Batch token counting failed: {e}")
            raise RuntimeError(f"Failed to process batch token counting: {e}") from e

    async def compress_text(self, request: CompressionRequest) -> CompressionResponse:
        """
        Compress text using specified strategy.

        Args:
            request: Text compression request

        Returns:
            Text compression response

        Raises:
            ValueError: If text is empty or strategy is invalid
            RuntimeError: If compression fails
        """
        self.logger.debug(f"Compressing text with strategy: {request.strategy}")

        if not request.text.strip():
            raise ValueError("Text cannot be empty")

        if request.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")

        try:
            result = await self._apply_compression_strategy(request)

            response = CompressionResponse(
                original_text=result.original_text,
                compressed_text=result.compressed_text,
                original_tokens=result.original_tokens,
                compressed_tokens=result.compressed_tokens,
                compression_ratio=result.compression_ratio,
                strategy_used=result.strategy_used,
            )

            self.logger.info(
                f"Text compression completed: {response.compression_ratio:.2f} ratio"
            )
            return response

        except Exception as e:
            self.logger.error(f"Text compression failed: {e}")
            raise RuntimeError(f"Failed to compress text: {e}") from e

    async def preview_compression(self, request: CompressionRequest) -> Dict[str, Any]:
        """
        Get preview of compression results for all available strategies.

        Args:
            request: Text compression request

        Returns:
            Dictionary with preview results for each strategy

        Raises:
            ValueError: If text is empty
            RuntimeError: If preview generation fails
        """
        self.logger.debug("Generating compression preview")

        if not request.text.strip():
            raise ValueError("Text cannot be empty")

        try:
            results = {}
            strategies = ["extractive", "semantic"]

            for strategy in strategies:
                try:
                    strategy_request = CompressionRequest(
                        text=request.text,
                        max_tokens=request.max_tokens,
                        model_name=request.model_name,
                        strategy=strategy,
                    )

                    compression_result = await self.compress_text(strategy_request)

                    results[strategy] = {
                        "compression_ratio": compression_result.compression_ratio,
                        "compressed_tokens": compression_result.compressed_tokens,
                        "preview": self._create_preview(
                            compression_result.compressed_text
                        ),
                    }

                except Exception as e:
                    self.logger.warning(f"Strategy {strategy} failed: {e}")
                    results[strategy] = {"error": str(e)}

            self.logger.info("Compression preview generated successfully")
            return results

        except Exception as e:
            self.logger.error(f"Compression preview failed: {e}")
            raise RuntimeError(f"Failed to generate compression preview: {e}") from e

    def get_available_models(self) -> List[str]:
        """
        Get list of available models for token counting.

        Returns:
            List of available model names
        """
        return self.token_counter.get_available_models()

    def get_available_strategies(self) -> Dict[str, str]:
        """
        Get list of available compression strategies with descriptions.

        Returns:
            Dictionary mapping strategy names to descriptions
        """
        return {
            "strategies": ["extractive", "semantic"],
            "descriptions": {
                "extractive": "TF-IDF based extractive summarization",
                "semantic": "Semantic chunking with importance scoring",
            },
        }

    async def _apply_compression_strategy(
        self, request: CompressionRequest
    ) -> CompressionResult:
        """
        Apply the specified compression strategy.

        Args:
            request: Compression request

        Returns:
            Compression result

        Raises:
            ValueError: If strategy is not supported
        """
        if request.strategy == "extractive":
            return self.extractive_compressor.compress(
                request.text, request.max_tokens, request.model_name
            )
        elif request.strategy == "semantic":
            return self.semantic_chunker.compress(
                request.text, request.max_tokens, request.model_name
            )
        else:
            available_strategies = list(self.get_available_strategies()["strategies"])
            raise ValueError(
                f"Unsupported strategy: {request.strategy}. Available: {available_strategies}"
            )

    def _create_preview(self, text: str, max_length: int = 200) -> str:
        """
        Create a preview of compressed text.

        Args:
            text: Compressed text
            max_length: Maximum length of preview

        Returns:
            Preview text with ellipsis if truncated
        """
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
