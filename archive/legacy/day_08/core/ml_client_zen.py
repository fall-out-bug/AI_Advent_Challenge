"""
Zen Python ML Client - Refactored following Python Zen principles.

Key improvements:
1. Explicit is better than implicit - clear error handling and type hints
2. Errors should never pass silently - proper exception handling
3. Simple is better than complex - cleaner interface design
4. Readability counts - better naming and documentation
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

import httpx

from models.data_models import CompressionResult, TokenInfo


class MLServiceError(Exception):
    """Custom exception for ML service errors."""

    pass


class ServiceUnavailableError(MLServiceError):
    """Raised when ML service is unavailable."""

    pass


class InvalidRequestError(MLServiceError):
    """Raised when request is invalid."""

    pass


@dataclass
class ServiceConfig:
    """Configuration for ML service - explicit and immutable."""

    base_url: str = "http://localhost:8004"
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.timeout_seconds < 1:
            raise MLServiceError("timeout_seconds must be >= 1")
        if self.max_retries < 0:
            raise MLServiceError("max_retries must be >= 0")
        if self.retry_delay < 0:
            raise MLServiceError("retry_delay must be >= 0")


class TokenAnalysisClient:
    """
    Client for Token Analysis ML Service.

    Following Zen principles:
    - Explicit is better than implicit
    - Errors should never pass silently
    - Simple is better than complex
    """

    def __init__(self, config: Optional[ServiceConfig] = None):
        """
        Initialize ML service client.

        Args:
            config: Service configuration (uses defaults if None)
        """
        self.config = config or ServiceConfig()
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.config.timeout_seconds)

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response data

        Raises:
            ServiceUnavailableError: If service is unavailable
            InvalidRequestError: If request is invalid
        """
        await self._ensure_client()

        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.request(method, url, **kwargs)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise InvalidRequestError(f"Endpoint not found: {endpoint}")
                elif response.status_code >= 500:
                    raise ServiceUnavailableError(
                        f"Server error: {response.status_code}"
                    )
                else:
                    raise InvalidRequestError(f"Request failed: {response.status_code}")

            except httpx.RequestError as e:
                if attempt == self.config.max_retries:
                    raise ServiceUnavailableError(
                        f"Cannot connect to ML service: {e}"
                    ) from e

                await asyncio.sleep(self.config.retry_delay * (2**attempt))

        raise ServiceUnavailableError("Max retries exceeded")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the ML service is healthy.

        Returns:
            Health status and available models

        Raises:
            ServiceUnavailableError: If service is unavailable
        """
        try:
            return await self._make_request("GET", "/health")
        except ServiceUnavailableError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Health check failed: {e}") from e

    async def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """
        Count tokens using accurate HuggingFace tokenizers.

        Args:
            text: Text to count tokens for
            model_name: Name of the model

        Returns:
            TokenInfo with accurate token count

        Raises:
            InvalidRequestError: If request is invalid
            ServiceUnavailableError: If service is unavailable
        """
        if not isinstance(text, str):
            raise InvalidRequestError(f"Text must be string, got {type(text)}")

        if not isinstance(model_name, str):
            raise InvalidRequestError(
                f"Model name must be string, got {type(model_name)}"
            )

        try:
            data = await self._make_request(
                "POST", "/count-tokens", json={"text": text, "model_name": model_name}
            )

            return TokenInfo(
                count=data["count"],
                estimated_cost=data["estimated_cost"],
                model_name=data["model_name"],
            )
        except ServiceUnavailableError:
            raise
        except Exception as e:
            raise InvalidRequestError(f"Token counting failed: {e}") from e

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

        Raises:
            InvalidRequestError: If request is invalid
            ServiceUnavailableError: If service is unavailable
        """
        if not isinstance(texts, list):
            raise InvalidRequestError(f"Texts must be list, got {type(texts)}")

        if not texts:
            return []

        try:
            data = await self._make_request(
                "POST",
                "/count-tokens-batch",
                json={"texts": texts, "model_name": model_name},
            )

            return [
                TokenInfo(
                    count=result["count"],
                    estimated_cost=result["estimated_cost"],
                    model_name=result["model_name"],
                )
                for result in data["results"]
            ]
        except ServiceUnavailableError:
            raise
        except Exception as e:
            raise InvalidRequestError(f"Batch token counting failed: {e}") from e

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

        Raises:
            InvalidRequestError: If request is invalid
            ServiceUnavailableError: If service is unavailable
        """
        if not isinstance(text, str):
            raise InvalidRequestError(f"Text must be string, got {type(text)}")

        if not isinstance(max_tokens, int) or max_tokens < 1:
            raise InvalidRequestError(
                f"max_tokens must be positive integer, got {max_tokens}"
            )

        if strategy not in ["extractive", "semantic"]:
            raise InvalidRequestError(
                f"Strategy must be 'extractive' or 'semantic', got {strategy}"
            )

        try:
            data = await self._make_request(
                "POST",
                "/compress-text",
                json={
                    "text": text,
                    "max_tokens": max_tokens,
                    "model_name": model_name,
                    "strategy": strategy,
                },
            )

            return CompressionResult(
                original_text=data["original_text"],
                compressed_text=data["compressed_text"],
                original_tokens=data["original_tokens"],
                compressed_tokens=data["compressed_tokens"],
                compression_ratio=data["compression_ratio"],
                strategy_used=data["strategy_used"],
            )
        except ServiceUnavailableError:
            raise
        except Exception as e:
            raise InvalidRequestError(f"Text compression failed: {e}") from e

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models.

        Returns:
            List of available model names

        Raises:
            ServiceUnavailableError: If service is unavailable
        """
        try:
            data = await self._make_request("GET", "/available-models")
            return data["models"]
        except ServiceUnavailableError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to get available models: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None


