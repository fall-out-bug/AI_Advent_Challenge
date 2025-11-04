"""Resilient LLM client with automatic fallback and retry logic."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from src.infrastructure.clients.llm_client import (
    FallbackLLMClient,
    HTTPLLMClient,
    get_llm_client,
)
from src.infrastructure.logging import get_logger
from .llm_client import LLMClient

logger = get_logger("llm.resilient_client")

try:
    from prometheus_client import Counter, Histogram  # type: ignore

    _llm_request_duration = Histogram(
        "llm_request_duration_seconds",
        "Duration of LLM requests",
        ["client", "status"],
    )
    _llm_requests_total = Counter(
        "llm_requests_total",
        "Total LLM requests",
        ["client", "status"],
    )
    _llm_fallback_usage = Counter(
        "llm_fallback_usage_total",
        "Fallback client usage count",
    )
except Exception:  # pragma: no cover - metrics are optional
    _llm_request_duration = None
    _llm_requests_total = None
    _llm_fallback_usage = None


class ResilientLLMClient:
    """LLM client with automatic fallback and exponential backoff retry.

    Purpose:
        Wraps primary LLM client and automatically falls back to
        FallbackLLMClient on errors. Implements exponential backoff
        retry strategy for transient errors.

    Args:
        url: Optional LLM service URL.
        max_retries: Maximum retry attempts (default: 3).
        initial_backoff: Initial backoff delay in seconds (default: 1.0).
        max_backoff: Maximum backoff delay in seconds (default: 60.0).
        backoff_factor: Multiplier for exponential backoff (default: 2.0).
    """

    def __init__(
        self,
        url: str | None = None,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_factor: float = 2.0,
    ) -> None:
        self._primary = get_llm_client(url) if url else get_llm_client()
        self._fallback = FallbackLLMClient()
        self._use_fallback = isinstance(self._primary, FallbackLLMClient)
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_factor = backoff_factor

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 256,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate with automatic retry and fallback.

        Args:
            prompt: Input prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.
            stop_sequences: Optional stop sequences (ignored if not supported).

        Returns:
            Generated text or fallback response.
        """
        if self._use_fallback:
            return await self._fallback.generate(prompt, temperature, max_tokens)

        start_time = time.time()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                # Calculate backoff delay (0 for first attempt)
                if attempt > 0:
                    delay = min(
                        self.initial_backoff * (self.backoff_factor ** (attempt - 1)),
                        self.max_backoff,
                    )
                    logger.debug(
                        f"Retrying LLM request: attempt={attempt + 1}, max_retries={self.max_retries}, delay={delay}",
                    )
                    await asyncio.sleep(delay)

                result = await self._primary.generate(prompt, temperature, max_tokens)
                duration = time.time() - start_time

                # Record metrics
                if _llm_request_duration:
                    _llm_request_duration.labels(
                        client="primary", status="success"
                    ).observe(duration)
                if _llm_requests_total:
                    _llm_requests_total.labels(client="primary", status="success").inc()

                logger.debug(
                    f"LLM request succeeded: attempt={attempt + 1}, duration={duration:.2f}s, "
                    f"prompt_length={len(prompt)}, result_length={len(result)}",
                )
                return result

            except httpx.ConnectError as e:
                last_error = e
                logger.warning(
                    f"LLM connection error: attempt={attempt + 1}/{self.max_retries}, error={str(e)}",
                )
                # Connection errors: retry with backoff
                if attempt < self.max_retries - 1:
                    continue

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"LLM timeout: attempt={attempt + 1}/{self.max_retries}, error={str(e)}",
                )
                # Timeout errors: retry with backoff
                if attempt < self.max_retries - 1:
                    continue

            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                # Rate limit errors: retry with longer backoff
                if status_code == 429:
                    logger.warning(
                        f"LLM rate limit: attempt={attempt + 1}/{self.max_retries}, status_code={status_code}",
                    )
                    if attempt < self.max_retries - 1:
                        # Use longer backoff for rate limits
                        delay = min(
                            self.initial_backoff * (self.backoff_factor ** attempt) * 2,
                            self.max_backoff,
                        )
                        await asyncio.sleep(delay)
                        continue

                # Server errors (5xx): retry
                if 500 <= status_code < 600:
                    logger.warning(
                        f"LLM server error: attempt={attempt + 1}/{self.max_retries}, status_code={status_code}",
                    )
                    if attempt < self.max_retries - 1:
                        continue

                # Client errors (4xx, except 429): don't retry, use fallback
                logger.error(
                    f"LLM client error (not retrying): status_code={status_code}, error={str(e)}",
                )
                break

            except Exception as e:
                last_error = e
                logger.error(
                    f"LLM unexpected error: attempt={attempt + 1}/{self.max_retries}, "
                    f"error={str(e)}, error_type={type(e).__name__}",
                    exc_info=True,
                )
                # Unknown errors: retry once, then fallback
                if attempt < self.max_retries - 1:
                    continue
                break

        # All retries exhausted, use fallback
        duration = time.time() - start_time

        if _llm_request_duration:
            _llm_request_duration.labels(client="primary", status="failure").observe(
                duration
            )
        if _llm_requests_total:
            _llm_requests_total.labels(client="primary", status="failure").inc()
        if _llm_fallback_usage:
            _llm_fallback_usage.inc()

        logger.warning(
            f"LLM request failed, using fallback: max_retries={self.max_retries}, "
            f"duration={duration:.2f}s, error={str(last_error) if last_error else 'unknown'}",
        )

        fallback_start = time.time()
        result = await self._fallback.generate(prompt, temperature, max_tokens)
        fallback_duration = time.time() - fallback_start

        if _llm_request_duration:
            _llm_request_duration.labels(
                client="fallback", status="success"
            ).observe(fallback_duration)
        if _llm_requests_total:
            _llm_requests_total.labels(client="fallback", status="success").inc()

        return result

    async def batch_generate(
        self,
        prompts: list[str],
        temperature: float = 0.2,
        max_tokens: int = 256,
        stop_sequences: list[str] | None = None,
    ) -> list[str]:
        """Generate for multiple prompts in parallel.

        Args:
            prompts: List of prompts.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.
            stop_sequences: Optional stop sequences.

        Returns:
            List of generated texts.
        """
        # Use asyncio.gather for parallel processing
        tasks = [
            self.generate(p, temperature, max_tokens, stop_sequences) for p in prompts
        ]
        return await asyncio.gather(*tasks)
