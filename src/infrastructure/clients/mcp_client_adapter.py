"""Adapter making RobustMCPClient compatible with domain ToolClientProtocol.

Following Clean Architecture: bridges presentation layer MCP client
with domain layer protocol requirements.
"""

import logging
from typing import Any, Dict, List

from src.domain.interfaces.tool_client import ToolClientProtocol
from src.infrastructure.clients.mcp_client_robust import RobustMCPClient

logger = logging.getLogger(__name__)


class MCPToolClientAdapter:
    """Adapter making RobustMCPClient compatible with domain ToolClientProtocol.

    Purpose:
        Bridges presentation layer RobustMCPClient with domain ToolClientProtocol.
        Enables domain layer to use MCP tools without depending on presentation layer.

    Example:
        >>> from src.infrastructure.clients.mcp_client_adapter import MCPToolClientAdapter
        >>> from src.infrastructure.clients.mcp_client_robust import RobustMCPClient
        >>> from src.presentation.mcp.client import MCPClient
        >>>
        >>> base_client = MCPClient()
        >>> robust_client = RobustMCPClient(base_client=base_client)
        >>> adapter = MCPToolClientAdapter(robust_client=robust_client)
        >>> tools = await adapter.discover_tools()
        >>> result = await adapter.call_tool("create_task", {"title": "Test"})
    """

    def __init__(self, robust_client: RobustMCPClient) -> None:
        """Initialize adapter.

        Args:
            robust_client: RobustMCPClient instance to wrap
        """
        self.robust_client = robust_client
        logger.debug("MCPToolClientAdapter initialized")

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover all available tools.

        Returns:
            List of tool metadata dictionaries, each containing:
            - name: Tool name
            - description: Tool description
            - input_schema: JSON schema for tool parameters

        Raises:
            Exception: If tool discovery fails
        """
        try:
            tools = await self.robust_client.discover_tools()
            logger.debug(f"Discovered {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}", exc_info=True)
            raise

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool with arguments.

        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of tool parameters

        Returns:
            Dictionary with tool execution result

        Raises:
            Exception: If tool execution fails
        """
        try:
            result = await self.robust_client.call_tool(
                tool_name=tool_name, arguments=arguments
            )
            logger.debug(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(
                f"Tool {tool_name} execution failed: {e}",
                exc_info=True,
            )
            raise

