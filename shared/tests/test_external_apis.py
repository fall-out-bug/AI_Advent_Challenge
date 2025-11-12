"""
Tests for external API functionality in UnifiedModelClient.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from shared_package.clients.unified_client import UnifiedModelClient
from shared_package.clients.base_client import ModelResponse
from shared_package.config.api_keys import get_api_key, is_api_key_configured
from shared_package.exceptions.model_errors import (
    ModelConfigurationError,
    ModelConnectionError,
    ModelRequestError
)


class TestExternalAPIRequests:
    """Test external API request functionality."""

    @pytest.mark.asyncio
    async def test_make_external_request_perplexity_success(self):
        """Test successful Perplexity API request."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True), \
             patch('shared_package.clients.unified_client.get_api_key', return_value="test_key"), \
             patch.object(client.client, 'post') as mock_post:

            # Mock successful response
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}]
            }
            mock_post.return_value = mock_response

            response = await client._make_external_request(
                "perplexity", "Test prompt", 100, 0.7
            )

            assert isinstance(response, ModelResponse)
            assert response.response == "Test response"
            assert response.model_name == "perplexity"
            assert response.response_tokens > 0
            assert response.input_tokens > 0
            assert response.total_tokens > 0

    @pytest.mark.asyncio
    async def test_make_external_request_chadgpt_success(self):
        """Test successful ChadGPT API request."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True), \
             patch('shared_package.clients.unified_client.get_api_key', return_value="test_key"), \
             patch.object(client.client, 'post') as mock_post:

            # Mock successful response
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "is_success": True,
                "response": "Test response"
            }
            mock_post.return_value = mock_response

            response = await client._make_external_request(
                "chadgpt", "Test prompt", 100, 0.7
            )

            assert isinstance(response, ModelResponse)
            assert response.response == "Test response"
            assert response.model_name == "chadgpt"
            assert response.response_tokens > 0
            assert response.input_tokens > 0
            assert response.total_tokens > 0

    @pytest.mark.asyncio
    async def test_make_external_request_no_api_key(self):
        """Test external API request without API key."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=False):
            with pytest.raises(ModelConfigurationError, match="API key not configured"):
                await client._make_external_request("perplexity", "Test prompt", 100, 0.7)

    @pytest.mark.asyncio
    async def test_make_external_request_unsupported_model(self):
        """Test external API request with unsupported model."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True):
            with pytest.raises((ModelConfigurationError, ModelRequestError), match=".*unknown.*"):
                await client._make_external_request("unknown", "Test prompt", 100, 0.7)

    @pytest.mark.asyncio
    async def test_make_external_request_connection_error(self):
        """Test external API request with connection error."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True), \
             patch('shared_package.clients.unified_client.get_api_key', return_value="test_key"), \
             patch.object(client.client, 'post', side_effect=httpx.ConnectError("Connection failed")):

            with pytest.raises(ModelConnectionError, match="Failed to connect to external API"):
                await client._make_external_request("perplexity", "Test prompt", 100, 0.7)

    @pytest.mark.asyncio
    async def test_make_external_request_http_error(self):
        """Test external API request with HTTP error."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True), \
             patch('shared_package.clients.unified_client.get_api_key', return_value="test_key"), \
             patch.object(client.client, 'post', side_effect=httpx.HTTPStatusError("HTTP Error", request=MagicMock(), response=MagicMock())):

            with pytest.raises(ModelRequestError, match="HTTP error for external API"):
                await client._make_external_request("perplexity", "Test prompt", 100, 0.7)

    @pytest.mark.asyncio
    async def test_make_external_request_perplexity_invalid_response(self):
        """Test Perplexity API request with invalid response format."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True), \
             patch('shared_package.clients.unified_client.get_api_key', return_value="test_key"), \
             patch.object(client.client, 'post') as mock_post:

            # Mock invalid response
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"invalid": "response"}
            mock_post.return_value = mock_response

            with pytest.raises(ModelRequestError, match="Unexpected response format from Perplexity API"):
                await client._make_external_request("perplexity", "Test prompt", 100, 0.7)

    @pytest.mark.asyncio
    async def test_make_external_request_chadgpt_invalid_response(self):
        """Test ChadGPT API request with invalid response format."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True), \
             patch('shared_package.clients.unified_client.get_api_key', return_value="test_key"), \
             patch.object(client.client, 'post') as mock_post:

            # Mock invalid response
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"is_success": False}
            mock_post.return_value = mock_response

            with pytest.raises(ModelRequestError, match="Unexpected response format from ChadGPT API"):
                await client._make_external_request("chadgpt", "Test prompt", 100, 0.7)


class TestExternalAPIAvailability:
    """Test external API availability checking."""

    @pytest.mark.asyncio
    async def test_check_external_availability_with_key(self):
        """Test external API availability check with API key."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True):
            result = await client._check_external_availability("perplexity")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_external_availability_without_key(self):
        """Test external API availability check without API key."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=False):
            result = await client._check_external_availability("perplexity")
            assert result is False


class TestExternalAPIIntegration:
    """Test integration of external APIs with main make_request method."""

    @pytest.mark.asyncio
    async def test_make_request_external_perplexity(self):
        """Test make_request with external Perplexity model."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True), \
             patch('shared_package.clients.unified_client.get_api_key', return_value="test_key"), \
             patch.object(client, '_make_external_request') as mock_external:

            mock_response = ModelResponse(
                response="Test response",
                response_tokens=10,
                input_tokens=5,
                total_tokens=15,
                model_name="perplexity",
                response_time=1.0
            )
            mock_external.return_value = mock_response

            response = await client.make_request("perplexity", "Test prompt")

            assert response.response == "Test response"
            assert response.model_name == "perplexity"
            mock_external.assert_called_once_with("perplexity", "Test prompt", 10000, 0.7)

    @pytest.mark.asyncio
    async def test_make_request_external_chadgpt(self):
        """Test make_request with external ChadGPT model."""
        client = UnifiedModelClient()

        with patch('shared_package.clients.unified_client.is_api_key_configured', return_value=True), \
             patch('shared_package.clients.unified_client.get_api_key', return_value="test_key"), \
             patch.object(client, '_make_external_request') as mock_external:

            mock_response = ModelResponse(
                response="Test response",
                response_tokens=10,
                input_tokens=5,
                total_tokens=15,
                model_name="chadgpt",
                response_time=1.0
            )
            mock_external.return_value = mock_response

            response = await client.make_request("chadgpt", "Test prompt")

            assert response.response == "Test response"
            assert response.model_name == "chadgpt"
            mock_external.assert_called_once_with("chadgpt", "Test prompt", 10000, 0.7)