class HybridTokenCounter:
    """
    Hybrid token counter that uses ML service when available,
    falls back to simple estimation when service is unavailable.

    Following Zen principles:
    - Simple is better than complex
    - Explicit is better than implicit
    - Errors should never pass silently
    """

    def __init__(
        self,
        ml_client: Optional[TokenAnalysisClient] = None,
        fallback_counter=None,
        config: Optional[ServiceConfig] = None,
    ):
        """
        Initialize hybrid counter.

        Args:
            ml_client: ML service client (optional)
            fallback_counter: Fallback counter for when ML service is unavailable
            config: Service configuration
        """
        self.ml_client = ml_client or TokenAnalysisClient(config)
        self.fallback_counter = fallback_counter
        self._service_available: Optional[bool] = None

    async def _check_service_availability(self) -> bool:
        """
        Check if ML service is available.

        Returns:
            True if service is available, False otherwise
        """
        if self._service_available is not None:
            return self._service_available

        try:
            await self.ml_client.health_check()
            self._service_available = True
            return True
        except ServiceUnavailableError:
            self._service_available = False
            return False
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

        Raises:
            MLServiceError: If both ML service and fallback fail
        """
        if await self._check_service_availability():
            try:
                return await self.ml_client.count_tokens(text, model_name)
            except ServiceUnavailableError as e:
                print(f"⚠️  ML service error: {e}, falling back to simple estimation")

        # Fallback to simple estimation
        if self.fallback_counter is None:
            raise MLServiceError("No fallback counter available")

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

        Raises:
            MLServiceError: If both ML service and fallback fail
        """
        if await self._check_service_availability():
            try:
                return await self.ml_client.compress_text(
                    text, max_tokens, model_name, strategy
                )
            except ServiceUnavailableError as e:
                print(f"⚠️  ML service error: {e}, falling back to basic compression")

        # Fallback to basic compression
        if self.fallback_counter is None:
            raise MLServiceError("No fallback counter available")

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

    async def close(self) -> None:
        """Close ML client if available."""
        if self.ml_client:
            await self.ml_client.close()
