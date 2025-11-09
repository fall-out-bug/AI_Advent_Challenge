"""OpenAI-compatible chat client with tools support.

Follows KISS and explicit interfaces. Provides a minimal async wrapper
for `/v1/chat/completions` supporting `tools` and `tool_choice`.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class OpenAIChatClient:
    """Async client for OpenAI-compatible chat completions endpoint.

    Purpose:
        Send chat messages with optional tools JSON schema and retrieve
        structured responses including `tool_calls`.

    Example:
        >>> client = OpenAIChatClient()
        >>> resp = await client.create_completion(
        ...     model="mistral-7b-instruct",
        ...     messages=[{"role": "user", "content": "hi"}],
        ... )
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.environ.get("LLM_CHAT_BASE_URL")
            or "http://localhost:8001/v1"
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("LLM_CHAT_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self._client.aclose()

    async def create_completion(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> Dict[str, Any]:
        """Call chat completions.

        Args:
            model: Model identifier string.
            messages: Chat messages list.
            tools: OpenAI tools schema list.
            tool_choice: e.g., "auto" to enable tool selection.
            temperature: Sampling temperature.
            max_tokens: Max completion tokens.

        Returns:
            Parsed JSON dict from API response (`choices[0].message`).
        """
        url = f"{self.base_url}/chat/completions"
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        response = await self._client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Extract first message; keep raw for callers that need it
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message", {})
        return {
            "id": data.get("id"),
            "object": data.get("object"),
            "model": data.get("model"),
            "message": message,
            "tool_calls": message.get("tool_calls", [])
            if isinstance(message, dict)
            else [],
            "usage": data.get("usage", {}),
            "raw": data,
        }
