"""Tests for MCP Aware Agent.

Following TDD approach: tests written BEFORE implementation (Red phase).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from src.domain.agents.mcp_aware_agent import MCPAwareAgent
from src.domain.agents.schemas import AgentRequest, AgentResponse
from shared_package.clients.unified_client import UnifiedModelClient
from shared_package.clients.base_client import ModelResponse


@pytest.mark.asyncio
class TestMCPAwareAgent:
    """Test suite for MCPAwareAgent."""
    
    async def test_agent_initialization(self, mock_mcp_client, mock_llm_client):
        """Test agent initialization.
        
        Args:
            mock_mcp_client: Mock MCP client fixture
            mock_llm_client: Mock LLM client fixture
        """
        # Arrange & Act
        agent = MCPAwareAgent(
            mcp_client=mock_mcp_client,
            llm_client=mock_llm_client
        )
        
        # Assert
        assert agent.mcp_client == mock_mcp_client
        assert agent.llm_client == mock_llm_client
        assert agent.registry is not None
    
    async def test_process_request_success(
        self,
        mock_mcp_client,
        mock_llm_client,
        mock_agent_request,
        mock_agent_response
    ):
        """Test successful request processing.
        
        Args:
            mock_mcp_client: Mock MCP client fixture
            mock_llm_client: Mock LLM client fixture
            mock_agent_request: Mock agent request fixture
            mock_agent_response: Mock agent response fixture
        """
        # Arrange
        mock_llm_client.make_request = AsyncMock(
            return_value=ModelResponse(
                response='{"tool": "get_posts", "args": {"channel_id": "onaboka"}}',
                response_tokens=50,
                input_tokens=50,
                total_tokens=100,
                model_name="mistral",
                response_time=1.0
            )
        )
        mock_mcp_client.discover_tools = AsyncMock(
            return_value=[
                {
                    "name": "get_posts",
                    "description": "Get posts",
                    "input_schema": {
                        "type": "object",
                        "properties": {"channel_id": {"type": "string"}},
                        "required": ["channel_id"]
                    }
                }
            ]
        )
        mock_mcp_client.call_tool.return_value = {"status": "success", "data": []}
        
        request = AgentRequest(**mock_agent_request)
        
        # Act
        agent = MCPAwareAgent(
            mcp_client=mock_mcp_client,
            llm_client=mock_llm_client
        )
        response = await agent.process(request)
        
        # Assert
        assert response.success is True
        assert len(response.tools_used) > 0
    
    async def test_process_request_tool_selection(
        self,
        mock_mcp_client,
        mock_llm_client,
        mock_agent_request,
        sample_tools_metadata
    ):
        """Test that agent correctly selects tools from prompt.
        
        Args:
            mock_mcp_client: Mock MCP client fixture
            mock_llm_client: Mock LLM client fixture
            mock_agent_request: Mock agent request fixture
            sample_tools_metadata: Sample tools metadata fixture
        """
        # Arrange
        mock_mcp_client.discover_tools = AsyncMock(
            return_value=sample_tools_metadata
        )
        mock_llm_client.make_request = AsyncMock(
            return_value=ModelResponse(
                response='{"tool": "get_posts", "args": {"channel_id": "onaboka", "limit": 100}}',
                response_tokens=50,
                input_tokens=50,
                total_tokens=100,
                model_name="mistral",
                response_time=1.0
            )
        )
        mock_mcp_client.call_tool.return_value = {"status": "success", "data": []}
        
        request = AgentRequest(**mock_agent_request)
        
        # Act
        agent = MCPAwareAgent(
            mcp_client=mock_mcp_client,
            llm_client=mock_llm_client
        )
        response = await agent.process(request)
        
        # Assert
        assert mock_mcp_client.call_tool.called
        call_args = mock_mcp_client.call_tool.call_args
        assert call_args[0][0] == "get_posts"
        assert response.success is True
        assert "get_posts" in response.tools_used
    
    async def test_process_request_invalid_tool(
        self,
        mock_mcp_client,
        mock_llm_client,
        mock_agent_request
    ):
        """Test handling of invalid tool selection.
        
        Args:
            mock_mcp_client: Mock MCP client fixture
            mock_llm_client: Mock LLM client fixture
            mock_agent_request: Mock agent request fixture
        """
        # Arrange
        mock_mcp_client.discover_tools = AsyncMock(
            return_value=[
                {
                    "name": "get_posts",
                    "description": "Get posts",
                    "input_schema": {
                        "type": "object",
                        "properties": {"channel_id": {"type": "string"}},
                        "required": ["channel_id"]
                    }
                }
            ]
        )
        mock_llm_client.make_request = AsyncMock(
            return_value=ModelResponse(
                response='{"tool": "nonexistent_tool", "args": {}}',
                response_tokens=50,
                input_tokens=50,
                total_tokens=100,
                model_name="mistral",
                response_time=1.0
            )
        )
        
        request = AgentRequest(**mock_agent_request)
        
        # Act
        agent = MCPAwareAgent(
            mcp_client=mock_mcp_client,
            llm_client=mock_llm_client
        )
        response = await agent.process(request)
        
        # Assert
        assert response.success is False
        assert response.error is not None
        assert "nonexistent_tool" in response.error.lower() or "invalid" in response.error.lower()
    
    async def test_process_request_llm_error(
        self,
        mock_mcp_client,
        mock_llm_client,
        mock_agent_request
    ):
        """Test handling of LLM errors.
        
        Args:
            mock_mcp_client: Mock MCP client fixture
            mock_llm_client: Mock LLM client fixture
            mock_agent_request: Mock agent request fixture
        """
        # Arrange
        mock_llm_client.make_request.side_effect = Exception("LLM service unavailable")
        request = AgentRequest(**mock_agent_request)
        
        # Act
        agent = MCPAwareAgent(
            mcp_client=mock_mcp_client,
            llm_client=mock_llm_client
        )
        response = await agent.process(request)
        
        # Assert
        assert response.success is False
        assert response.error is not None

