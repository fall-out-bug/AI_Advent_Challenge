"""
Tests for HTTP client wrapper.
"""

import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock

from utils.http_wrapper import (
    HTTPClientWrapper, 
    HTTPConnectionError, 
    HTTPTimeoutError, 
    HTTPRequestError,
    http_error_handler
)


class TestHTTPClientWrapper:
    """Test HTTPClientWrapper functionality."""
    
    @pytest.mark.asyncio
    async def test_post_success(self):
        """Test successful POST request."""
        wrapper = HTTPClientWrapper()
        
        with patch.object(wrapper.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            response = await wrapper.post("http://test.com", json={"test": "data"})
            
            assert response == mock_response
            mock_post.assert_called_once_with("http://test.com", json={"test": "data"}, headers=None)
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_post_with_headers(self):
        """Test POST request with headers."""
        wrapper = HTTPClientWrapper()
        
        with patch.object(wrapper.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            headers = {"Authorization": "Bearer token"}
            response = await wrapper.post("http://test.com", json={"test": "data"}, headers=headers)
            
            assert response == mock_response
            mock_post.assert_called_once_with("http://test.com", json={"test": "data"}, headers=headers)
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_post_connection_error(self):
        """Test POST request with connection error."""
        wrapper = HTTPClientWrapper()
        
        with patch.object(wrapper.client, 'post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(HTTPConnectionError, match="Failed to connect to http://test.com"):
                await wrapper.post("http://test.com")
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_post_timeout_error(self):
        """Test POST request with timeout error."""
        wrapper = HTTPClientWrapper()
        
        with patch.object(wrapper.client, 'post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")
            
            with pytest.raises(HTTPTimeoutError, match="Request to http://test.com timed out"):
                await wrapper.post("http://test.com")
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_post_http_error(self):
        """Test POST request with HTTP error."""
        wrapper = HTTPClientWrapper()
        
        with patch.object(wrapper.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "HTTP error", request=MagicMock(), response=mock_response
            )
            mock_post.return_value = mock_response
            
            with pytest.raises(HTTPRequestError, match="HTTP error for http://test.com"):
                await wrapper.post("http://test.com")
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_get_success(self):
        """Test successful GET request."""
        wrapper = HTTPClientWrapper()
        
        with patch.object(wrapper.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = await wrapper.get("http://test.com")
            
            assert response == mock_response
            mock_get.assert_called_once_with("http://test.com", headers=None)
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_get_with_headers(self):
        """Test GET request with headers."""
        wrapper = HTTPClientWrapper()
        
        with patch.object(wrapper.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            headers = {"Authorization": "Bearer token"}
            response = await wrapper.get("http://test.com", headers=headers)
            
            assert response == mock_response
            mock_get.assert_called_once_with("http://test.com", headers=headers)
        
        await wrapper.close()
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test client close."""
        wrapper = HTTPClientWrapper()
        
        with patch.object(wrapper.client, 'aclose') as mock_close:
            await wrapper.close()
            mock_close.assert_called_once()


class TestHTTPErrorDecorator:
    """Test HTTP error decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator with successful function."""
        @http_error_handler
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_decorator_http_error(self):
        """Test decorator with HTTP error."""
        @http_error_handler
        async def test_func():
            raise HTTPConnectionError("Connection failed")
        
        with pytest.raises(HTTPConnectionError, match="Connection failed"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_decorator_unexpected_error(self):
        """Test decorator with unexpected error."""
        @http_error_handler
        async def test_func():
            raise ValueError("Unexpected error")
        
        with pytest.raises(HTTPRequestError, match="Unexpected error in test_func"):
            await test_func()
