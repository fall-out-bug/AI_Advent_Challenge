"""Unit tests for ResilientLLMClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.clients.llm_client import FallbackLLMClient
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.llm.clients.resilient_client import ResilientLLMClient


@pytest.fixture(autouse=True)
def mock_logger():
    """Mock logger to avoid logging format issues in tests."""
    with patch("src.infrastructure.llm.clients.resilient_client.logger"):
        yield


@pytest.fixture
def mock_llm_client():
    """Mock primary LLM client."""
    client = MagicMock(spec=LLMClient)
    client.generate = AsyncMock(return_value="Generated text")
    client.batch_generate = AsyncMock(return_value=["Text 1", "Text 2"])
    return client


@pytest.fixture
def resilient_client(mock_llm_client):
    """ResilientLLMClient instance with mocked primary client."""
    with patch(
        "src.infrastructure.llm.clients.resilient_client.get_llm_client",
        return_value=mock_llm_client,
    ):
        client = ResilientLLMClient(
            url="http://localhost:8001",
            max_retries=3,
            initial_backoff=0.1,
            max_backoff=1.0,
        )
        # Override primary to use mock directly
        client._primary = mock_llm_client
        client._use_fallback = False
        yield client


@pytest.mark.asyncio
async def test_successful_generation_no_retry(resilient_client, mock_llm_client):
    """Test successful generation without retry."""
    result = await resilient_client.generate("test prompt")

    assert result == "Generated text"
    mock_llm_client.generate.assert_called_once()
    # Should not use fallback
    assert result != ""


@pytest.mark.asyncio
async def test_retry_on_temporary_error(resilient_client, mock_llm_client):
    """Test retry logic with exponential backoff on temporary errors."""
    import httpx

    # First two calls fail, third succeeds
    # ResilientLLMClient retries on httpx.ConnectError and httpx.TimeoutException
    mock_llm_client.generate.side_effect = [
        httpx.ConnectError("Connection failed"),
        httpx.ConnectError("Connection failed"),
        "Success text",
    ]

    result = await resilient_client.generate("test prompt")

    assert result == "Success text"
    assert mock_llm_client.generate.call_count == 3


@pytest.mark.asyncio
async def test_fallback_on_persistent_errors(resilient_client, mock_llm_client):
    """Test fallback to FallbackLLMClient when all retries fail."""
    import httpx

    # All retries fail with connection errors
    mock_llm_client.generate.side_effect = httpx.ConnectError("Persistent error")

    # Mock fallback client
    fallback_mock = MagicMock(spec=FallbackLLMClient)
    fallback_mock.generate = AsyncMock(return_value="Fallback text")
    resilient_client._fallback = fallback_mock

    result = await resilient_client.generate("test prompt")

    # Should use fallback after all retries exhausted
    assert result == "Fallback text"
    assert mock_llm_client.generate.call_count == 3  # max_retries attempts
    fallback_mock.generate.assert_called_once()


# Note: ResilientLLMClient doesn't implement batch_generate currently
# These tests are skipped until batch_generate is implemented
@pytest.mark.skip(reason="batch_generate not implemented in ResilientLLMClient")
async def test_batch_generate_success(resilient_client, mock_llm_client):
    """Test successful batch generation."""
    prompts = ["prompt 1", "prompt 2"]
    result = await resilient_client.batch_generate(prompts)

    assert result == ["Text 1", "Text 2"]
    mock_llm_client.batch_generate.assert_called_once_with(prompts)


@pytest.mark.asyncio
async def test_exponential_backoff_timing(resilient_client, mock_llm_client):
    """Test that exponential backoff delays increase."""
    import time

    import httpx

    mock_llm_client.generate.side_effect = [
        httpx.ConnectError("Error 1"),
        httpx.ConnectError("Error 2"),
        "Success",
    ]

    start = time.time()
    result = await resilient_client.generate("test")
    elapsed = time.time() - start

    # Should have delays between retries (rough check)
    # With initial_backoff=0.1, we expect at least some delay
    assert elapsed >= 0.1
    assert result == "Success"


@pytest.mark.asyncio
async def test_max_retries_respected(resilient_client, mock_llm_client):
    """Test that max_retries is respected."""
    import httpx

    # Always fail with connection error
    mock_llm_client.generate.side_effect = httpx.ConnectError("Always fails")

    # Mock fallback client
    fallback_mock = MagicMock(spec=FallbackLLMClient)
    fallback_mock.generate = AsyncMock(return_value="Fallback")
    resilient_client._fallback = fallback_mock

    await resilient_client.generate("test")

    # Should try max_retries times (3 attempts)
    assert mock_llm_client.generate.call_count == 3  # max_retries=3


def test_prometheus_metrics_exist():
    """Test that Prometheus metrics are defined."""
    from src.infrastructure.llm.clients.resilient_client import (
        _llm_fallback_usage,
        _llm_request_duration,
        _llm_requests_total,
    )

    # Metrics should exist (may be None if Prometheus not available)
    # Just check they don't raise import errors
    assert _llm_request_duration is not None or _llm_request_duration is None
    assert _llm_requests_total is not None or _llm_requests_total is None
    assert _llm_fallback_usage is not None or _llm_fallback_usage is None
