"""HTTP client for MCP server over network."""
import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPHTTPClient:
    """HTTP client for discovering and executing MCP tools over network."""

    def __init__(self, base_url: str = "http://localhost:8004"):
        """Initialize MCP HTTP client.

        Args:
            base_url: Base URL of the MCP HTTP server
        """
        self.base_url = base_url.rstrip("/")
        # Increased timeout for long-running operations like digest generation
        # Digest can take up to 5 minutes (fetching posts + summarization)
        self.timeout = httpx.Timeout(600.0, connect=10.0)  # 10 min total, 10 sec connect

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to MCP server.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response data
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == "GET":
                    response = await client.get(url)
                elif method == "POST":
                    response = await client.post(url, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed: {e}")
            raise Exception(f"HTTP request failed: {str(e)}")

    async def check_health(self) -> bool:
        """Check if MCP server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            result = await self._make_request("GET", "/health")
            return result.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover all available tools.

        Returns:
            List of tool metadata dictionaries
        """
        try:
            result = await self._make_request("GET", "/tools")
            return result.get("tools", [])
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            raise Exception(f"Failed to discover tools: {str(e)}")

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
        try:
            result = await self._make_request(
                "POST", 
                "/call",
                data={"tool_name": tool_name, "arguments": arguments}
            )
            return result.get("result", {})
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            raise Exception(f"Failed to call tool: {str(e)}")
