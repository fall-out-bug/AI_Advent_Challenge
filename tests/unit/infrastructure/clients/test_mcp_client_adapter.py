"""Tests for MCPToolClientAdapter.

Following TDD approach with comprehensive test coverage.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.clients.mcp_client_adapter import MCPToolClientAdapter
from src.infrastructure.clients.mcp_client_robust import RobustMCPClient


@pytest.fixture
def mock_robust_client():
    """Mock RobustMCPClient for testing.

    Returns:
        Mocked RobustMCPClient
    """
    mock_client = AsyncMock(spec=RobustMCPClient)
    return mock_client


@pytest.mark.asyncio
class TestMCPToolClientAdapter:
    """Test suite for MCPToolClientAdapter."""

    async def test_discover_tools_success(self, mock_robust_client):
        """Test successful tool discovery.

        Args:
            mock_robust_client: Mocked RobustMCPClient
        """
        # Arrange
        expected_tools = [
            {
                "name": "create_task",
                "description": "Create a new task",
                "input_schema": {"type": "object"},
            },
            {
                "name": "get_posts",
                "description": "Get channel posts",
                "input_schema": {"type": "object"},
            },
        ]
        mock_robust_client.discover_tools = AsyncMock(return_value=expected_tools)

        # Act
        adapter = MCPToolClientAdapter(robust_client=mock_robust_client)
        result = await adapter.discover_tools()

        # Assert
        assert result == expected_tools
        assert len(result) == 2
        mock_robust_client.discover_tools.assert_called_once()

    async def test_discover_tools_failure(self, mock_robust_client):
        """Test tool discovery failure propagates exception.

        Args:
            mock_robust_client: Mocked RobustMCPClient
        """
        # Arrange
        mock_robust_client.discover_tools = AsyncMock(
            side_effect=Exception("Discovery failed")
        )

        # Act & Assert
        adapter = MCPToolClientAdapter(robust_client=mock_robust_client)
        with pytest.raises(Exception, match="Discovery failed"):
            await adapter.discover_tools()

        mock_robust_client.discover_tools.assert_called_once()

    async def test_call_tool_success(self, mock_robust_client):
        """Test successful tool call.

        Args:
            mock_robust_client: Mocked RobustMCPClient
        """
        # Arrange
        expected_result = {"status": "success", "task_id": "123"}
        mock_robust_client.call_tool = AsyncMock(return_value=expected_result)

        # Act
        adapter = MCPToolClientAdapter(robust_client=mock_robust_client)
        result = await adapter.call_tool(
            tool_name="create_task", arguments={"title": "Test"}
        )

        # Assert
        assert result == expected_result
        assert result["status"] == "success"
        mock_robust_client.call_tool.assert_called_once_with(
            tool_name="create_task", arguments={"title": "Test"}
        )

    async def test_call_tool_failure(self, mock_robust_client):
        """Test tool call failure propagates exception.

        Args:
            mock_robust_client: Mocked RobustMCPClient
        """
        # Arrange
        mock_robust_client.call_tool = AsyncMock(
            side_effect=Exception("Tool execution failed")
        )

        # Act & Assert
        adapter = MCPToolClientAdapter(robust_client=mock_robust_client)
        with pytest.raises(Exception, match="Tool execution failed"):
            await adapter.call_tool(
                tool_name="create_task", arguments={"title": "Test"}
            )

        mock_robust_client.call_tool.assert_called_once()

    async def test_call_tool_empty_arguments(self, mock_robust_client):
        """Test tool call with empty arguments.

        Args:
            mock_robust_client: Mocked RobustMCPClient
        """
        # Arrange
        expected_result = {"status": "success"}
        mock_robust_client.call_tool = AsyncMock(return_value=expected_result)

        # Act
        adapter = MCPToolClientAdapter(robust_client=mock_robust_client)
        result = await adapter.call_tool(tool_name="get_tasks", arguments={})

        # Assert
        assert result == expected_result
        mock_robust_client.call_tool.assert_called_once_with(
            tool_name="get_tasks", arguments={}
        )

    async def test_adapter_delegates_to_robust_client(self, mock_robust_client):
        """Test that adapter properly delegates all calls.

        Args:
            mock_robust_client: Mocked RobustMCPClient
        """
        # Arrange
        mock_robust_client.discover_tools = AsyncMock(return_value=[])
        mock_robust_client.call_tool = AsyncMock(return_value={})

        # Act
        adapter = MCPToolClientAdapter(robust_client=mock_robust_client)
        await adapter.discover_tools()
        await adapter.call_tool("test_tool", {"arg": "value"})

        # Assert
        mock_robust_client.discover_tools.assert_called_once()
        mock_robust_client.call_tool.assert_called_once_with(
            tool_name="test_tool", arguments={"arg": "value"}
        )
