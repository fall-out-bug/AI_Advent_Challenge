"""Tests for agent client communication."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx

from communication.agent_client import AgentClient


class TestAgentClient:
    """Test agent client functionality."""

    def setup_method(self):
        """Set up test client."""
        self.client = AgentClient()

    def test_init(self):
        """Test client initialization."""
        assert self.client is not None
        assert hasattr(self.client, 'timeout')
        assert self.client._client is None

    def test_init_with_custom_timeout(self):
        """Test client initialization with custom timeout."""
        client = AgentClient(timeout=30.0)
        assert client.timeout == 30.0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with AgentClient() as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_context_manager_close(self):
        """Test context manager closes client."""
        async with AgentClient() as client:
            pass
        
        # Client should be closed after context
        assert client._client is None

    @pytest.mark.asyncio
    async def test_make_request_post_success(self):
        """Test successful POST request."""
        async with AgentClient() as client:
            with patch.object(client, "_client") as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {"test": "data"}
                mock_response.raise_for_status.return_value = None
                mock_client.post = AsyncMock(return_value=mock_response)

                result = await client._make_request(
                    "http://test.com/api", "POST", {"data": "test"}
                )

                assert result == {"test": "data"}
                mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_get_success(self):
        """Test successful GET request."""
        async with AgentClient() as client:
            with patch.object(client, "_client") as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {"status": "ok"}
                mock_response.raise_for_status.return_value = None
                mock_client.get = AsyncMock(return_value=mock_response)

                result = await client._make_request(
                    "http://test.com/api", "GET"
                )

                assert result == {"status": "ok"}
                mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_unsupported_method(self):
        """Test request with unsupported HTTP method."""
        async with AgentClient() as client:
            with pytest.raises(ValueError, match="Unsupported HTTP method: PUT"):
                await client._make_request(
                    "http://test.com/api", "PUT", {"data": "test"}
                )

    @pytest.mark.asyncio
    async def test_make_request_not_initialized(self):
        """Test request without initialized client."""
        client = AgentClient()
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client._make_request("http://test.com/api", "POST")

    @pytest.mark.asyncio
    async def test_make_request_timeout_retry(self):
        """Test request with timeout and retry."""
        async with AgentClient() as client:
            with patch.object(client, "_client") as mock_client:
                mock_client.post = AsyncMock(side_effect=[
                    httpx.TimeoutException("Timeout"),
                    httpx.TimeoutException("Timeout"),
                    Mock(json=lambda: {"success": True}, raise_for_status=lambda: None)
                ])

                result = await client._make_request(
                    "http://test.com/api", "POST", {"data": "test"}, max_retries=2
                )

                assert result == {"success": True}
                assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_make_request_http_error_retry(self):
        """Test request with HTTP error and retry."""
        async with AgentClient() as client:
            with patch.object(client, "_client") as mock_client:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.text = "Server Error"
                
                mock_client.post = AsyncMock(side_effect=[
                    httpx.HTTPStatusError("Server Error", request=Mock(), response=mock_response),
                    Mock(json=lambda: {"success": True}, raise_for_status=lambda: None)
                ])

                result = await client._make_request(
                    "http://test.com/api", "POST", {"data": "test"}, max_retries=1
                )

                assert result == {"success": True}
                assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_make_request_http_error_no_retry(self):
        """Test request with HTTP error that doesn't retry."""
        async with AgentClient() as client:
            with patch.object(client, "_client") as mock_client:
                mock_response = Mock()
                mock_response.status_code = 400
                mock_response.text = "Bad Request"
                
                mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
                    "Bad Request", request=Mock(), response=mock_response
                ))

                with pytest.raises(httpx.HTTPError, match="HTTP error 400"):
                    await client._make_request(
                        "http://test.com/api", "POST", {"data": "test"}
                    )

    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self):
        """Test request with max retries exceeded."""
        async with AgentClient() as client:
            with patch.object(client, "_client") as mock_client:
                mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

                with pytest.raises(httpx.HTTPError, match="Request failed after 4 attempts"):
                    await client._make_request(
                        "http://test.com/api", "POST", {"data": "test"}, max_retries=3
                    )

    @pytest.mark.asyncio
    async def test_generate_code_success(self):
        """Test successful code generation."""
        async with AgentClient() as client:
            with patch.object(client, "_make_request") as mock_request:
                mock_request.return_value = {
                    "generated_code": "def test(): pass",
                    "tests": "def test_test(): pass",
                    "tokens_used": 100
                }

                result = await client.generate_code(
                    "http://test.com/generate",
                    "Create a test function"
                )

                assert result["generated_code"] == "def test(): pass"
                assert result["tests"] == "def test_test(): pass"
                assert result["tokens_used"] == 100

    @pytest.mark.asyncio
    async def test_review_code_success(self):
        """Test successful code review."""
        async with AgentClient() as client:
            with patch.object(client, "_make_request") as mock_request:
                mock_request.return_value = {
                    "code_quality_score": 8.5,
                    "suggestions": ["Add type hints"],
                    "tokens_used": 150
                }

                result = await client.review_code(
                    "http://test.com/review",
                    "def test(): pass",
                    "def test_test(): pass"
                )

                assert result["code_quality_score"] == 8.5
                assert result["suggestions"] == ["Add type hints"]
                assert result["tokens_used"] == 150

    @pytest.mark.asyncio
    async def test_check_health_success(self):
        """Test successful health check."""
        async with AgentClient() as client:
            with patch.object(client, "_make_request") as mock_request:
                mock_request.return_value = {
                    "status": "healthy",
                    "uptime": 100.0
                }

                result = await client.check_health("http://test.com/health")

                assert result["status"] == "healthy"
                assert result["uptime"] == 100.0

    @pytest.mark.asyncio
    async def test_get_stats_success(self):
        """Test successful stats retrieval."""
        async with AgentClient() as client:
            with patch.object(client, "_make_request") as mock_request:
                mock_request.return_value = {
                    "total_requests": 100,
                    "successful_requests": 95,
                    "failed_requests": 5
                }

                result = await client.get_stats("http://test.com/stats")

                assert result["total_requests"] == 100
                assert result["successful_requests"] == 95
                assert result["failed_requests"] == 5

    @pytest.mark.asyncio
    async def test_wait_for_agent_success(self):
        """Test successful agent waiting."""
        async with AgentClient() as client:
            with patch.object(client, "check_health") as mock_health:
                mock_health.return_value = {"status": "healthy"}

                result = await client.wait_for_agent(
                    "http://test.com", max_retries=1, retry_delay=0.01
                )

                assert result is True
                mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_agent_timeout(self):
        """Test agent waiting timeout."""
        async with AgentClient() as client:
            with patch.object(client, "check_health") as mock_health:
                mock_health.side_effect = httpx.HTTPError("Not ready")

                result = await client.wait_for_agent(
                    "http://test.com", max_retries=1, retry_delay=0.01
                )

                assert result is False
                assert mock_health.call_count == 1

    @pytest.mark.asyncio
    async def test_wait_for_agent_retry_success(self):
        """Test agent waiting with retry success."""
        async with AgentClient() as client:
            with patch.object(client, "check_health") as mock_health:
                mock_health.side_effect = [
                    httpx.HTTPError("Not ready"),
                    {"status": "healthy"}
                ]

                result = await client.wait_for_agent(
                    "http://test.com", max_retries=2, retry_delay=0.01
                )

                assert result is True
                assert mock_health.call_count == 2
