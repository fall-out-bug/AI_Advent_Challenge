"""
Client for Token Analysis ML Service.

This client provides a clean interface to interact with the ML service
running in Docker container, handling heavy operations like accurate
token counting and advanced compression.
"""

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from models.data_models import CompressionResult, TokenInfo
from utils.retry import ResilientClient, RetryConfig, CircuitBreakerConfig
from core.validators import RequestValidator
from utils.logging import LoggerFactory


class TokenAnalysisClient:
    """
    Client for Token Analysis ML Service.

    Provides methods to interact with the ML service running in Docker
    for accurate token counting and advanced compression strategies.
    """

    def __init__(self, base_url: str = "http://localhost:8004"):
        """
        Initialize client with retry and circuit breaker.

        Args:
            base_url: Base URL of the ML service
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Configure retry and circuit breaker
        retry_config = RetryConfig(max_attempts=3, base_delay=1.0)
        cb_config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
        self.resilient_client = ResilientClient(retry_config, cb_config)

    async def _execute_with_resilience(self, func, *args, **kwargs):
        """
        Execute HTTP call with retry and circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        return await self.resilient_client.execute(func, *args, **kwargs)

    async def _make_get_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make GET request to ML service.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Response data
        """
        response = await self.client.get(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()

    async def _make_post_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make POST request to ML service.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response data
        """
        response = await self.client.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the ML service is healthy.

        Returns:
            Dict with health status and available models
        """
        try:
            return await self._execute_with_resilience(self._make_get_request, "/health")
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            raise ConnectionError(f"Cannot connect to ML service: {e}")

    async def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """
        Count tokens using accurate HuggingFace tokenizers.

        Args:
            text: Text to count tokens for
            model_name: Name of the model

        Returns:
            TokenInfo with accurate token count
        """
        self._validate_count_tokens_input(text, model_name)
        response_data = await self._execute_count_request(text, model_name)
        return self._parse_token_info(response_data)

    def _validate_count_tokens_input(self, text: str, model_name: str) -> None:
        """Validate input parameters for count_tokens."""
        RequestValidator.validate_text(text)
        RequestValidator.validate_model_name(model_name)

    async def _execute_count_request(self, text: str, model_name: str) -> Dict[str, Any]:
        """Execute count tokens request."""
        data = {"text": text, "model_name": model_name}
        return await self._execute_with_resilience(
            self._make_post_request, "/count-tokens", data
        )

    def _parse_token_info(self, data: Dict[str, Any]) -> TokenInfo:
        """Parse response data into TokenInfo."""
        return TokenInfo(
            count=data["count"],
            estimated_cost=data["estimated_cost"],
            model_name=data["model_name"],
        )

    async def count_tokens_batch(
        self, texts: List[str], model_name: str = "starcoder"
    ) -> List[TokenInfo]:
        """
        Count tokens for multiple texts in batch.

        Args:
            texts: List of texts to count tokens for
            model_name: Name of the model

        Returns:
            List of TokenInfo objects
        """
        self._validate_batch_input(texts, model_name)
        response_data = await self._execute_batch_request(texts, model_name)
        return self._parse_batch_results(response_data)

    def _validate_batch_input(self, texts: List[str], model_name: str) -> None:
        """Validate input for batch operation."""
        RequestValidator.validate_texts_list(texts)
        RequestValidator.validate_model_name(model_name)

    async def _execute_batch_request(self, texts: List[str], model_name: str) -> Dict[str, Any]:
        """Execute batch count tokens request."""
        data = {"texts": texts, "model_name": model_name}
        return await self._execute_with_resilience(
            self._make_post_request, "/count-tokens-batch", data
        )

    def _parse_batch_results(self, data: Dict[str, Any]) -> List[TokenInfo]:
        """Parse batch response data."""
        return [
            TokenInfo(
                count=result["count"],
                estimated_cost=result["estimated_cost"],
                model_name=result["model_name"],
            )
            for result in data["results"]
        ]

    async def compress_text(
        self,
        text: str,
        max_tokens: int,
        model_name: str = "starcoder",
        strategy: str = "extractive",
    ) -> CompressionResult:
        """
        Compress text using advanced strategies.

        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            strategy: Compression strategy ("extractive" or "semantic")

        Returns:
            CompressionResult with compression details
        """
        self._validate_compression_input(text, max_tokens, model_name, strategy)
        response_data = await self._execute_compression_request(text, max_tokens, model_name, strategy)
        return self._parse_compression_result(response_data)

    def _validate_compression_input(self, text: str, max_tokens: int, model_name: str, strategy: str) -> None:
        """Validate input for compression."""
        RequestValidator.validate_text(text)
        RequestValidator.validate_max_tokens(max_tokens)
        RequestValidator.validate_model_name(model_name)
        RequestValidator.validate_strategy(strategy)

    async def _execute_compression_request(
        self, text: str, max_tokens: int, model_name: str, strategy: str
    ) -> Dict[str, Any]:
        """Execute compression request."""
        data = {
            "text": text,
            "max_tokens": max_tokens,
            "model_name": model_name,
            "strategy": strategy,
        }
        return await self._execute_with_resilience(
            self._make_post_request, "/compress-text", data
        )

    def _parse_compression_result(self, data: Dict[str, Any]) -> CompressionResult:
        """Parse compression response data."""
        return CompressionResult(
            original_text=data["original_text"],
            compressed_text=data["compressed_text"],
            original_tokens=data["original_tokens"],
            compressed_tokens=data["compressed_tokens"],
            compression_ratio=data["compression_ratio"],
            strategy_used=data["strategy_used"],
        )

    async def preview_compression(
        self, text: str, max_tokens: int, model_name: str = "starcoder"
    ) -> Dict[str, Any]:
        """
        Get preview of compression results for all strategies.

        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            Dict with preview results for each strategy
        """
        RequestValidator.validate_text(text)
        RequestValidator.validate_max_tokens(max_tokens)
        RequestValidator.validate_model_name(model_name)
        
        data = {
            "text": text,
            "max_tokens": max_tokens,
            "model_name": model_name,
            "strategy": "extractive",  # Not used in preview
        }
        
        try:
            return await self._execute_with_resilience(
                self._make_post_request, "/preview-compression", data
            )
        except Exception as e:
            self.logger.error("preview_compression_failed", error=str(e))
            raise ConnectionError(f"Error getting compression preview: {e}")

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models.

        Returns:
            List of available model names
        """
        try:
            data = await self._execute_with_resilience(
                self._make_get_request, "/available-models"
            )
            return data["models"]
        except Exception as e:
            self.logger.error("get_available_models_failed", error=str(e))
            raise ConnectionError(f"Error getting available models: {e}")

    async def get_available_strategies(self) -> Dict[str, str]:
        """
        Get list of available compression strategies.

        Returns:
            Dict mapping strategy names to descriptions
        """
        try:
            data = await self._execute_with_resilience(
                self._make_get_request, "/available-strategies"
            )
            return data["descriptions"]
        except Exception as e:
            self.logger.error("get_available_strategies_failed", error=str(e))
            raise ConnectionError(f"Error getting available strategies: {e}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class HybridTokenCounter:
    """
    Hybrid token counter that uses ML service when available,
    falls back to simple estimation when service is unavailable.
    """

    def __init__(
        self, ml_client: Optional[TokenAnalysisClient] = None, fallback_counter=None
    ):
        """
        Initialize hybrid counter.

        Args:
            ml_client: ML service client (optional)
            fallback_counter: Fallback counter for when ML service is unavailable
        """
        self.ml_client = ml_client
        self.fallback_counter = fallback_counter
        self._service_available = None
        self.logger = LoggerFactory.create_logger(__name__)

    async def _check_service_availability(self) -> bool:
        """Check if ML service is available."""
        if self._service_available is not None:
            return self._service_available

        if self.ml_client is None:
            self._service_available = False
            return False

        try:
            await self.ml_client.health_check()
            self._service_available = True
            return True
        except Exception:
            self._service_available = False
            return False

    async def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """
        Count tokens using ML service if available, fallback otherwise.

        Args:
            text: Text to count tokens for
            model_name: Name of the model

        Returns:
            TokenInfo with token count
        """
        if await self._check_service_availability():
            try:
                return await self.ml_client.count_tokens(text, model_name)
            except Exception as e:
                self.logger.warning("ml_service_error", error=str(e), operation="count_tokens")

        # Fallback to simple estimation
        if self.fallback_counter is None:
            raise RuntimeError("No fallback counter available")

        return self.fallback_counter.count_tokens(text, model_name)

    async def compress_text(
        self,
        text: str,
        max_tokens: int,
        model_name: str = "starcoder",
        strategy: str = "extractive",
    ) -> CompressionResult:
        """
        Compress text using ML service if available.

        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            strategy: Compression strategy

        Returns:
            CompressionResult with compression details
        """
        if await self._check_service_availability():
            try:
                return await self.ml_client.compress_text(
                    text, max_tokens, model_name, strategy
                )
            except Exception as e:
                self.logger.warning("ml_service_error", error=str(e), operation="compress_text")

        # Fallback to basic compression
        if self.fallback_counter is None:
            raise RuntimeError("No fallback counter available")

        # Use basic compression strategies
        if strategy == "extractive":
            # Simple keyword extraction as fallback
            from core.text_compressor import SimpleTextCompressor

            compressor = SimpleTextCompressor(self.fallback_counter)
            return compressor.compress_by_keywords(text, max_tokens, model_name)
        else:
            # Default to truncation
            from core.text_compressor import SimpleTextCompressor

            compressor = SimpleTextCompressor(self.fallback_counter)
            return compressor.compress_by_truncation(text, max_tokens, model_name)

    async def close(self):
        """Close ML client if available."""
        if self.ml_client:
            await self.ml_client.close()
