"""Tests for agent client communication."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from communication.agent_client import AgentClient


class TestAgentClient:
    """Test agent client functionality."""

    def setup_method(self):
        """Set up test client."""
        self.client = AgentClient()

    def test_init(self):
        """Test client initialization."""
        assert self.client is not None
        assert hasattr(self.client, "timeout")
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

                result = await client._make_request("http://test.com/api", "GET")

                assert result == {"status": "ok"}
                mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_unsupported_method(self):
        """Test request with unsupported HTTP method."""
        async with AgentClient() as client:
            with pytest.raises(httpx.HTTPError, match="Request failed after 4 attempts"):
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
                mock_client.post = AsyncMock(
                    side_effect=[
                        httpx.TimeoutException("Timeout"),
                        httpx.TimeoutException("Timeout"),
                        Mock(
                            json=lambda: {"success": True},
                            raise_for_status=lambda: None,
                        ),
                    ]
                )

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

                mock_client.post = AsyncMock(
                    side_effect=[
                        httpx.HTTPStatusError(
                            "Server Error", request=Mock(), response=mock_response
                        ),
                        Mock(
                            json=lambda: {"success": True},
                            raise_for_status=lambda: None,
                        ),
                    ]
                )

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

                mock_client.post = AsyncMock(
                    side_effect=httpx.HTTPStatusError(
                        "Bad Request", request=Mock(), response=mock_response
                    )
                )

                with pytest.raises(httpx.HTTPError, match="HTTP error 400"):
                    await client._make_request(
                        "http://test.com/api", "POST", {"data": "test"}
                    )

    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self):
        """Test request with max retries exceeded."""
        async with AgentClient() as client:
            with patch.object(client, "_client") as mock_client:
                mock_client.post = AsyncMock(
                    side_effect=httpx.TimeoutException("Timeout")
                )

                with pytest.raises(
                    httpx.HTTPError, match="Request failed after 4 attempts"
                ):
                    await client._make_request(
                        "http://test.com/api", "POST", {"data": "test"}, max_retries=3
                    )

    @pytest.mark.asyncio
    async def test_generate_code_success(self):
        """Test successful code generation."""
        from communication.message_schema import CodeGenerationRequest
        
        async with AgentClient() as client:
            with patch.object(client, "_make_request") as mock_request:
                mock_request.return_value = {
                    "task_description": "Create a test function",
                    "generated_code": "def test(): pass",
                    "tests": "def test_test(): pass",
                    "metadata": {
                        "complexity": "low",
                        "lines_of_code": 1,
                        "estimated_time": "1s",
                        "dependencies": []
                    },
                    "generation_time": "2023-01-01T00:00:00",
                    "tokens_used": 100,
                }

                request = CodeGenerationRequest(task_description="Create a test function")
                result = await client.generate_code("http://test.com/generate", request)

                assert result.task_description == "Create a test function"
                assert result.generated_code == "def test(): pass"
                assert result.tests == "def test_test(): pass"
                assert result.tokens_used == 100

    @pytest.mark.asyncio
    async def test_review_code_success(self):
        """Test successful code review."""
        from communication.message_schema import CodeReviewRequest, TaskMetadata
        
        async with AgentClient() as client:
            with patch.object(client, "_make_request") as mock_request:
                mock_request.return_value = {
                    "code_quality_score": 8.5,
                    "metrics": {
                        "pep8_compliance": True,
                        "pep8_score": 9.0,
                        "has_docstrings": True,
                        "has_type_hints": True,
                        "test_coverage": "high",
                        "complexity_score": 3.0,
                    },
                    "issues": ["Minor formatting issue"],
                    "recommendations": ["Add more comments"],
                    "review_time": "2023-01-01T00:00:00",
                    "tokens_used": 150,
                }

                metadata = TaskMetadata(
                    complexity="low",
                    lines_of_code=2,
                    estimated_time="1s",
                    dependencies=[]
                )
                request = CodeReviewRequest(
                    task_description="Test task",
                    generated_code="def test(): pass",
                    tests="def test_test(): pass",
                    metadata=metadata
                )
                result = await client.review_code("http://test.com/review", request)

                assert result.code_quality_score == 8.5
                assert result.issues == ["Minor formatting issue"]
                assert result.recommendations == ["Add more comments"]
                assert result.tokens_used == 150

    @pytest.mark.asyncio
    async def test_check_health_success(self):
        """Test successful health check."""
        async with AgentClient() as client:
            with patch.object(client, "_make_request") as mock_request:
                mock_request.return_value = {
                    "status": "healthy",
                    "agent_type": "generator",
                    "uptime": 100.0,
                    "last_request": "2023-01-01T00:00:00"
                }

                result = await client.check_health("http://test.com/health")

                assert result.status == "healthy"
                assert result.agent_type == "generator"
                assert result.uptime == 100.0

    @pytest.mark.asyncio
    async def test_get_stats_success(self):
        """Test successful stats retrieval."""
        async with AgentClient() as client:
            with patch.object(client, "_make_request") as mock_request:
                mock_request.return_value = {
                    "total_requests": 100,
                    "successful_requests": 95,
                    "failed_requests": 5,
                    "average_response_time": 1.5,
                    "total_tokens_used": 1000,
                }

                result = await client.get_stats("http://test.com/stats")

                assert result.total_requests == 100
                assert result.successful_requests == 95
                assert result.failed_requests == 5
                assert result.average_response_time == 1.5
                assert result.total_tokens_used == 1000

    @pytest.mark.asyncio
    async def test_wait_for_agent_success(self):
        """Test successful agent waiting."""
        from communication.message_schema import AgentHealthResponse
        
        async with AgentClient() as client:
            with patch.object(client, "check_health") as mock_health:
                mock_health.return_value = AgentHealthResponse(
                    status="healthy",
                    agent_type="generator",
                    uptime=100.0
                )

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
        from communication.message_schema import AgentHealthResponse
        
        async with AgentClient() as client:
            with patch.object(client, "check_health") as mock_health:
                mock_health.side_effect = [
                    httpx.HTTPError("Not ready"),
                    AgentHealthResponse(
                        status="healthy",
                        agent_type="generator",
                        uptime=100.0
                    ),
                ]

                result = await client.wait_for_agent(
                    "http://test.com", max_retries=2, retry_delay=0.01
                )

                assert result is True
                assert mock_health.call_count == 2
