"""LLM client abstraction and simple providers."""

from __future__ import annotations

import os
import re
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
        Automatically detects Docker vs host access and adjusts URL accordingly.

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
        self._host_url: str | None = None  # Cached host URL for fallback
        
    def _get_host_url(self, docker_url: str) -> str:
        """Convert Docker URL to host URL if running from host.
        
        Args:
            docker_url: Docker network URL (e.g., http://llm-server:8000)
            
        Returns:
            Host URL (e.g., http://localhost:8080)
        """
        # Map common Docker service names to host ports
        docker_to_host = {
            "llm-server:8000": "localhost:8001",  # Port mapping: 8000->8001
            "mistral-chat:8000": "localhost:8001",
            "mistral-vllm:8000": "localhost:8001",
        }
        
        # Extract host:port from URL
        url_parts = docker_url.replace("http://", "").replace("https://", "")
        if url_parts in docker_to_host:
            return f"http://{docker_to_host[url_parts]}"
        
        # Default: try common ports
        if ":8000" in url_parts:
            return "http://localhost:8001"  # Common mapping
        if ":8001" in url_parts:
            return "http://localhost:8001"
            
        return docker_url  # Fallback to original

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate text via OpenAI-compatible chat completions API.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Assistant message content from choices[0].message.content

        Raises:
            httpx.RequestError: On network errors
            httpx.HTTPStatusError: On HTTP errors
            ValueError: On empty or invalid response structure
        """
        client = await self._get_client()
        url = f"{self.url}/v1/chat/completions"
        payload = {
            "model": os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.95,
            "stop": ["</s>", "[/INST]"]
        }

        try:
            response = await client.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            # Validate and extract content
            if "choices" not in data or not data["choices"]:
                raise ValueError("Response missing 'choices'")
            message = data["choices"][0].get("message", {})
            content = (message.get("content") or "").strip()
            if not content:
                raise ValueError("LLM returned empty content")
            return content
        except httpx.HTTPStatusError as e:
            # Fallback: try legacy /chat endpoint used by older servers
            if e.response is not None and e.response.status_code == 404:
                legacy_url = f"{self.url}/chat"
                legacy_payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                legacy_resp = await client.post(legacy_url, json=legacy_payload, timeout=self.timeout)
                legacy_resp.raise_for_status()
                legacy_data = legacy_resp.json()
                return (legacy_data.get("response") or "").strip()
            raise
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            # If Docker URL failed, try host URL
            if self._host_url is None and ("llm-server" in self.url or "mistral" in self.url.lower()):
                self._host_url = self._get_host_url(self.url)
                logger.debug(f"Docker URL failed, trying host URL: {self._host_url}")
                try:
                    # Try /chat endpoint first (legacy)
                    host_url = f"{self._host_url}/chat"
                    host_payload = {
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                    response = await client.post(host_url, json=host_payload, timeout=self.timeout)
                    response.raise_for_status()
                    data = response.json()
                    content = (data.get("response") or "").strip()
                    if content:
                        logger.info(f"Successfully connected to LLM via host URL: {self._host_url}")
                        return content
                    
                    # If /chat doesn't work, try /v1/chat/completions
                    host_url = f"{self._host_url}/v1/chat/completions"
                    response = await client.post(host_url, json=payload, timeout=self.timeout)
                    response.raise_for_status()
                    data = response.json()
                    if "choices" not in data or not data["choices"]:
                        raise ValueError("Response missing 'choices'")
                    message = data["choices"][0].get("message", {})
                    content = (message.get("content") or "").strip()
                    if content:
                        logger.info(f"Successfully connected to LLM via host URL: {self._host_url}")
                        return content
                except Exception as host_error:
                    logger.debug(f"Host URL also failed: {host_error}")
            logger.warning("LLM connection error, service may be unavailable: %s", e, extra={"url": url})
            raise
        except Exception:
            # Re-raise to let ResilientLLMClient fallback if needed
            raise

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class FallbackLLMClient:
    """Trivial LLM that returns context-aware fallback responses.
    
    Analyzes the prompt to determine if it's for summarization or intent parsing,
    and returns appropriate fallback format.
    """

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate context-aware fallback response.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (ignored)
            max_tokens: Maximum tokens (ignored)
            
        Returns:
            Fallback response in appropriate format
        """
        prompt_lower = prompt.lower()
        
        # Detect summarization prompts
        summarization_keywords = [
            "суммариз", "summarize", "суммар", "итогов", "факт",
            "канала", "channel", "пост", "post", "новост", "news"
        ]
        
        intent_keywords = [
            "извлеки", "extract", "intent", "задача", "task",
            "deadline", "приоритет", "priority", "title", "название"
        ]
        
        is_summarization = any(keyword in prompt_lower for keyword in summarization_keywords)
        is_intent = any(keyword in prompt_lower for keyword in intent_keywords)
        
        if is_summarization and not is_intent:
            # Generate simple text summary from prompt content
            # Extract post texts - look for numbered lines like "1. текст поста"
            lines = prompt.split('\n')
            post_texts = []
            
            for line in lines:
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                # Skip instructions and empty lines
                if (not line_stripped or 
                    'важно' in line_lower or 'пример' in line_lower or 
                    'суммар' in line_lower or 'верни' in line_lower or
                    line_stripped.startswith('Пример') or line_stripped.startswith('ВАЖНО')):
                    continue
                    
                # Look for numbered lines: "1. текст" or "1) текст"
                numbered_match = re.match(r'^\d+[\.\)]\s*(.+)$', line_stripped)
                if numbered_match:
                    text = numbered_match.group(1).strip()
                    # Filter out very short or instruction-like text
                    if len(text) > 15 and not any(skip in text.lower() for skip in ['важно', 'пример', 'суммар', 'верни', 'json']):
                        post_texts.append(text)
            
            if post_texts:
                # Simple concatenation fallback - join first few posts
                summary = '. '.join(post_texts[:min(3, len(post_texts))])
                if not summary.endswith('.'):
                    summary += '.'
                return summary
            else:
                # Generic fallback for summarization
                return "Обсуждаются основные темы и новости."
        else:
            # Default to intent parsing JSON format
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


