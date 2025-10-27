"""
Tests for error handling decorators.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from utils.error_decorators import (
    retry_on_error,
    handle_http_errors,
    log_http_requests,
    timeout_protection,
    circuit_breaker
)
from utils.http_wrapper import HTTPConnectionError, HTTPTimeoutError, HTTPRequestError


class TestRetryOnError:
    """Test retry_on_error decorator."""
    
    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test retry decorator with success on first attempt."""
        @retry_on_error(max_retries=3)
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry decorator with success after failures."""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise HTTPConnectionError("Connection failed")
            return "success"
        
        result = await test_func()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_max_retries_exceeded(self):
        """Test retry decorator with max retries exceeded."""
        @retry_on_error(max_retries=2, delay=0.01)
        async def test_func():
            raise HTTPConnectionError("Connection failed")
        
        with pytest.raises(HTTPConnectionError, match="Connection failed"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_retry_non_http_error(self):
        """Test retry decorator with non-HTTP error."""
        @retry_on_error(max_retries=3)
        async def test_func():
            raise ValueError("Not an HTTP error")
        
        with pytest.raises(HTTPRequestError, match="Unexpected error in test_func"):
            await test_func()


class TestHandleHTTPErrors:
    """Test handle_http_errors decorator."""
    
    @pytest.mark.asyncio
    async def test_handle_connection_error(self):
        """Test handling connection error."""
        @handle_http_errors
        async def test_func():
            raise HTTPConnectionError("Connection failed")
        
        with pytest.raises(HTTPConnectionError, match="Connection failed in test_func"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_handle_timeout_error(self):
        """Test handling timeout error."""
        @handle_http_errors
        async def test_func():
            raise HTTPTimeoutError("Request timed out")
        
        with pytest.raises(HTTPTimeoutError, match="Timeout in test_func"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_handle_request_error(self):
        """Test handling request error."""
        @handle_http_errors
        async def test_func():
            raise HTTPRequestError("Request failed")
        
        with pytest.raises(HTTPRequestError, match="Request failed in test_func"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_handle_unexpected_error(self):
        """Test handling unexpected error."""
        @handle_http_errors
        async def test_func():
            raise ValueError("Unexpected error")
        
        with pytest.raises(HTTPRequestError, match="Unexpected error in test_func"):
            await test_func()


class TestLogHTTPRequests:
    """Test log_http_requests decorator."""
    
    @pytest.mark.asyncio
    async def test_log_success(self, capsys):
        """Test logging successful request."""
        @log_http_requests
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
        
        captured = capsys.readouterr()
        assert "🌐 Making HTTP request: test_func" in captured.out
        assert "✅ HTTP request successful: test_func" in captured.out
    
    @pytest.mark.asyncio
    async def test_log_failure(self, capsys):
        """Test logging failed request."""
        @log_http_requests
        async def test_func():
            raise HTTPConnectionError("Connection failed")
        
        with pytest.raises(HTTPConnectionError):
            await test_func()
        
        captured = capsys.readouterr()
        assert "🌐 Making HTTP request: test_func" in captured.out
        assert "❌ HTTP request failed: test_func" in captured.out


class TestTimeoutProtection:
    """Test timeout_protection decorator."""
    
    @pytest.mark.asyncio
    async def test_timeout_protection_success(self):
        """Test timeout protection with successful request."""
        @timeout_protection(timeout_seconds=1.0)
        async def test_func():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_timeout_protection_timeout(self):
        """Test timeout protection with timeout."""
        @timeout_protection(timeout_seconds=0.1)
        async def test_func():
            await asyncio.sleep(0.2)
            return "success"
        
        with pytest.raises(HTTPTimeoutError, match="Request timed out after 0.1s in test_func"):
            await test_func()


class TestCircuitBreaker:
    """Test circuit_breaker decorator."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Test circuit breaker with successful requests."""
        @circuit_breaker(failure_threshold=3, recovery_timeout=0.1)
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self):
        """Test circuit breaker opening after failures."""
        @circuit_breaker(failure_threshold=2, recovery_timeout=0.1)
        async def test_func():
            raise HTTPConnectionError("Connection failed")
        
        # First failure
        with pytest.raises(HTTPConnectionError):
            await test_func()
        
        # Second failure - circuit should open
        with pytest.raises(HTTPConnectionError):
            await test_func()
        
        # Third attempt - circuit should be open
        with pytest.raises(HTTPRequestError, match="Circuit breaker open for test_func"):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        @circuit_breaker(failure_threshold=1, recovery_timeout=0.1)
        async def test_func():
            raise HTTPConnectionError("Connection failed")
        
        # Cause circuit to open
        with pytest.raises(HTTPConnectionError):
            await test_func()
        
        # Wait for recovery
        await asyncio.sleep(0.2)
        
        # Circuit should be closed again
        with pytest.raises(HTTPConnectionError):
            await test_func()
