"""Tests for MCP server tools."""

import pytest

from src.presentation.mcp.server import add, count_tokens, list_models, multiply


def test_add_tool():
    """Test addition tool."""
    result = add(5, 3)
    assert result == 8


def test_multiply_tool():
    """Test multiplication tool."""
    result = multiply(4, 3)
    assert result == 12


def test_count_tokens_tool():
    """Test token counting tool."""
    result = count_tokens("Hello world")
    assert "count" in result
    assert result["count"] > 0


@pytest.mark.asyncio
async def test_list_models_tool():
    """Test model listing tool."""
    result = await list_models()
    assert "local_models" in result
    assert isinstance(result["local_models"], list)
    assert "api_models" in result
    assert isinstance(result["api_models"], list)


@pytest.mark.asyncio
async def test_check_model_tool():
    """Test model checking tool."""
    from src.presentation.mcp.server import check_model

    result = await check_model("qwen")
    assert "available" in result
    assert isinstance(result["available"], bool)
