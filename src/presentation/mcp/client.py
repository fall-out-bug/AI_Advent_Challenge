"""MCP client for tool discovery and execution."""
import os
from typing import Any, Dict, List, Protocol
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClientProtocol(Protocol):
    """Protocol for MCP client implementations."""
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover all available tools."""
        ...
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool with arguments."""
        ...


class MCPClient:
    """Client for discovering and executing MCP tools."""

    def __init__(self, server_script: str = "src/presentation/mcp/server.py"):
        """Initialize MCP client.

        Args:
            server_script: Path to MCP server script
        """
        self.server_script = server_script
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_script],
        )
        self.session: ClientSession | None = None

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover all available tools.

        Returns:
            List of tool metadata dictionaries
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()

                tools = []
                for tool in tools_response.tools:
                    tools.append(
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                        }
                    )

                return tools

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool with arguments.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                if result.content and len(result.content) > 0:
                    # Handle text content
                    if hasattr(result.content[0], "text"):
                        import json

                        try:
                            return json.loads(result.content[0].text)
                        except json.JSONDecodeError:
                            return {"result": result.content[0].text}
                    # Handle dict content
                    elif isinstance(result.content[0], dict):
                        return result.content[0]
                return {}

    async def interactive_mode(self) -> None:
        """Interactive CLI for tool exploration."""
        print("MCP Interactive Mode")
        print("Commands: list, call <tool> <args>, quit")

        while True:
            command = input("\nmcp> ").strip()

            if command == "quit":
                break
            elif command == "list":
                tools = await self.discover_tools()
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")
            elif command.startswith("call "):
                # TODO: Parse and execute tool call
                print("Tool call parsing not yet implemented")
            else:
                print(f"Unknown command: {command}")


def get_mcp_client(server_url: str | None = None) -> MCPClientProtocol:
    """Get appropriate MCP client based on configuration.
    
    Args:
        server_url: MCP server URL (HTTP) or None for stdio mode
        
    Returns:
        MCPClientProtocol instance (HTTP or stdio)
    """
    url = server_url or os.getenv("MCP_SERVER_URL", "")
    
    if url and url.startswith("http"):
        # Use HTTP client
        from src.presentation.mcp.http_client import MCPHTTPClient
        return MCPHTTPClient(base_url=url)
    
    # Default to stdio client
    return MCPClient()

