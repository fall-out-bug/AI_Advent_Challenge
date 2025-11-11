"""LLM service adapter for RAG system."""

from __future__ import annotations

import time
from typing import Any

import httpx

from src.domain.rag import Answer
from src.infrastructure.logging import get_logger


class LLMServiceAdapter:
    """Adapter for LLM service (implements LLMService protocol).

    Purpose:
        Interact with an OpenAI-compatible HTTP endpoint without relying on
        additional infrastructure clients.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        """Initialise LLM service adapter.

        Purpose:
            Capture configuration for LLM HTTP endpoint.

        Args:
            base_url: Base URL of the OpenAI-compatible endpoint.
            model: Model identifier to request.
            timeout_seconds: Request timeout in seconds.

        Example:
            >>> adapter = LLMServiceAdapter(  # doctest: +SKIP
            ...     base_url="http://127.0.0.1:8000",
            ...     model="qwen",
            ... )
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._logger = get_logger(__name__)

    def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Answer:
        """Generate completion and return answer with metadata.

        Purpose:
            Call LLM API with prompt and return structured answer.

        Args:
            prompt: Formatted prompt string.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            Answer value object with text and metadata.

        Raises:
            RuntimeError: If LLM API is unavailable.

        Example:
            >>> adapter = LLMServiceAdapter(...)  # doctest: +SKIP
            >>> answer = adapter.generate(
            ...     "Вопрос: ...",
            ...     max_tokens=1000,
            ...     temperature=0.7,
            ... )
        """
        start_time = time.time()

        try:
            response = httpx.post(
                f"{self._base_url}/v1/chat/completions",
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            self._logger.error("llm_generation_failed", error=str(error))
            raise RuntimeError(f"LLM generation failed: {error}") from error

        latency_ms = int((time.time() - start_time) * 1000)
        payload: Any = response.json()
        choice = (payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}

        return Answer(
            text=(message.get("content") or "").strip(),
            model=payload.get("model", self._model),
            latency_ms=latency_ms,
            tokens_generated=payload.get("usage", {}).get("completion_tokens", 0),
            metadata={
                "finish_reason": choice.get("finish_reason", "unknown"),
            },
        )
