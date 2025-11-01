"""
Integration tests for OpenAI-compatible API endpoints.

Purpose:
    Test OpenAI-compatible endpoints and backward compatibility
    with legacy /chat endpoint.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from shared_package.clients.unified_client import UnifiedModelClient
from shared_package.clients.base_client import ModelResponse


class TestOpenAICompatibility:
    """Test OpenAI-compatible API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create client instance for testing."""
        return UnifiedModelClient(timeout=5.0)
    
    @pytest.mark.asyncio
    async def test_openai_endpoint_success(self, client):
        """Test successful request via OpenAI-compatible endpoint."""
        with patch.object(client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "qwen",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Test response"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            result = await client.make_request("qwen", "Test prompt")
            
            assert isinstance(result, ModelResponse)
            assert result.response == "Test response"
            assert result.response_tokens == 5
            assert result.input_tokens == 10
            assert result.total_tokens == 15
            assert result.model_name == "qwen"
            
            # Verify OpenAI endpoint was called
            call_args = mock_post.call_args
            assert call_args is not None
            url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
            assert "/v1/chat/completions" in str(url)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_openai_endpoint_fallback_to_legacy(self, client):
        """Test fallback to legacy endpoint when OpenAI endpoint fails."""
        with patch.object(client.client, 'post') as mock_post:
            # First call fails (OpenAI endpoint)
            # Second call succeeds (legacy endpoint)
            mock_post.side_effect = [
                httpx.HTTPStatusError(
                    "404 Not Found",
                    request=MagicMock(),
                    response=MagicMock(status_code=404)
                ),
                MagicMock(
                    status_code=200,
                    json=lambda: {
                        "response": "Legacy response",
                        "input_tokens": 10,
                        "response_tokens": 5,
                        "total_tokens": 15
                    },
                    raise_for_status=MagicMock()
                )
            ]
            
            result = await client.make_request("qwen", "Test prompt")
            
            assert isinstance(result, ModelResponse)
            assert result.response == "Legacy response"
            
            # Verify both endpoints were tried
            assert mock_post.call_count == 2
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_openai_endpoint_parse_error(self, client):
        """Test error handling for invalid OpenAI response format."""
        with patch.object(client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                # Missing "choices" field
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="Unexpected OpenAI response format"):
                await client.make_request("qwen", "Test prompt")
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_legacy_endpoint_backward_compatibility(self, client):
        """Test backward compatibility with legacy /chat endpoint."""
        with patch.object(client.client, 'post') as mock_post:
            # Simulate OpenAI endpoint not available, use legacy
            mock_post.side_effect = [
                httpx.ConnectError("Connection failed"),
                MagicMock(
                    status_code=200,
                    json=lambda: {
                        "response": "Legacy response",
                        "input_tokens": 10,
                        "response_tokens": 5,
                        "total_tokens": 15
                    },
                    raise_for_status=MagicMock()
                )
            ]
            
            result = await client.make_request("qwen", "Test prompt")
            
            assert isinstance(result, ModelResponse)
            assert result.response == "Legacy response"
            
            # Verify legacy endpoint was called
            call_args = mock_post.call_args
            assert call_args is not None
            url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
            assert "/chat" in str(url)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_openai_availability_check(self, client):
        """Test availability check using OpenAI endpoint."""
        with patch.object(client.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = await client.check_availability("qwen")
            
            assert result is True
            
            # Verify /v1/models endpoint was called
            call_args = mock_get.call_args
            assert call_args is not None
            url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
            assert "/v1/models" in str(url)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_openai_availability_check_fallback(self, client):
        """Test availability check fallback to legacy /health endpoint."""
        with patch.object(client.client, 'get') as mock_get:
            # First call fails (OpenAI endpoint)
            # Second call succeeds (legacy endpoint)
            mock_get.side_effect = [
                httpx.ConnectError("Connection failed"),
                MagicMock(status_code=200)
            ]
            
            result = await client.check_availability("qwen")
            
            assert result is True
            
            # Verify both endpoints were tried
            assert mock_get.call_count == 2
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_openai_payload_format(self, client):
        """Test OpenAI-compatible payload format."""
        with patch.object(client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "qwen",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Test response"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            await client.make_request("qwen", "Test prompt", max_tokens=100, temperature=0.7)
            
            # Verify payload format
            call_args = mock_post.call_args
            assert call_args is not None
            
            # Check if OpenAI endpoint was called
            url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
            if "/v1/chat/completions" in str(url):
                json_data = call_args[1].get('json', {})
                assert "model" in json_data
                assert "messages" in json_data
                assert "max_tokens" in json_data
                assert "temperature" in json_data
                assert json_data["max_tokens"] == 100
                assert json_data["temperature"] == 0.7
        
        await client.close()

