"""Tests for base MCP adapter utilities."""

from unittest.mock import Mock

import pytest

from src.presentation.mcp.adapters.base_adapter import BaseMCPAdapter
from src.presentation.mcp.exceptions import MCPBaseException, MCPModelError


class TestBaseMCPAdapter:
    """Test suite for BaseMCPAdapter."""

    def test_init(self):
        """Test adapter initialization."""
        mock_client = Mock()
        adapter = BaseMCPAdapter(mock_client)

        assert adapter.unified_client is mock_client

    def test_safe_execute_success(self):
        """Test successful safe execution."""
        adapter = BaseMCPAdapter(Mock())

        result = adapter.safe_execute(lambda: "success", "Operation failed")

        assert result == "success"

    def test_safe_execute_raises_base_exception(self):
        """Test safe_execute raises MCPBaseException on failure."""
        adapter = BaseMCPAdapter(Mock())

        with pytest.raises(MCPBaseException) as exc_info:
            adapter.safe_execute(
                lambda: (_ for _ in ()).throw(ValueError("Test error")),
                "Test operation failed",
            )

        assert "Test operation failed" in str(exc_info.value)

    def test_safe_execute_re_raises_specific_exception(self):
        """Test safe_execute re-raises specific exceptions."""
        adapter = BaseMCPAdapter(Mock())

        with pytest.raises(MCPModelError):
            adapter.safe_execute(
                lambda: (_ for _ in ()).throw(MCPModelError("Specific error")),
                "Generic operation failed",
                exception_type=MCPBaseException,
            )

    @pytest.mark.asyncio
    async def test_safe_execute_async_success(self):
        """Test successful async safe execution."""
        adapter = BaseMCPAdapter(Mock())

        async def async_op():
            return "async_success"

        result = await adapter.safe_execute_async(async_op, "Async operation failed")

        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_safe_execute_async_raises_exception(self):
        """Test safe_execute_async raises exception on failure."""
        adapter = BaseMCPAdapter(Mock())

        with pytest.raises(MCPBaseException):
            await adapter.safe_execute_async(
                lambda: (_ for _ in ()).throw(ValueError("Async error")),
                "Async operation failed",
            )
