"""MCP Tools Registry for discovering and caching tools.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from src.domain.agents.schemas import ToolMetadata
from src.presentation.mcp.client import MCPClientProtocol

logger = logging.getLogger(__name__)


class MCPToolsRegistry:
    """Registry for MCP tools discovery and caching.
    
    Purpose:
        Discover MCP tools and build prompt sections describing them.
        Cache tools in memory to avoid repeated discovery.
    
    Example:
        >>> from src.presentation.mcp.tools_registry import MCPToolsRegistry
        >>> from src.presentation.mcp.client import MCPClient
        >>>
        >>> client = MCPClient()
        >>> registry = MCPToolsRegistry(mcp_client=client)
        >>> tools = await registry.discover_tools()
        >>> prompt = registry.build_tools_prompt()
    """
    
    def __init__(self, mcp_client: MCPClientProtocol, cache_ttl_seconds: int = 300):
        """Initialize registry.
        
        Args:
            mcp_client: MCP client for discovering tools
            cache_ttl_seconds: Cache TTL in seconds (default 5 minutes)
        """
        self.mcp_client = mcp_client
        self.cache_ttl_seconds = cache_ttl_seconds
        self._tools: Optional[List[ToolMetadata]] = None
        self._cache_timestamp: Optional[datetime] = None
    
    async def discover_tools(self) -> List[ToolMetadata]:
        """Discover all available MCP tools.
        
        Returns:
            List of tool metadata
        
        Raises:
            Exception: If tool discovery fails
        """
        if self._is_cache_valid():
            return self._tools or []
        
        raw_tools = await self._fetch_tools()
        parsed_tools = self._parse_tool_metadata(raw_tools)
        self._cache_tools(parsed_tools)
        return parsed_tools
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid.
        
        Returns:
            True if cache is valid, False otherwise
        """
        if self._tools is None or self._cache_timestamp is None:
            return False
        
        elapsed = (datetime.utcnow() - self._cache_timestamp).total_seconds()
        return elapsed < self.cache_ttl_seconds
    
    async def _fetch_tools(self) -> List[dict]:
        """Fetch tools from MCP client.
        
        Returns:
            List of raw tool dictionaries
        
        Raises:
            Exception: If fetch fails
        """
        try:
            return await self.mcp_client.discover_tools()
        except Exception as e:
            logger.error(f"Failed to fetch tools: {e}")
            raise
    
    def _parse_tool_metadata(self, raw_tools: List[dict]) -> List[ToolMetadata]:
        """Parse raw tools into ToolMetadata objects.
        
        Args:
            raw_tools: Raw tool dictionaries from MCP
        
        Returns:
            List of ToolMetadata objects
        """
        parsed = []
        for tool in raw_tools:
            try:
                metadata = ToolMetadata(
                    name=tool["name"],
                    description=tool["description"],
                    input_schema=tool.get("input_schema", {})
                )
                parsed.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to parse tool {tool.get('name', 'unknown')}: {e}")
        return parsed
    
    def _cache_tools(self, tools: List[ToolMetadata]) -> None:
        """Cache tools in memory.
        
        Args:
            tools: List of tools to cache
        """
        self._tools = tools
        self._cache_timestamp = datetime.utcnow()
        logger.debug(f"Cached {len(tools)} tools")
    
    def build_tools_prompt(self) -> str:
        """Build prompt section describing all tools.
        
        Returns:
            Formatted prompt text with tool descriptions
        """
        if not self._tools:
            return "No tools available."
        
        sections = ["Available tools:"]
        for tool in self._tools:
            section = self._format_tool_description(tool)
            sections.append(section)
        
        return "\n\n".join(sections)
    
    def _format_tool_description(self, tool: ToolMetadata) -> str:
        """Format single tool description.
        
        Args:
            tool: Tool metadata
        
        Returns:
            Formatted tool description string
        """
        params = self._extract_parameters(tool.input_schema)
        param_desc = ", ".join(params) if params else "no parameters"
        
        return (
            f"- {tool.name}: {tool.description}\n"
            f"  Parameters: {param_desc}"
        )
    
    def _extract_parameters(self, schema: dict) -> List[str]:
        """Extract parameter names from schema.
        
        Args:
            schema: JSON schema dictionary
        
        Returns:
            List of parameter names
        """
        props = schema.get("properties", {})
        required = schema.get("required", [])
        
        params = []
        for param_name, param_schema in props.items():
            param_type = param_schema.get("type", "any")
            required_mark = "*" if param_name in required else ""
            params.append(f"{param_name}{required_mark}({param_type})")
        
        return params

