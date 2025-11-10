"""Unit tests for `llm_client` module."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from src.infrastructure.clients.llm_client import (
    FallbackLLMClient,
    HTTPLLMClient,
    ResilientLLMClient,
    get_llm_client,
)


def test_http_llm_client_host_url_conversion() -> None:
    """Docker URLs are converted to host URLs when needed."""
    client = HTTPLLMClient(url="llm-server:8000")
    host_url = client._get_host_url("http://llm-server:8000")
    assert host_url == "http://localhost:8001"
    assert client.url == "http://llm-server:8000"


class _StubResponse:
    def __init__(self, json_data: dict[str, Any], error: Exception | None = None):
        self._json = json_data
        self._error = error

    def raise_for_status(self) -> None:
        if self._error:
            raise self._error

    def json(self) -> dict[str, Any]:
        return self._json


class _StubAsyncClient:
    def __init__(self, responses: list[Any]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    async def post(self, url: str, json: dict[str, Any], timeout: float) -> Any:
        self.calls.append(url)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.mark.asyncio
async def test_http_llm_client_generate_uses_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTPLLMClient returns response from /chat endpoint when available."""
    client = HTTPLLMClient(url="http://localhost:8000")
    stub = _StubAsyncClient([_StubResponse({"response": "answer"})])
    async def _get_client() -> _StubAsyncClient:
        return stub

    monkeypatch.setattr(client, "_get_client", _get_client)
    result = await client.generate("Prompt")
    assert result == "answer"
    assert stub.calls == ["http://localhost:8000/chat"]


@pytest.mark.asyncio
async def test_http_llm_client_falls_back_to_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """When /chat returns 404, the client uses /v1/chat/completions."""
    client = HTTPLLMClient(url="http://localhost:8000")
    request = httpx.Request("POST", "http://localhost:8000/chat")
    http_error = httpx.HTTPStatusError(
        "not found",
        request=request,
        response=httpx.Response(404, request=request),
    )
    stub = _StubAsyncClient(
        [
            _StubResponse({}, error=http_error),
            _StubResponse(
                {
                    "choices": [
                        {"message": {"content": "fallback answer"}},
                    ]
                }
            ),
        ]
    )
    async def _get_client() -> _StubAsyncClient:
        return stub

    monkeypatch.setattr(client, "_get_client", _get_client)
    result = await client.generate("Prompt")
    assert result == "fallback answer"
    assert stub.calls[-1].endswith("/v1/chat/completions")


@pytest.mark.asyncio
async def test_http_llm_client_uses_host_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Connection error triggers host URL fallback."""
    client = HTTPLLMClient(url="http://llm-server:8000")
    stub = _StubAsyncClient(
        [
            httpx.ConnectError("boom", request=httpx.Request("POST", "http://llm-server:8000/chat")),
            _StubResponse({"response": "host response"}),
        ]
    )

    async def _get_client() -> _StubAsyncClient:
        return stub

    monkeypatch.setattr(client, "_get_client", _get_client)
    result = await client.generate("Prompt")
    assert result == "host response"
    assert stub.calls[-1].startswith("http://localhost:8001")


@pytest.mark.asyncio
async def test_fallback_llm_client_detects_summarization() -> None:
    """Fallback client returns textual summary for summarization prompts."""
    prompt = (
        "Суммаризируй посты:\n"
        "1. Пост о продуктивности и тайм-менеджменте.\n"
        "2. Пост о важности тестирования.\n"
    )
    client = FallbackLLMClient()
    result = await client.generate(prompt)
    assert "продуктивности" in result.lower()
    assert result.endswith((".", "!", "?", "..."))


@pytest.mark.asyncio
async def test_fallback_llm_client_returns_intent_json() -> None:
    """Fallback client returns JSON when prompt resembles intent parsing."""
    prompt = "Extract intent JSON: needs_clarification and task title."
    client = FallbackLLMClient()
    result = await client.generate(prompt)
    assert result.startswith("{")
    assert '"needs_clarification":false' in result.replace(" ", "")


def test_get_llm_client_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variable overrides fallback client."""
    monkeypatch.setenv("LLM_URL", "http://mistral-chat:8000")
    client = get_llm_client()
    assert isinstance(client, HTTPLLMClient)
    monkeypatch.delenv("LLM_URL", raising=False)


@pytest.mark.asyncio
async def test_resilient_client_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resilient client falls back when primary client fails."""

    class _FailingClient:
        async def generate(self, *args: Any, **kwargs: Any) -> str:
            raise httpx.ConnectError("boom", request=None)

    async def _fallback_generate(self, *args: Any, **kwargs: Any) -> str:
        return "fallback-response"

    monkeypatch.setattr(
        "src.infrastructure.clients.llm_client.FallbackLLMClient.generate",
        _fallback_generate,
    )
    monkeypatch.setattr(
        "src.infrastructure.clients.llm_client.get_llm_client",
        lambda url=None: _FailingClient(),
    )
    resilient = ResilientLLMClient(url="http://does-not-matter")
    result = await resilient.generate("Summarize the post about testing.")
    assert result == "fallback-response"
