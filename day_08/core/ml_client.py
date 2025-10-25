"""
Client for Token Analysis ML Service.

This client provides a clean interface to interact with the ML service
running in Docker container, handling heavy operations like accurate
token counting and advanced compression.

Example:
    Basic usage for token counting:
    
    ```python
    from core.ml_client import TokenAnalysisClient
    from models.data_models import TokenInfo
    
    client = TokenAnalysisClient("http://localhost:8004")
    
    # Count tokens accurately
    token_info = await client.count_tokens("Hello world!", "starcoder")
    print(f"Token count: {token_info.count}")
    ```
    
    Advanced compression usage:
    
    ```python
    # Compress text using ML service
    result = await client.compress_text(
        text="Very long text...",
        max_tokens=100,
        strategy="extractive",
        model_name="starcoder"
    )
    print(f"Compressed: {result.compressed_text}")
    ```
"""

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from core.validators import RequestValidator
from models.data_models import CompressionResult, TokenInfo
from utils.logging import LoggerFactory
from utils.retry import CircuitBreakerConfig, ResilientClient, RetryConfig


class TokenAnalysisClient:
    """
    Client for Token Analysis ML Service.

    Provides methods to interact with the ML service running in Docker
    for accurate token counting and advanced compression strategies.

    Features:
    - Retry logic with exponential backoff
    - Circuit breaker pattern for resilience
    - Structured logging for debugging
    - Request validation

    Attributes:
        base_url (str): Base URL of the ML service
        client (httpx.AsyncClient): HTTP client for requests
        logger: Logger instance for structured logging
        resilient_client (ResilientClient): Client with retry and circuit breaker

    Example:
        ```python
        from core.ml_client import TokenAnalysisClient
        from models.data_models import TokenInfo, CompressionResult

        # Initialize client
        client = TokenAnalysisClient("http://localhost:8004")

        # Count tokens
        token_info = await client.count_tokens("Hello world!", "starcoder")

        # Compress text
        result = await client.compress_text(
            text="Very long text...",
            max_tokens=100,
            strategy="extractive"
        )

        # Batch operations
        texts = ["Text 1", "Text 2", "Text 3"]
        batch_result = await client.batch_count_tokens(texts, "starcoder")
        ```
    """

    def __init__(self, base_url: str = "http://localhost:8004"):
        """
        Initialize client with retry and circuit breaker.

        Sets up the HTTP client with retry logic, circuit breaker pattern,
        and structured logging for robust communication with the ML service.

        Args:
            base_url: Base URL of the ML service (default: "http://localhost:8004")

        Example:
            ```python
            from core.ml_client import TokenAnalysisClient

            # Default local service
            client = TokenAnalysisClient()

            # Custom service URL
            client = TokenAnalysisClient("http://ml-service:8004")
            ```
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

    async def _make_post_request(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            return await self._execute_with_resilience(
                self._make_get_request, "/health"
            )
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            raise ConnectionError(f"Cannot connect to ML service: {e}")

    async def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """
        Count tokens using accurate HuggingFace tokenizers.

        Sends text to the ML service for accurate token counting using
        the actual tokenizer for the specified model. This provides
        much more accurate results than word-based estimation.

        Args:
            text: Text to count tokens for
            model_name: Name of the model (default: "starcoder")

        Returns:
            TokenInfo: Object containing accurate token count and metadata

        Example:
            ```python
            from core.ml_client import TokenAnalysisClient
            from models.data_models import TokenInfo

            client = TokenAnalysisClient()

            # Count tokens accurately
            text = "Hello world! This is a test."
            token_info = await client.count_tokens(text, "starcoder")

            print(f"Accurate token count: {token_info.count}")
            print(f"Model: {token_info.model}")
            print(f"Cost: {token_info.estimated_cost}")
            ```
        """
        self._validate_count_tokens_input(text, model_name)
        response_data = await self._execute_count_request(text, model_name)
        return self._parse_token_info(response_data)

    def _validate_count_tokens_input(self, text: str, model_name: str) -> None:
        """Validate input parameters for count_tokens."""
        RequestValidator.validate_text(text)
        RequestValidator.validate_model_name(model_name)

    async def _execute_count_request(
        self, text: str, model_name: str
    ) -> Dict[str, Any]:
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

    async def _execute_batch_request(
        self, texts: List[str], model_name: str
    ) -> Dict[str, Any]:
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

        Sends text to the ML service for advanced compression using
        sophisticated algorithms like extractive summarization or
        semantic chunking. These strategies preserve meaning better
        than simple truncation.

        Args:
            text: Text to compress
            max_tokens: Maximum allowed tokens for compressed text
            model_name: Name of the model (default: "starcoder")
            strategy: Compression strategy ("extractive" or "semantic")

        Returns:
            CompressionResult: Object containing compressed text, token counts, and ratio

        Example:
            ```python
            from core.ml_client import TokenAnalysisClient
            from models.data_models import CompressionResult

            client = TokenAnalysisClient()

            # Compress using extractive strategy
            text = "This is a very long text that needs compression..."
            result = await client.compress_text(
                text=text,
                max_tokens=100,
                model_name="starcoder",
                strategy="extractive"
            )

            print(f"Original tokens: {result.original_tokens}")
            print(f"Compressed tokens: {result.compressed_tokens}")
            print(f"Compression ratio: {result.compression_ratio}")
            print(f"Compressed text: {result.compressed_text}")
            ```
        """
        self._validate_compression_input(text, max_tokens, model_name, strategy)
        response_data = await self._execute_compression_request(
            text, max_tokens, model_name, strategy
        )
        return self._parse_compression_result(response_data)

    def _validate_compression_input(
        self, text: str, max_tokens: int, model_name: str, strategy: str
    ) -> None:
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
    
    async def make_request(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> "ModelResponse":
        """
        Make inference request to model via UnifiedModelClient.
        
        Args:
            model_name: Name of the model to use
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            ModelResponse with response text, tokens, and timing
            
        Example:
            ```python
            from core.ml_client import TokenAnalysisClient
            
            client = TokenAnalysisClient()
            
            response = await client.make_request(
                model_name="starcoder",
                prompt="Write a Python function to sort a list",
                max_tokens=500,
                temperature=0.7
            )
            
            print(f"Response: {response.response}")
            print(f"Tokens used: {response.total_tokens}")
            ```
        """
        import asyncio
        from models.data_models import ModelResponse
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Use UnifiedModelClient for model inference
            import sys
            from pathlib import Path
            shared_path = Path(__file__).parent.parent.parent / "shared"
            sys.path.insert(0, str(shared_path))
            from shared_package.clients.unified_client import UnifiedModelClient
            
            unified_client = UnifiedModelClient()
            
            # Make the actual model request
            result = await unified_client.make_request(
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response_time = asyncio.get_event_loop().time() - start_time
            
            # Count tokens in response
            response_text = result.response
            token_count = result.total_tokens
            
            return ModelResponse(
                response=response_text,
                total_tokens=token_count,
                response_time=response_time,
                model_name=model_name
            )
            
        except Exception as e:
            self.logger.error(f"make_request failed for {model_name}: {e}")
            raise ConnectionError(f"Error making request to model {model_name}: {e}")

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
                self.logger.warning(
                    "ml_service_error", error=str(e), operation="count_tokens"
                )

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
                self.logger.warning(
                    "ml_service_error", error=str(e), operation="compress_text"
                )

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
