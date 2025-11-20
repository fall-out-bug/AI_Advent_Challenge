"""Tests for MistralClient implementing LLMClientProtocol.

Following TDD approach with comprehensive test coverage.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.llm.mistral_client import (
    MistralClient,
    MistralClientError,
    MistralConnectionError,
    MistralTimeoutError,
)


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing.

    Returns:
        Mocked httpx.AsyncClient
    """
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    return mock_client


@pytest.fixture
def mistral_client():
    """Create MistralClient instance for testing.

    Returns:
        MistralClient instance
    """
    return MistralClient(base_url="http://localhost:8001", timeout=5.0)


@pytest.mark.asyncio
class TestMistralClient:
    """Test suite for MistralClient."""

    async def test_make_request_success_openai_format(
        self, mistral_client, mock_httpx_client
    ):
        """Test successful request with OpenAI-compatible format.

        Args:
            mistral_client: MistralClient fixture
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, how can I help?"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient(base_url="http://localhost:8001")

            # Act
            response = await client.make_request(
                model_name="mistral",
                prompt="Hello",
                max_tokens=100,
                temperature=0.7,
            )

            # Assert
            assert response == "Hello, how can I help?"
            await client.close()

    async def test_make_request_success_legacy_format(
        self, mistral_client, mock_httpx_client
    ):
        """Test successful request with legacy format.

        Args:
            mistral_client: MistralClient fixture
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        # OpenAI endpoint fails, legacy succeeds
        mock_openai_response = MagicMock()
        mock_openai_response.post.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=MagicMock(status_code=404)
        )

        mock_legacy_response = MagicMock()
        mock_legacy_response.status_code = 200
        mock_legacy_response.json.return_value = {"response": "Legacy response"}
        mock_legacy_response.raise_for_status = MagicMock()

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call to OpenAI endpoint fails
                raise httpx.HTTPStatusError(
                    "Not found",
                    request=MagicMock(),
                    response=MagicMock(status_code=404),
                )
            # Second call to legacy endpoint succeeds
            return mock_legacy_response

        mock_httpx_client.post = AsyncMock(side_effect=mock_post)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient(base_url="http://localhost:8001")

            # Act
            response = await client.make_request(
                model_name="mistral", prompt="Hello", max_tokens=100
            )

            # Assert
            assert response == "Legacy response"
            await client.close()

    async def test_make_request_empty_prompt(self, mistral_client):
        """Test request with empty prompt raises ValueError.

        Args:
            mistral_client: MistralClient fixture
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await mistral_client.make_request(
                model_name="mistral", prompt="", max_tokens=100
            )

    async def test_make_request_timeout_retry(self, mistral_client, mock_httpx_client):
        """Test retry logic on timeout error.

        Args:
            mistral_client: MistralClient fixture
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        # First two calls timeout, third succeeds
        mock_httpx_client.post = AsyncMock(
            side_effect=[
                httpx.TimeoutException("Request timeout"),
                httpx.TimeoutException("Request timeout"),
                MagicMock(
                    status_code=200,
                    json=lambda: {"choices": [{"message": {"content": "Success"}}]},
                    raise_for_status=MagicMock(),
                ),
            ]
        )

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient(base_url="http://localhost:8001", timeout=5.0)

            # Act
            response = await client.make_request(
                model_name="mistral", prompt="Test", max_tokens=100
            )

            # Assert
            assert response == "Success"
            assert mock_httpx_client.post.call_count == 3
            await client.close()

    async def test_make_request_max_retries_exceeded(
        self, mistral_client, mock_httpx_client
    ):
        """Test that max retries exceeded raises MistralClientError.

        Args:
            mistral_client: MistralClient fixture
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        mock_httpx_client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient(base_url="http://localhost:8001", timeout=5.0)

            # Act & Assert
            with pytest.raises(MistralClientError, match="LLM request failed"):
                await client.make_request(
                    model_name="mistral", prompt="Test", max_tokens=100
                )

            # Verify retries attempted
            assert mock_httpx_client.post.call_count >= 3
            await client.close()

    async def test_check_availability_success(self, mistral_client, mock_httpx_client):
        """Test successful health check.

        Args:
            mistral_client: MistralClient fixture
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "model": "mistral"}
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient(base_url="http://localhost:8001")

            # Act
            available = await client.check_availability("mistral")

            # Assert
            assert available is True
            await client.close()

    async def test_check_availability_failure(self, mistral_client, mock_httpx_client):
        """Test health check failure.

        Args:
            mistral_client: MistralClient fixture
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        mock_httpx_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient(base_url="http://localhost:8001")

            # Act
            available = await client.check_availability("mistral")

            # Assert
            assert available is False
            await client.close()

    async def test_check_availability_wrong_model(
        self, mistral_client, mock_httpx_client
    ):
        """Test health check with wrong model name.

        Args:
            mistral_client: MistralClient fixture
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "model": "qwen"}
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient(base_url="http://localhost:8001")

            # Act
            available = await client.check_availability("mistral")

            # Assert
            assert available is False
            await client.close()

    async def test_close(self, mistral_client, mock_httpx_client):
        """Test client close method.

        Args:
            mistral_client: MistralClient fixture
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        mock_httpx_client.aclose = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient(base_url="http://localhost:8001")

            # Act
            await client.close()

            # Assert
            mock_httpx_client.aclose.assert_called_once()

    async def test_default_parameters(self, mock_httpx_client):
        """Test default parameter values.

        Args:
            mock_httpx_client: Mocked httpx client
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MistralClient()

            # Act
            response = await client.make_request(model_name="mistral", prompt="Test")

            # Assert
            assert response == "Response"
            # Verify default max_tokens and temperature used
            call_args = mock_httpx_client.post.call_args
            assert call_args is not None
            payload = call_args.kwargs["json"]
            assert payload["max_tokens"] == 512  # default
            assert payload["temperature"] == 0.2  # default
            await client.close()

    async def test_environment_variable_override(self):
        """Test that MISTRAL_API_URL environment variable is used."""
        # Arrange
        import os

        original_url = os.environ.get("MISTRAL_API_URL")

        try:
            # Use config-driven URL from environment variable (not hardcoded)
            test_url = "http://custom:9000"
            os.environ["MISTRAL_API_URL"] = test_url

            # Act
            client = MistralClient()

            # Assert: URL comes from environment variable (config-driven check)
            assert client.base_url == test_url
        finally:
            if original_url:
                os.environ["MISTRAL_API_URL"] = original_url
            elif "MISTRAL_API_URL" in os.environ:
                del os.environ["MISTRAL_API_URL"]
