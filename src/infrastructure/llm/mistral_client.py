"""Mistral LLM client implementing LLMClientProtocol.

Following Clean Architecture: infrastructure layer implements domain protocol.
Supports local Mistral-7B via localhost:8001 endpoint.
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

from src.domain.interfaces.llm_client import LLMClientProtocol

logger = logging.getLogger(__name__)


class MistralClientError(Exception):
    """Base exception for Mistral client errors."""

    pass


class MistralTimeoutError(MistralClientError):
    """Timeout error for Mistral client."""

    pass


class MistralConnectionError(MistralClientError):
    """Connection error for Mistral client."""

    pass


class MistralClient:
    """Async client for Mistral-7B LLM via localhost:8001 endpoint.

    Purpose:
        Provides async wrapper for Mistral LLM with retry logic and error handling.
        Implements domain LLMClientProtocol for Clean Architecture compliance.

    Example:
        >>> from src.infrastructure.llm.mistral_client import MistralClient
        >>> client = MistralClient()
        >>> response = await client.make_request(
        ...     model_name="mistral",
        ...     prompt="Hello, how are you?",
        ...     max_tokens=100,
        ...     temperature=0.7
        ... )
        >>> await client.close()
    """

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_WAIT = 1.0  # seconds
    MAX_WAIT = 10.0  # seconds
    EXPONENTIAL_BASE = 2.0
    DEFAULT_TIMEOUT = 30.0  # seconds

    # Retryable exceptions
    RETRYABLE_EXCEPTIONS = (
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.ConnectError,
        TimeoutError,
        ConnectionError,
    )

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize Mistral client.

        Args:
            base_url: Base URL for Mistral API (default: http://localhost:8001)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.base_url = (
            base_url or os.environ.get("MISTRAL_API_URL") or "http://localhost:8001"
        ).rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized.

        Returns:
            Initialized HTTP client
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def make_request(
        self,
        model_name: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Make a request to the LLM.

        Args:
            model_name: Name of the model to use (e.g., "mistral")
            prompt: Input prompt for the model
            max_tokens: Maximum tokens to generate (default: 512)
            temperature: Generation temperature (default: 0.2)

        Returns:
            Model response text

        Raises:
            MistralClientError: If LLM request fails after retries
            ValueError: If parameters are invalid
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        params = self._prepare_request_params(max_tokens, temperature)
        try:
            response_text = await self._request_with_retry(
                model_name=model_name,
                prompt=prompt,
                **params,
            )
            logger.debug(f"LLM request successful: {len(response_text)} chars")
            return response_text
        except RetryError as e:
            self._handle_retry_error(e)
        except Exception as e:
            self._handle_request_error(e)

    def _prepare_request_params(
        self, max_tokens: Optional[int], temperature: Optional[float]
    ) -> Dict[str, Any]:
        """Prepare request parameters with defaults.

        Args:
            max_tokens: Optional max tokens
            temperature: Optional temperature

        Returns:
            Dictionary with max_tokens and temperature
        """
        return {
            "max_tokens": max_tokens or 512,
            "temperature": temperature if temperature is not None else 0.2,
        }

    def _handle_retry_error(self, e: RetryError) -> None:
        """Handle retry error.

        Args:
            e: RetryError exception

        Raises:
            MistralClientError: Always raises after logging
        """
        last_exception = e.last_attempt.exception()
        logger.error(
            f"Max retries exceeded for LLM request: {last_exception}",
            exc_info=True,
        )
        raise MistralClientError(
            f"LLM request failed after {self.MAX_RETRIES} retries: {last_exception}"
        ) from last_exception

    def _handle_request_error(self, e: Exception) -> None:
        """Handle general request error.

        Args:
            e: Exception

        Raises:
            MistralClientError: Always raises after logging
        """
        logger.error(f"LLM request failed: {e}", exc_info=True)
        raise MistralClientError(f"LLM request failed: {e}") from e

    async def _request_with_retry(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Make HTTP request with retry logic.

        Args:
            model_name: Model name
            prompt: User prompt
            max_tokens: Max tokens
            temperature: Temperature

        Returns:
            Response text

        Raises:
            Exception: If request fails
        """
        return await self._execute_request(
            model_name=model_name,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(
            multiplier=INITIAL_WAIT,
            max=MAX_WAIT,
            exp_base=EXPONENTIAL_BASE,
        ),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )
    async def _execute_request(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Execute HTTP request to Mistral API.

        Args:
            model_name: Model name
            prompt: User prompt
            max_tokens: Max tokens
            temperature: Temperature

        Returns:
            Extracted response text

        Raises:
            MistralTimeoutError: If request times out
            MistralConnectionError: If connection fails
            httpx.HTTPStatusError: If HTTP error occurs
        """
        client = await self._ensure_client()
        messages = [{"role": "user", "content": prompt}]

        # Try OpenAI-compatible endpoint first
        try:
            return await self._try_openai_endpoint(
                client, model_name, messages, max_tokens, temperature
            )
        except Exception as e:
            logger.debug(f"OpenAI endpoint failed, trying legacy: {e}")

        # Fallback to legacy /chat endpoint
        return await self._try_legacy_endpoint(
            client, messages, max_tokens, temperature
        )

    async def _try_openai_endpoint(
        self,
        client: httpx.AsyncClient,
        model_name: str,
        messages: list,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Try OpenAI-compatible /v1/chat/completions endpoint.

        Args:
            client: HTTP client
            model_name: Model name
            messages: Message list
            max_tokens: Max tokens
            temperature: Temperature

        Returns:
            Response text
        """
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        return self._extract_openai_response(data)

    def _extract_openai_response(self, data: dict) -> str:
        """Extract response text from OpenAI format.

        Args:
            data: Response JSON data

        Returns:
            Response text

        Raises:
            ValueError: If response cannot be extracted
        """
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        if content:
            return content

        if "response" in data:
            return str(data["response"])

        raise ValueError("Could not extract response from API")

    async def _try_legacy_endpoint(
        self,
        client: httpx.AsyncClient,
        messages: list,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Try legacy /chat endpoint.

        Args:
            client: HTTP client
            messages: Message list
            max_tokens: Max tokens
            temperature: Temperature

        Returns:
            Response text
        """
        url = f"{self.base_url}/chat"
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        # Extract response from various formats
        if "response" in data:
            return str(data["response"])
        if "text" in data:
            return str(data["text"])
        if "content" in data:
            return str(data["content"])

        raise ValueError("Could not extract response from legacy API")

    async def check_availability(self, model_name: str) -> bool:
        """Check if model is available.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is available, False otherwise
        """
        try:
            client = await self._ensure_client()
            health_url = f"{self.base_url}/health"

            response = await client.get(health_url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                # Check if model matches (if specified in response)
                if "model" in data:
                    return data["model"].lower() == model_name.lower()
                return True

            return False
        except Exception as e:
            logger.debug(f"Health check failed for {model_name}: {e}")
            return False

    async def close(self) -> None:
        """Close client resources.

        Cleanup any open connections or resources.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("Mistral client closed")

