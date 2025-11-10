import asyncio
import os
import types
import pytest

from src.infrastructure.clients.llm_client import HTTPLLMClient


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise AssertionError(f"HTTP error: {self.status_code}")


class _FakeAsyncClient:
    def __init__(self, expected_url: str, payload: dict, status_code: int = 200):
        self.expected_url = expected_url
        self.payload = payload
        self.status_code = status_code
        self.last_url = None
        self.last_json = None

    async def post(self, url: str, json: dict, timeout: float | None = None):
        self.last_url = url
        self.last_json = json
        assert url == self.expected_url
        return _FakeResponse(self.payload, self.status_code)

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_generate_parses_openai_chat_response(monkeypatch):
    os.environ["LLM_MODEL"] = "mistralai/Mistral-7B-Instruct-v0.2"
    client = HTTPLLMClient(url="http://localhost:8000")

    expected_url = "http://localhost:8000/v1/chat/completions"
    payload = {
        "id": "chatcmpl-1",
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": "hello world"}},
        ],
    }

    fake = _FakeAsyncClient(expected_url=expected_url, payload=payload)

    async def _fake_get_client():
        return fake

    monkeypatch.setattr(client, "_get_client", _fake_get_client)

    out = await client.generate("hi", temperature=0.1, max_tokens=10)
    assert out == "hello world"
    assert fake.last_json["model"] == os.environ["LLM_MODEL"]
    assert fake.last_json["messages"][0]["content"] == "hi"
    assert fake.last_json["max_tokens"] == 10
    assert fake.last_json["temperature"] == 0.1


@pytest.mark.asyncio
async def test_generate_raises_on_missing_choices(monkeypatch):
    client = HTTPLLMClient(url="http://localhost:8000")
    expected_url = "http://localhost:8000/v1/chat/completions"
    payload = {"object": "chat.completion"}
    fake = _FakeAsyncClient(expected_url=expected_url, payload=payload)

    async def _fake_get_client():
        return fake

    monkeypatch.setattr(client, "_get_client", _fake_get_client)

    with pytest.raises(ValueError):
        await client.generate("hi")


@pytest.mark.asyncio
async def test_generate_raises_on_empty_content(monkeypatch):
    client = HTTPLLMClient(url="http://localhost:8000")
    expected_url = "http://localhost:8000/v1/chat/completions"
    payload = {"choices": [{"message": {"role": "assistant", "content": "   "}}]}
    fake = _FakeAsyncClient(expected_url=expected_url, payload=payload)

    async def _fake_get_client():
        return fake

    monkeypatch.setattr(client, "_get_client", _fake_get_client)

    with pytest.raises(ValueError):
        await client.generate("hi")
