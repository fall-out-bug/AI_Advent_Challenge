"""LLM client abstraction and simple providers."""

from __future__ import annotations

import os
from typing import Protocol
import httpx
import logging

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate a text completion for a prompt."""


class HTTPLLMClient:
    """HTTP-based LLM client for Mistral chat API.

    Purpose:
        Call local Mistral chat API via HTTP.

    Args:
        url: Base URL of the LLM service (e.g., http://mistral-chat:8000)
        timeout: Request timeout in seconds
    """

    def __init__(self, url: str | None = None, timeout: float = 30.0) -> None:
        self.url = url or os.getenv("LLM_URL", "http://localhost:8001")
        if not self.url.startswith("http"):
            self.url = f"http://{self.url}"
        # Remove trailing slash
        self.url = self.url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate text completion via HTTP API.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            httpx.RequestError: On network errors
            httpx.HTTPStatusError: On HTTP errors
        """
        client = await self._get_client()
        url = f"{self.url}/chat"
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            response = await client.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(f"LLM connection error, service may be unavailable: {e}", url=url)
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {e}", status=e.response.status_code, url=url)
            raise
        except Exception as e:
            logger.error(f"LLM unexpected error: {e}", url=url)
            raise

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class FallbackLLMClient:
    """Trivial LLM that echoes a minimal intent JSON when no provider is configured."""

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:  # noqa: D401
        return (
            '{"title":"Task","description":"","deadline":null,'
            '"priority":"medium","tags":[],"needs_clarification":false,"questions":[]}'
        )


def get_llm_client(url: str | None = None) -> LLMClient:
    """Get appropriate LLM client based on configuration.

    Purpose:
        Returns HTTPLLMClient if URL is configured, otherwise FallbackLLMClient.

    Args:
        url: LLM service URL (from env var LLM_URL if not provided)

    Returns:
        LLMClient instance
    """
    if url:
        return HTTPLLMClient(url=url)
    llm_url = os.getenv("LLM_URL", "")
    if llm_url and llm_url.strip():
        return HTTPLLMClient(url=llm_url)
    logger.warning("LLM_URL not configured, using FallbackLLMClient")
    return FallbackLLMClient()


class ResilientLLMClient:
    """LLM client that falls back to FallbackLLMClient on errors.

    Purpose:
        Wraps HTTPLLMClient and automatically falls back on connection failures.
    """

    def __init__(self, url: str | None = None) -> None:
        """Initialize resilient client.

        Args:
            url: LLM service URL
        """
        self._primary = get_llm_client(url) if url else get_llm_client()
        self._fallback = FallbackLLMClient()
        self._use_fallback = isinstance(self._primary, FallbackLLMClient)

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate with automatic fallback.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Generated text or fallback response
        """
        if self._use_fallback:
            return await self._fallback.generate(prompt, temperature, max_tokens)

        try:
            return await self._primary.generate(prompt, temperature, max_tokens)
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(f"LLM service unavailable, using fallback: {e}")
            return await self._fallback.generate(prompt, temperature, max_tokens)
        except Exception as e:
            logger.warning(f"LLM error, using fallback: {e}")
            return await self._fallback.generate(prompt, temperature, max_tokens)


