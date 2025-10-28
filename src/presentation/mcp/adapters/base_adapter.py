"""Base adapter with common utilities for MCP adapters."""

import sys
from pathlib import Path
from typing import Any, Callable, TypeVar

# Add shared to path for imports
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

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
    """Base adapter with common error handling and utilities.

    Provides shared functionality for all MCP adapters including:
    - Standardized error handling
    - Lazy imports
    - Safe model request execution
    """

    def __init__(self, unified_client: Any) -> None:
        """Initialize base adapter.

        Args:
            unified_client: Unified model client instance
        """
        self.unified_client = unified_client

    def safe_execute(
        self,
        operation: Callable[[], T],
        error_message: str,
        exception_type: type[MCPBaseException] = MCPBaseException,
        **context: Any,
    ) -> T:
        """Execute operation with standardized error handling.

        Args:
            operation: Function to execute
            error_message: Error message for exceptions
            exception_type: Exception type to raise
            **context: Additional context for exceptions

        Returns:
            Operation result

        Raises:
            exception_type: If operation fails
        """
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
        """Execute async operation with standardized error handling.

        Args:
            operation: Async function to execute
            error_message: Error message for exceptions
            exception_type: Exception type to raise
            **context: Additional context for exceptions

        Returns:
            Operation result

        Raises:
            exception_type: If operation fails
        """
        try:
            return await operation()
        except exception_type:
            raise
        except Exception as e:
            raise exception_type(f"{error_message}: {e}", **context)

    def get_unified_client_class(self) -> type:
        """Get UnifiedModelClient class for lazy import.

        Returns:
            UnifiedModelClient class
        """
        return _get_unified_client()

    def get_model_configs(self) -> dict[str, Any]:
        """Get model configurations for lazy import.

        Returns:
            MODEL_CONFIGS dictionary
        """
        return _get_model_configs()

