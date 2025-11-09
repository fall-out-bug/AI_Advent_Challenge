"""LLM client protocol for multipass reviewer package."""

from __future__ import annotations

from typing import Any, Protocol


class LLMClientProtocol(Protocol):
    async def make_request(self, model_name: str, prompt: str, **kwargs: Any) -> str:
        """Send prompt to underlying LLM and return response."""
        ...
