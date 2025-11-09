"""Multi-MCP Client for aggregating tools from multiple MCP servers.

Following Clean Architecture: aggregates multiple MCP clients into unified interface.
Following Python Zen: Simple is better than complex.
"""

import logging
from typing import Any, Dict, List, Tuple

from src.presentation.mcp.client import MCPClientProtocol
from src.presentation.mcp.exceptions import MCPClientError

logger = logging.getLogger(__name__)


class MultiMCPClient:
    """Aggregates multiple MCP clients into a single interface.

    Purpose:
        Combines tools from multiple MCP servers, allowing butler-bot
        to use tools from local and external MCP servers simultaneously.
        Handles tool name conflicts by preferring first server.

    Example:
        >>> from src.presentation.mcp.client import get_mcp_client
        >>> from src.infrastructure.clients.multi_mcp_client import MultiMCPClient
        >>>
        >>> client1 = get_mcp_client("http://mcp-server:8004")
        >>> client2 = get_mcp_client("http://external-mcp:8005")
        >>> multi_client = MultiMCPClient([
        ...     (client1, "local"),
        ...     (client2, "external")
        ... ])
        >>> tools = await multi_client.discover_tools()
        >>> result = await multi_client.call_tool("get_posts", {"channel": "test"})
    """

    def __init__(self, clients: List[Tuple[MCPClientProtocol, str]]) -> None:
        """Initialize multi-MCP client.

        Args:
            clients: List of (client, server_name) tuples.
                     Server names are used for logging and error messages.
        """
        if not clients:
            raise ValueError("MultiMCPClient requires at least one client")

        self.clients = clients
        self._tool_server_map: Dict[str, str] = {}  # tool_name -> server_name
        logger.info(
            f"MultiMCPClient initialized with {len(clients)} servers: "
            f"{[name for _, name in clients]}"
        )

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover tools from all MCP servers.

        Returns:
            List of tool metadata dictionaries. Tools from first server
            take precedence in case of name conflicts.

        Raises:
            MCPClientError: If all servers fail
        """
        all_tools: Dict[str, Dict[str, Any]] = {}
        errors: List[Tuple[str, Exception]] = []

        for client, server_name in self.clients:
            try:
                tools = await client.discover_tools()
                logger.debug(f"Discovered {len(tools)} tools from {server_name}")

                for tool in tools:
                    tool_name = tool.get("name")
                    if not tool_name:
                        logger.warning(
                            f"Tool without name from {server_name}, skipping"
                        )
                        continue

                    # First server wins in case of conflicts
                    if tool_name not in all_tools:
                        all_tools[tool_name] = tool
                        self._tool_server_map[tool_name] = server_name
                        # Add server metadata to tool
                        tool["_server"] = server_name
                    else:
                        logger.debug(
                            f"Tool '{tool_name}' already exists from "
                            f"{self._tool_server_map[tool_name]}, "
                            f"skipping duplicate from {server_name}"
                        )

            except Exception as e:
                error_msg = f"Failed to discover tools from {server_name}: {e}"
                logger.warning(error_msg)
                errors.append((server_name, e))

        if not all_tools and errors:
            # All servers failed
            error_details = "; ".join([f"{name}: {str(e)}" for name, e in errors])
            raise MCPClientError(f"All MCP servers failed: {error_details}")

        if errors:
            logger.warning(
                f"Some MCP servers failed, but {len(all_tools)} tools "
                f"available from other servers"
            )

        result = list(all_tools.values())
        logger.info(
            f"Total {len(result)} unique tools discovered from "
            f"{len(self.clients) - len(errors)}/{len(self.clients)} servers"
        )
        return result

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call tool from appropriate server.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPClientError: If tool not found or execution fails
        """
        # Find which server has this tool
        server_name = self._tool_server_map.get(tool_name)

        if server_name:
            # Try the mapped server first
            for client, name in self.clients:
                if name == server_name:
                    try:
                        logger.debug(
                            f"Calling tool '{tool_name}' from server '{server_name}'"
                        )
                        return await client.call_tool(tool_name, arguments)
                    except Exception as e:
                        logger.error(
                            f"Failed to call tool '{tool_name}' from "
                            f"server '{server_name}': {e}"
                        )
                        raise MCPClientError(
                            f"Tool '{tool_name}' execution failed on "
                            f"server '{server_name}': {e}"
                        ) from e

        # Tool not found in cache, try all servers
        logger.warning(f"Tool '{tool_name}' not in cache, searching all servers")
        for client, name in self.clients:
            try:
                # Try to call - will fail if tool doesn't exist
                result = await client.call_tool(tool_name, arguments)
                # Success - update cache
                self._tool_server_map[tool_name] = name
                logger.debug(
                    f"Found and called tool '{tool_name}' from server '{name}'"
                )
                return result
            except Exception as e:
                # Tool doesn't exist on this server, try next
                logger.debug(
                    f"Tool '{tool_name}' not available on server '{name}': {e}"
                )
                continue

        # Tool not found on any server
        available_servers = [name for _, name in self.clients]
        raise MCPClientError(
            f"Tool '{tool_name}' not found on any server. "
            f"Available servers: {available_servers}"
        )
