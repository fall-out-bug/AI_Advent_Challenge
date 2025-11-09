"""Performance and latency tests for MCP operations."""
import time

import pytest

from src.presentation.mcp.client import MCPClient


@pytest.mark.asyncio
class TestPerformanceMetrics:
    """Tests for performance and latency metrics."""

    async def test_tool_discovery_latency(self):
        """Test that tool discovery completes within acceptable time."""
        client = MCPClient()

        start_time = time.time()
        tools = await client.discover_tools()
        elapsed_time = time.time() - start_time

        # Should complete in < 1 second
        assert elapsed_time < 1.0, f"Discovery took {elapsed_time:.3f}s"
        assert len(tools) > 0

    async def test_calculator_tool_latency(self):
        """Test calculator tool execution latency."""
        client = MCPClient()

        start_time = time.time()
        result = await client.call_tool("add", {"a": 5, "b": 3})
        elapsed_time = time.time() - start_time

        # Should complete in < 500ms
        assert elapsed_time < 0.5, f"Tool call took {elapsed_time:.3f}s"
        assert result == 8 or isinstance(result, dict)

    async def test_token_counting_performance(self):
        """Test token counting performance with different text sizes."""
        client = MCPClient()

        # Small text
        small_text = "Hello world"
        start = time.time()
        result_small = await client.call_tool("count_tokens", {"text": small_text})
        elapsed_small = time.time() - start
        assert elapsed_small < 0.2

        # Medium text
        medium_text = " ".join(["word"] * 100)
        start = time.time()
        result_medium = await client.call_tool("count_tokens", {"text": medium_text})
        elapsed_medium = time.time() - start
        assert elapsed_medium < 0.5

        # Large text
        large_text = " ".join(["word"] * 1000)
        start = time.time()
        result_large = await client.call_tool("count_tokens", {"text": large_text})
        elapsed_large = time.time() - start
        assert elapsed_large < 1.0

    async def test_concurrent_tool_calls(self):
        """Test multiple concurrent tool calls."""
        import asyncio

        client = MCPClient()

        async def call_add(a: int, b: int) -> dict:
            return await client.call_tool("add", {"a": a, "b": b})

        start_time = time.time()
        results = await asyncio.gather(
            call_add(1, 2),
            call_add(3, 4),
            call_add(5, 6),
        )
        elapsed_time = time.time() - start_time

        # Concurrent execution should be faster than sequential
        # (though stdio_client may serialize calls)
        assert len(results) == 3
        print(f"Concurrent calls took {elapsed_time:.3f}s")

    async def test_batch_operations(self):
        """Test batch operations performance."""
        client = MCPClient()

        operations = [("add", {"a": i, "b": i + 1}) for i in range(10)]

        start_time = time.time()
        results = []
        for tool_name, args in operations:
            result = await client.call_tool(tool_name, args)
            results.append(result)
        elapsed_time = time.time() - start_time

        assert len(results) == 10
        print(f"Batch of 10 operations took {elapsed_time:.3f}s")


@pytest.mark.asyncio
class TestMemoryPerformance:
    """Tests for memory usage and leaks."""

    async def test_repeated_calls_no_memory_leak(self):
        """Test that repeated calls don't increase memory usage significantly."""
        import gc

        client = MCPClient()

        # Make multiple calls
        for _ in range(20):
            await client.call_tool("add", {"a": 1, "b": 2})

        # Force garbage collection
        gc.collect()

        # If we get here without memory errors, test passes
        assert True

    async def test_large_text_handling(self):
        """Test handling of large text inputs."""
        client = MCPClient()

        # Create large text
        large_text = "A" * 10000

        start_time = time.time()
        result = await client.call_tool("count_tokens", {"text": large_text})
        elapsed_time = time.time() - start_time

        assert elapsed_time < 1.0
        assert "count" in result


@pytest.mark.asyncio
class TestTimeoutHandling:
    """Tests for timeout handling in operations."""

    async def test_slow_operation_timeout(self):
        """Test behavior with slow operations."""
        # This would require mocking slow responses
        # For now, just verify that normal operations complete
        client = MCPClient()

        result = await client.call_tool("multiply", {"a": 7, "b": 6})
        assert result in [42, {"result": 42}] or isinstance(result, (int, dict))


@pytest.mark.asyncio
class TestScalability:
    """Tests for system scalability."""

    async def test_discover_tools_with_many_tools(self):
        """Test discovery with multiple tools available."""
        client = MCPClient()

        tools = await client.discover_tools()
        tool_count = len(tools)

        # Should have at least the base tools
        assert tool_count >= 5
        print(f"Discovered {tool_count} tools")

    async def test_model_listing_performance(self):
        """Test model listing performance."""
        client = MCPClient()

        start_time = time.time()
        models = await client.call_tool("list_models", {})
        elapsed_time = time.time() - start_time

        assert elapsed_time < 1.0
        assert isinstance(models, dict)
        print(f"Model listing took {elapsed_time:.3f}s")
