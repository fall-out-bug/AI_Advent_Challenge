"""Basic MCP tool discovery example."""
import asyncio
import sys
from pathlib import Path

# Add root to path
root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root))

from src.presentation.mcp.client import MCPClient


async def main():
    """Demonstrate tool discovery."""
    print("=" * 70)
    print("MCP Tool Discovery Demo")
    print("=" * 70)

    client = MCPClient()

    # Discover tools
    print("\nDiscovering available tools...")
    tools = await client.discover_tools()

    print(f"\nFound {len(tools)} tools:")
    for tool in tools:
        print(f"\n  • {tool['name']}")
        print(f"    {tool['description']}")

    # Test calculator tool
    print("\n" + "=" * 70)
    print("Testing calculator tool...")
    result = await client.call_tool("add", {"a": 5, "b": 3})
    print(f"add(5, 3) = {result}")

    # Test token counting
    print("\n" + "=" * 70)
    print("Testing token counting tool...")
    tokens = await client.call_tool(
        "count_tokens", {"text": "Hello world, this is a test"}
    )
    print(f"Token count: {tokens}")

    print("\n✅ Discovery demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
