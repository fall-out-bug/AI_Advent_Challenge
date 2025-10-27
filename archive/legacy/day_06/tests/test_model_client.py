"""
Unit tests for model_client module.

Tests functionality of client for working with local models.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import httpx
from unittest.mock import AsyncMock, patch, Mock

from src.model_client import LocalModelClient, ModelTestResult
from shared.clients.base_client import ModelResponse
from shared.exceptions.model_errors import ModelClientError, ModelConnectionError, ModelRequestError, ModelTimeoutError, ModelConfigurationError
from src.constants import MODEL_PORTS


class TestLocalModelClient:
    """Tests for LocalModelClient class."""
    
    @pytest.fixture
    def client(self):
        """Fixture for creating client."""
        return LocalModelClient()
    
    @pytest.fixture
    def mock_response_data(self):
        """Fixture with model response data."""
        return {
            "response": "Test response",
            "response_tokens": 5,
            "input_tokens": 10,
            "total_tokens": 15
        }
    
    def test_model_ports_mapping(self):
        """Test model to ports mapping."""
        expected_ports = {
            "qwen": 8000,
            "mistral": 8001,
            "tinyllama": 8002
        }
        assert MODEL_PORTS == expected_ports
    
    def test_client_initialization(self):
        """Test client initialization."""
        client = LocalModelClient()
        assert client.client is not None
        assert isinstance(client.client, httpx.AsyncClient)
    
    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test client closing."""
        await client.close()
        # Check that client is closed (can't directly check state)
        assert True  # If no exception thrown, test passed
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, client, mock_response_data):
        """Test successful model request."""
        with patch.object(client.client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            result = await client._make_request("qwen", "Test prompt")
            
            assert isinstance(result, ModelResponse)
            assert result.response == "Test response"
            assert result.response_tokens == 5
            assert result.model_name == "qwen"
            assert result.response_time > 0
    
    @pytest.mark.asyncio
    async def test_make_request_unknown_model(self, client):
        """Test request to unknown model."""
        with pytest.raises(ModelConfigurationError, match="Unknown model"):
            await client._make_request("unknown_model", "Test prompt")
    
    @pytest.mark.asyncio
    async def test_make_request_connection_error(self, client):
        """Test connection error handling."""
        with patch.object(client.client, 'post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection error")
            
            with pytest.raises(ModelConnectionError, match="Failed to connect to local model"):
                await client._make_request("qwen", "Test prompt")
    
    @pytest.mark.asyncio
    async def test_make_request_timeout_error(self, client):
        """Test timeout error handling."""
        with patch.object(client.client, 'post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout error")
            
            with pytest.raises(ModelTimeoutError, match="timed out"):
                await client._make_request("qwen", "Test prompt")
    
    @pytest.mark.asyncio
    async def test_make_request_http_status_error(self, client):
        """Test HTTP status error handling."""
        with patch.object(client.client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Server error", request=None, response=mock_response)
            
            with pytest.raises(ModelRequestError, match="HTTP error"):
                await client._make_request("qwen", "Test prompt")
    
    @pytest.mark.asyncio
    async def test_test_riddle(self, client, mock_response_data):
        """Тест тестирования загадки."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = [
                ModelResponse(
                    response="Прямой ответ",
                    response_tokens=3,
                    input_tokens=5,
                    total_tokens=8,
                    model_name="qwen",
                    response_time=1.0
                ),
                ModelResponse(
                    response="Пошаговый ответ",
                    response_tokens=5,
                    input_tokens=5,
                    total_tokens=10,
                    model_name="qwen",
                    response_time=2.0
                )
            ]
            
            result = await client.test_riddle("Тестовая загадка", "qwen", verbose=False)
            
            assert isinstance(result, ModelTestResult)
            assert result.riddle == "Тестовая загадка"
            assert result.model_name == "qwen"
            assert result.direct_answer == "Прямой ответ"
            assert result.stepwise_answer == "Пошаговый ответ"
            assert result.direct_response_time == 1.0
            assert result.stepwise_response_time == 2.0
    
    @pytest.mark.asyncio
    async def test_check_model_availability(self, client):
        """Тест проверки доступности моделей."""
        with patch.object(client.client, 'post') as mock_post:
            # Модель доступна
            mock_response_available = AsyncMock()
            mock_response_available.status_code = 200
            mock_post.return_value = mock_response_available
            
            availability = await client.check_all_availability()
            
            assert isinstance(availability, dict)
            assert "qwen" in availability
            assert "mistral" in availability
            assert "tinyllama" in availability
            assert availability["qwen"] is True
    
    @pytest.mark.asyncio
    async def test_check_model_availability_unavailable(self, client):
        """Тест проверки недоступности моделей."""
        with patch.object(client.client, 'post') as mock_post:
            # Модель недоступна
            mock_post.side_effect = httpx.HTTPError("Connection refused")
            
            availability = await client.check_all_availability()
            
            assert isinstance(availability, dict)
            assert availability["qwen"] is False
            assert availability["mistral"] is False
            assert availability["tinyllama"] is False
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test context manager functionality."""
        async with client as ctx_client:
            assert ctx_client is client
            # Test that client can be used in context
            assert ctx_client.client is not None
