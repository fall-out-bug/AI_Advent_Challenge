"""MCP wrapper bridging Mistral orchestrator to MCP client.

Following separation of concerns: MCP-specific logic stays in presentation layer.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from src.application.orchestrators.mistral_orchestrator import MistralChatOrchestrator
from src.application.services.result_cache import ResultCache
from src.domain.entities.conversation import ExecutionPlan

logger = logging.getLogger(__name__)


class MCPMistralWrapper:
    """Wrapper connecting Mistral orchestrator to MCP server."""

    def __init__(
        self,
        server_script: str = None,
        orchestrator: MistralChatOrchestrator = None,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        max_retries: int = 3,
        retry_initial_delay: float = 1.0,
        retry_backoff: float = 2.0,
        use_docker: bool = False,
        docker_url: str = "http://localhost:8004",
    ) -> None:
        """Initialize wrapper.

        Args:
            server_script: Path to MCP server script (for stdio mode)
            orchestrator: Mistral orchestrator instance
            enable_cache: Whether to enable result caching
            cache_ttl: Cache TTL in seconds
            max_retries: Maximum retry attempts
            retry_initial_delay: Initial retry delay in seconds
            retry_backoff: Backoff multiplier
            use_docker: Use Docker MCP server via HTTP
            docker_url: URL of Docker MCP server
        """
        self.use_docker = (
            use_docker or os.getenv("MCP_USE_DOCKER", "false").lower() == "true"
        )
        self.docker_url = docker_url or os.getenv(
            "MCP_DOCKER_URL", "http://localhost:8004"
        )

        # Lazy import to avoid circular dependencies
        if self.use_docker:
            from src.presentation.mcp.http_client import MCPHTTPClient

            self.mcp_client = MCPHTTPClient(base_url=self.docker_url)
            logger.info(f"Using Docker MCP server at {self.docker_url}")
        else:
            from src.presentation.mcp.client import MCPClient

            self.mcp_client = MCPClient(
                server_script=server_script or "src/presentation/mcp/server.py"
            )
            logger.info(f"Using stdio MCP server with script: {server_script}")

        self.orchestrator = orchestrator
        self.available_tools: Dict[str, Any] = {}
        self.enable_cache = enable_cache
        self.cache: Optional[ResultCache] = None

        if enable_cache:
            self.cache = ResultCache(ttl_seconds=cache_ttl)

        # Tools that should not be cached
        self.no_cache_tools = {"formalize_task"}

        # Retry configuration
        self.max_retries = max_retries
        self.retry_initial_delay = retry_initial_delay
        self.retry_backoff = retry_backoff

    async def initialize(self) -> None:
        """Initialize MCP client and discover tools."""
        try:
            tools = await self.mcp_client.discover_tools()
            self.available_tools = {tool["name"]: tool for tool in tools}
            logger.info(f"Discovered {len(self.available_tools)} MCP tools")
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
            self.available_tools = {}

    async def execute_plan(
        self, plan: ExecutionPlan, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Execute plan via MCP tools.

        Args:
            plan: Execution plan
            conversation_id: Conversation identifier

        Returns:
            List of execution results
        """
        results = []
        for step in plan.steps:
            result = await self._call_mcp_tool(step.tool, step.args)
            step.result = result
            results.append(result)
            logger.info(f"Tool {step.tool} completed")
        return results

    async def _call_mcp_tool(
        self, tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call MCP tool with caching.

        Args:
            tool_name: Tool name
            args: Tool arguments

        Returns:
            Tool result
        """
        # Check cache if enabled and tool is cachable
        if self.enable_cache and self.cache and tool_name not in self.no_cache_tools:
            cached_result = self.cache.get(tool_name, args)
            if cached_result is not None:
                logger.debug(f"Cache hit for {tool_name}")
                return cached_result

        try:
            result = await self._execute_tool_with_retry(tool_name, args)

            # Store in cache if enabled
            if (
                self.enable_cache
                and self.cache
                and tool_name not in self.no_cache_tools
            ):
                self.cache.set(tool_name, args, result)

            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e)}

    async def _execute_tool_with_retry(
        self, tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool with exponential backoff retry.

        Args:
            tool_name: Tool name
            args: Tool arguments

        Returns:
            Tool result

        Raises:
            Exception: If all retries exhausted
        """
        last_error = None
        delay = self.retry_initial_delay

        for attempt in range(self.max_retries + 1):
            try:
                result = await self._execute_tool(tool_name, args)
                if attempt > 0:
                    logger.info(f"Tool {tool_name} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"Tool {tool_name} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}, retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    delay *= self.retry_backoff
                else:
                    logger.error(
                        f"Tool {tool_name} failed after {attempt + 1} attempts"
                    )

        raise last_error or Exception(f"Tool {tool_name} execution failed")

    async def _execute_tool(
        self, tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute MCP tool (internal method).

        Args:
            tool_name: Tool name
            args: Tool arguments

        Returns:
            Tool result

        Raises:
            Exception: If tool execution fails
        """
        if tool_name not in self.available_tools:
            raise ValueError(f"Tool {tool_name} not found")

        result = await self.mcp_client.call_tool(tool_name, args)
        logger.debug(f"Tool {tool_name} result: {result}")
        return result if isinstance(result, dict) else {"result": str(result)}

    def get_available_tools(self) -> List[str]:
        """Get list of available tools.

        Returns:
            List of tool names
        """
        return list(self.available_tools.keys())
