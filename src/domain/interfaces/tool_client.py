"""Protocol for tool execution clients.

This protocol defines the interface for MCP tool clients.
Infrastructure layer implementations must conform to this protocol.
"""

from typing import Protocol, List, Dict, Any


class ToolClientProtocol(Protocol):
    """Protocol for tool execution clients.

    Following Clean Architecture, this protocol is defined in domain layer
    while implementations reside in infrastructure/presentation layers.

    Methods:
        discover_tools: Discover all available tools
        call_tool: Execute a tool with given parameters
    """

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
        ...

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
        ...

