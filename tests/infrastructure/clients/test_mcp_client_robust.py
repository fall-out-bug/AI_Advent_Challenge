"""Tests for Robust MCP Client with retry logic.

Following TDD approach: tests written BEFORE implementation (Red phase).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.infrastructure.clients.mcp_client_robust import RobustMCPClient
from src.presentation.mcp.exceptions import (
    MCPClientError,
    MCPTimeoutError,
    MCPConnectionError,
)


@pytest.mark.asyncio
class TestRobustMCPClient:
    """Test suite for RobustMCPClient."""

    async def test_call_tool_success(self, mock_mcp_client):
        """Test successful tool call without retry.

        Args:
            mock_mcp_client: Mock MCP client fixture
        """
        # Arrange
        mock_mcp_client.call_tool.return_value = {"status": "success", "data": []}

        # Act
        client = RobustMCPClient(base_client=mock_mcp_client)
        result = await client.call_tool("get_posts", {"channel_id": "onaboka"})

        # Assert
        assert result["status"] == "success"
        assert mock_mcp_client.call_tool.call_count == 1

    async def test_call_tool_retry_on_timeout(self, mock_mcp_client):
        """Test retry logic on timeout error.

        Args:
            mock_mcp_client: Mock MCP client fixture
        """
        # Arrange
        # First two calls fail, third succeeds
        mock_mcp_client.call_tool.side_effect = [
            MCPTimeoutError("Timeout"),
            MCPTimeoutError("Timeout"),
            {"status": "success", "data": []},
        ]

        # Act
        client = RobustMCPClient(base_client=mock_mcp_client)
        result = await client.call_tool("get_posts", {"channel_id": "onaboka"})

        # Assert
        assert result["status"] == "success"
        assert mock_mcp_client.call_tool.call_count == 3

    async def test_call_tool_retry_on_connection_error(self, mock_mcp_client):
        """Test retry logic on connection error.

        Args:
            mock_mcp_client: Mock MCP client fixture
        """
        # Arrange
        # First call fails, second succeeds
        mock_mcp_client.call_tool.side_effect = [
            MCPConnectionError("Connection refused"),
            {"status": "success", "data": []},
        ]

        # Act
        client = RobustMCPClient(base_client=mock_mcp_client)
        result = await client.call_tool("get_posts", {"channel_id": "onaboka"})

        # Assert
        assert result["status"] == "success"
        assert mock_mcp_client.call_tool.call_count == 2

    async def test_call_tool_max_retries_exceeded(self, mock_mcp_client):
        """Test that exception is raised after max retries.

        Args:
            mock_mcp_client: Mock MCP client fixture
        """
        # Arrange
        # All calls fail
        mock_mcp_client.call_tool.side_effect = [
            MCPTimeoutError("Timeout"),
            MCPTimeoutError("Timeout"),
            MCPTimeoutError("Timeout"),
        ]

        # Act & Assert
        client = RobustMCPClient(base_client=mock_mcp_client)
        with pytest.raises(MCPClientError):
            await client.call_tool("get_posts", {"channel_id": "onaboka"})

        assert mock_mcp_client.call_tool.call_count == 3

    async def test_call_tool_exponential_backoff(self, mock_mcp_client):
        """Test that retry uses exponential backoff.

        Args:
            mock_mcp_client: Mock MCP client fixture
        """
        # Arrange
        import asyncio

        call_times = []

        async def track_calls(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            # First two calls fail
            if len(call_times) < 3:
                raise MCPTimeoutError("Timeout")
            return {"status": "success"}

        mock_mcp_client.call_tool.side_effect = track_calls

        # Act
        client = RobustMCPClient(base_client=mock_mcp_client)
        await client.call_tool("get_posts", {"channel_id": "onaboka"})

        # Assert
        assert len(call_times) == 3
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Exponential backoff means delay2 should be greater than delay1
            assert delay2 >= delay1 * 0.9  # Allow some tolerance for timing

    async def test_call_tool_no_retry_on_non_retryable_error(self, mock_mcp_client):
        """Test that non-retryable errors are not retried.

        Args:
            mock_mcp_client: Mock MCP client fixture
        """
        # Arrange
        # ValueError is not retryable
        mock_mcp_client.call_tool.side_effect = ValueError("Invalid arguments")

        # Act & Assert
        client = RobustMCPClient(base_client=mock_mcp_client)
        with pytest.raises(ValueError):
            await client.call_tool("get_posts", {"channel_id": "onaboka"})

        assert mock_mcp_client.call_tool.call_count == 1
