"""Robust MCP Client with retry logic.

Following Python Zen:
- Errors should never pass silently
- In the face of ambiguity, refuse the temptation to guess
"""

import logging
import asyncio
import time
from typing import Any, Dict, List

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from src.presentation.mcp.client import MCPClientProtocol
from src.presentation.mcp.exceptions import (
    MCPTimeoutError,
    MCPConnectionError,
    MCPClientError
)

try:
    from src.infrastructure.monitoring.agent_metrics import MCPClientMetrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RobustMCPClient:
    """MCP client with retry logic and error handling.
    
    Purpose:
        Wrap base MCP client with retry logic for transient errors.
        Uses exponential backoff and classifies errors as retryable/non-retryable.
    
    Example:
        >>> from src.infrastructure.clients.mcp_client_robust import RobustMCPClient
        >>> from src.presentation.mcp.client import MCPClient
        >>>
        >>> base_client = MCPClient()
        >>> robust_client = RobustMCPClient(base_client=base_client)
        >>> tools = await robust_client.discover_tools()
        >>> result = await robust_client.call_tool("get_posts", {"channel_id": "test"})
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_WAIT = 1.0  # seconds
    MAX_WAIT = 10.0  # seconds
    EXPONENTIAL_BASE = 2.0
    
    # Retryable exceptions
    RETRYABLE_EXCEPTIONS = (
        MCPTimeoutError,
        MCPConnectionError,
        TimeoutError,
        ConnectionError,
        asyncio.TimeoutError
    )
    
    def __init__(self, base_client: MCPClientProtocol):
        """Initialize robust client.
        
        Args:
            base_client: Base MCP client to wrap
        """
        self.base_client = base_client
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover tools with retry logic.
        
        Returns:
            List of tool metadata
        
        Raises:
            MCPClientError: If discovery fails after retries
        """
        return await self._retry_call(
            self.base_client.discover_tools
        )
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call tool with retry logic.
        
        Args:
            tool_name: Tool name
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        
        Raises:
            MCPClientError: If call fails after retries
            ValueError: If arguments are invalid (not retried)
        """
        start_time = time.time()
        retry_count = 0
        
        try:
            result = await self._retry_call(
                self.base_client.call_tool,
                tool_name,
                arguments
            )
            
            duration = time.time() - start_time
            
            # Record metrics
            if METRICS_AVAILABLE:
                MCPClientMetrics.record_request(
                    tool_name=tool_name,
                    success=True,
                    duration=duration,
                    retries=retry_count
                )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            if METRICS_AVAILABLE:
                MCPClientMetrics.record_request(
                    tool_name=tool_name,
                    success=False,
                    duration=duration,
                    retries=retry_count
                )
            
            raise
    
    async def _retry_call(
        self,
        func,
        *args,
        **kwargs
    ) -> Any:
        """Call function with retry logic.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            MCPClientError: If call fails after retries
        """
        try:
            return await self._execute_with_retry(func, *args, **kwargs)
        except RetryError as e:
            last_exception = e.last_attempt.exception()
            logger.error(
                f"Max retries exceeded: {last_exception}",
                exc_info=True
            )
            raise MCPClientError(
                f"Operation failed after {self.MAX_RETRIES} retries: {last_exception}"
            ) from last_exception
        except Exception as e:
            if not self._is_retryable(e):
                raise
            logger.error(f"Unexpected retryable error: {e}", exc_info=True)
            raise MCPClientError(f"Operation failed: {e}") from e
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(
            multiplier=INITIAL_WAIT,
            max=MAX_WAIT,
            exp_base=EXPONENTIAL_BASE
        ),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True
    )
    async def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute function with retry decorator.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception: If execution fails
        """
        exception = None
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            exception = self._classify_exception(e)
            if exception:
                raise exception
            raise
    
    def _classify_exception(self, error: Exception) -> Exception | None:
        """Classify exception as retryable error.
        
        Args:
            error: Exception to classify
        
        Returns:
            Classified exception or None
        """
        error_str = str(error).lower()
        
        # Check for timeout patterns
        if any(word in error_str for word in ["timeout", "timed out"]):
            return MCPTimeoutError(str(error))
        
        # Check for connection patterns
        if any(word in error_str for word in [
            "connection", "connect", "refused", "reset", "closed"
        ]):
            return MCPConnectionError(str(error))
        
        # Check instance type
        if isinstance(error, self.RETRYABLE_EXCEPTIONS):
            return error
        
        # Non-retryable
        return None
    
    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable.
        
        Args:
            error: Exception to check
        
        Returns:
            True if retryable
        """
        return isinstance(error, self.RETRYABLE_EXCEPTIONS) or (
            self._classify_exception(error) is not None
        )

