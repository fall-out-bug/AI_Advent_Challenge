"""
Tests for shared.clients.unified_client module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from shared_package.clients.base_client import ModelResponse
from shared_package.clients.unified_client import UnifiedModelClient
from shared_package.exceptions.model_errors import (
    ModelConfigurationError,
    ModelConnectionError,
    ModelRequestError,
    ModelTimeoutError,
)


class TestUnifiedModelClient:
    """Test UnifiedModelClient functionality."""

    @pytest.fixture
    def client(self):
        """Create client instance for testing."""
        return UnifiedModelClient(timeout=5.0, retry_base_delay=0.1)

    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.timeout == 5.0
        assert client.client is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_make_request_local_success(self, client):
        """Test successful local model request."""
        with patch.object(client.client, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            }
            mock_post.return_value = mock_response

            result = await client.make_request("qwen", "Test prompt")

            assert isinstance(result, ModelResponse)
            assert result.response == "Test response"
            assert result.response_tokens == 5
            assert result.input_tokens == 10
            assert result.total_tokens == 15
            assert result.model_name == "qwen"
            assert result.response_time >= 0

        await client.close()

    @pytest.mark.asyncio
    async def test_make_request_invalid_model(self, client):
        """Test request with invalid model."""
        with pytest.raises(ModelConfigurationError, match="Unknown model"):
            await client.make_request("invalid_model", "Test prompt")

        await client.close()

    @pytest.mark.asyncio
    async def test_make_request_external_not_implemented(self, client):
        """Test request to external model without API key."""
        with pytest.raises(ModelConfigurationError, match="API key not configured"):
            await client.make_request("perplexity", "Test prompt")

        await client.close()

    @pytest.mark.asyncio
    async def test_make_request_connection_error(self, client):
        """Test request with connection error."""
        with patch.object(client.client, "post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(ModelConnectionError, match="Failed to connect"):
                await client.make_request("qwen", "Test prompt")
            assert mock_post.call_count == client.max_retries * 2

        await client.close()

    @pytest.mark.asyncio
    async def test_make_request_timeout_error(self, client):
        """Test request with timeout error."""
        with patch.object(client.client, "post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(ModelTimeoutError, match="timed out"):
                await client.make_request("qwen", "Test prompt")
            assert mock_post.call_count == client.max_retries * 2

        await client.close()

    @pytest.mark.asyncio
    async def test_make_request_http_error(self, client):
        """Test request with HTTP error."""
        with patch.object(client.client, "post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "HTTP error", request=MagicMock(), response=MagicMock()
            )

            with pytest.raises(ModelRequestError, match="HTTP error"):
                await client.make_request("qwen", "Test prompt")

        await client.close()

    @pytest.mark.asyncio
    async def test_make_request_retries_then_succeeds(self):
        """Ensure transient errors are retried before succeeding."""
        client = UnifiedModelClient(timeout=5.0, max_retries=4, retry_base_delay=0.1)

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "After retries"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        call_counter = {"count": 0}

        async def side_effect(*args, **kwargs):
            call_counter["count"] += 1
            if call_counter["count"] < 3:
                raise httpx.ConnectError("flaky")
            return success_response

        with patch.object(client.client, "post", side_effect=side_effect):
            result = await client.make_request("qwen", "Hello world")

        assert result.response == "After retries"
        assert call_counter["count"] == 3
        await client.close()

    @pytest.mark.asyncio
    async def test_check_availability_local_success(self, client):
        """Test successful local model availability check."""
        with patch.object(client.client, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = await client.check_availability("qwen")
            assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_check_availability_local_failure(self, client):
        """Test failed local model availability check."""
        with patch.object(client.client, "get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            result = await client.check_availability("qwen")
        assert result is False

        await client.close()

    @pytest.mark.asyncio
    async def test_check_availability_external(self, client):
        """Test external model availability check."""
        result = await client.check_availability("perplexity")
        assert result is False  # External models require API key

        await client.close()

    @pytest.mark.asyncio
    async def test_check_availability_invalid_model(self, client):
        """Test availability check with invalid model."""
        result = await client.check_availability("invalid_model")
        assert result is False

        await client.close()

    @pytest.mark.asyncio
    async def test_check_all_availability(self, client):
        """Test checking availability of all models."""
        with patch.object(client, "check_availability") as mock_check:
            mock_check.return_value = True

            result = await client.check_all_availability()

            assert isinstance(result, dict)
            assert len(result) == 6  # All models in config
            assert all(result.values())  # All should be True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_available_models(self, client):
        """Test getting list of available models."""
        with patch.object(client, "check_all_availability") as mock_check:
            mock_check.return_value = {
                "qwen": True,
                "mistral": False,
                "tinyllama": True,
                "perplexity": True,
                "chadgpt": False,
            }

            result = await client.get_available_models()

            assert isinstance(result, list)
            assert len(result) == 3
            assert "qwen" in result
            assert "tinyllama" in result
            assert "perplexity" in result
            assert "mistral" not in result
            assert "chadgpt" not in result

        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as context manager."""
        async with UnifiedModelClient() as client:
            assert client.client is not None
            # Client should be closed automatically
        # Client should be closed after context exit

    @pytest.mark.asyncio
    async def test_default_parameters(self, client):
        """Test default parameters in make_request."""
        with patch.object(client.client, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test"}}],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            }
            mock_post.return_value = mock_response

            await client.make_request("qwen", "Test")

            # Check that default parameters were used
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["max_tokens"] == 10000  # DEFAULT_MAX_TOKENS
            assert payload["temperature"] == 0.7  # DEFAULT_TEMPERATURE

        await client.close()
