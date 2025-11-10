"""Tests for MCP Tools Registry.

Following TDD approach: tests written BEFORE implementation (Red phase).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from src.presentation.mcp.tools_registry import MCPToolsRegistry
from src.domain.agents.schemas import ToolMetadata


@pytest.mark.asyncio
class TestMCPToolsRegistry:
    """Test suite for MCPToolsRegistry."""

    async def test_discover_tools_success(self, mock_mcp_client, sample_tools_metadata):
        """Test successful tool discovery.

        Args:
            mock_mcp_client: Mock MCP client fixture
            sample_tools_metadata: Sample tools metadata fixture
        """
        # Arrange
        mock_mcp_client.discover_tools.return_value = sample_tools_metadata

        # Act
        registry = MCPToolsRegistry(mcp_client=mock_mcp_client)
        tools = await registry.discover_tools()

        # Assert
        assert len(tools) == 3
        assert tools[0].name == "get_posts"
        assert tools[1].name == "generate_summary"
        assert tools[2].name == "export_pdf"

    async def test_discover_tools_empty_list(self, mock_mcp_client):
        """Test discovery with empty tools list.

        Args:
            mock_mcp_client: Mock MCP client fixture
        """
        # Arrange
        mock_mcp_client.discover_tools.return_value = []

        # Act
        registry = MCPToolsRegistry(mcp_client=mock_mcp_client)
        tools = await registry.discover_tools()

        # Assert
        assert len(tools) == 0

    async def test_discover_tools_cache(self, mock_mcp_client, sample_tools_metadata):
        """Test that tools are cached after first discovery.

        Args:
            mock_mcp_client: Mock MCP client fixture
            sample_tools_metadata: Sample tools metadata fixture
        """
        # Arrange
        mock_mcp_client.discover_tools.return_value = sample_tools_metadata

        # Act
        registry = MCPToolsRegistry(mcp_client=mock_mcp_client)
        tools1 = await registry.discover_tools()
        tools2 = await registry.discover_tools()

        # Assert
        assert mock_mcp_client.discover_tools.call_count == 1
        assert len(tools1) == len(tools2)
        assert tools1[0].name == tools2[0].name

    async def test_build_tools_prompt(self, mock_mcp_client, sample_tools_metadata):
        """Test building tools prompt from metadata.

        Args:
            mock_mcp_client: Mock MCP client fixture
            sample_tools_metadata: Sample tools metadata fixture
        """
        # Arrange
        mock_mcp_client.discover_tools.return_value = sample_tools_metadata

        # Act
        registry = MCPToolsRegistry(mcp_client=mock_mcp_client)
        await registry.discover_tools()
        prompt = registry.build_tools_prompt()

        # Assert
        assert "get_posts" in prompt
        assert "generate_summary" in prompt
        assert "export_pdf" in prompt
        assert "channel_id" in prompt
        assert "posts_text" in prompt

    @pytest.mark.parametrize("tool_count", [0, 1, 10, 100])
    async def test_discover_tools_edge_cases(self, mock_mcp_client, tool_count):
        """Test tool discovery with various tool counts.

        Args:
            mock_mcp_client: Mock MCP client fixture
            tool_count: Number of tools to return
        """
        # Arrange
        tools = [
            {
                "name": f"tool_{i}",
                "description": f"Tool {i} description",
                "input_schema": {"type": "object"},
            }
            for i in range(tool_count)
        ]
        mock_mcp_client.discover_tools.return_value = tools

        # Act
        registry = MCPToolsRegistry(mcp_client=mock_mcp_client)
        result = await registry.discover_tools()

        # Assert
        assert len(result) == tool_count
