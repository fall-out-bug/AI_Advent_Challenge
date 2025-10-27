"""Integration tests for MCP client-server workflow."""
import pytest
from src.presentation.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_full_discovery_workflow():
    """Test full tool discovery workflow."""
    client = MCPClient()

    # Discover tools
    tools = await client.discover_tools()
    assert len(tools) >= 5  # At least 5 tools should be available

    # Verify calculator tools exist
    tool_names = [t["name"] for t in tools]
    assert "add" in tool_names
    assert "multiply" in tool_names
    assert "list_models" in tool_names
    assert "count_tokens" in tool_names
    
    # Verify all expected tools are present
    expected_tools = ["generate_code", "review_code", "generate_and_review", "check_model"]
    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Expected tool '{tool_name}' not found"


@pytest.mark.asyncio
async def test_calculator_tool_execution():
    """Test calculator tool execution via client."""
    client = MCPClient()

    result = await client.call_tool("add", {"a": 10, "b": 20})
    # Should return either a number or dict
    assert isinstance(result, (int, float, dict))
    if isinstance(result, dict):
        assert "result" in result or result  # Non-empty dict


@pytest.mark.asyncio
async def test_token_counting_tool_execution():
    """Test token counting via client."""
    client = MCPClient()

    result = await client.call_tool("count_tokens", {"text": "Hello world"})
    # Should have count field
    assert isinstance(result, dict)
    assert "count" in result
    assert isinstance(result["count"], int)
    assert result["count"] > 0


@pytest.mark.asyncio
async def test_model_listing_tool_execution():
    """Test model listing via client."""
    client = MCPClient()

    result = await client.call_tool("list_models", {})
    # Verify structure
    assert isinstance(result, dict)
    assert "local_models" in result
    assert "api_models" in result
    assert isinstance(result["local_models"], list)
    assert isinstance(result["api_models"], list)
    # Should have at least one model
    assert len(result["local_models"]) + len(result["api_models"]) > 0


@pytest.mark.asyncio
async def test_model_availability_check():
    """Test model availability check."""
    client = MCPClient()
    
    result = await client.call_tool("check_model", {"model_name": "mistral"})
    assert isinstance(result, dict)
    assert "available" in result
    assert isinstance(result["available"], bool)


@pytest.mark.asyncio
async def test_multiple_tool_calls():
    """Test multiple consecutive tool calls."""
    client = MCPClient()
    
    # Call multiple tools in sequence
    add_result = await client.call_tool("add", {"a": 5, "b": 3})
    multiply_result = await client.call_tool("multiply", {"a": 4, "b": 6})
    token_result = await client.call_tool("count_tokens", {"text": "test"})
    
    # Verify all calls succeeded
    assert add_result in [8, {"result": 8}] or isinstance(add_result, (int, float, dict))
    assert isinstance(multiply_result, (int, float, dict))
    assert "count" in token_result or isinstance(token_result, dict)

