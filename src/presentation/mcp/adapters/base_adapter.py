"""Base adapter with common utilities for MCP adapters."""

from typing import Any, Callable, TypeVar

from src.presentation.mcp.exceptions import MCPBaseException

T = TypeVar("T")


def _get_unified_client():
    """Import UnifiedModelClient at runtime."""
    from shared_package.clients.unified_client import UnifiedModelClient

    return UnifiedModelClient


def _get_model_configs():
    """Import MODEL_CONFIGS at runtime."""
    from shared_package.config.models import MODEL_CONFIGS

    return MODEL_CONFIGS


class BaseMCPAdapter:
    """Base adapter with common error handling and utilities."""

    def __init__(self, unified_client: Any) -> None:
        """Initialize base adapter."""
        self.unified_client = unified_client

    def safe_execute(
        self,
        operation: Callable[[], T],
        error_message: str,
        exception_type: type[MCPBaseException] = MCPBaseException,
        **context: Any,
    ) -> T:
        """Execute operation with standardized error handling."""
        try:
            return operation()
        except exception_type:
            raise
        except Exception as e:
            raise exception_type(f"{error_message}: {e}", **context)

    async def safe_execute_async(
        self,
        operation: Callable[[], T],
        error_message: str,
        exception_type: type[MCPBaseException] = MCPBaseException,
        **context: Any,
    ) -> T:
        """Execute async operation with standardized error handling."""
        try:
            return await operation()
        except exception_type:
            raise
        except Exception as e:
            raise exception_type(f"{error_message}: {e}", **context)

    def get_unified_client_class(self) -> type:
        """Get UnifiedModelClient class for lazy import."""
        return _get_unified_client()

    def get_model_configs(self) -> dict[str, Any]:
        """Get model configurations for lazy import."""
        return _get_model_configs()
