"""Full workflow examples for MCP and Mistral orchestration.

Demonstrates complete multi-step workflows with conversation handling.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))


async def demo_mcp_workflow():
    """Demonstrate MCP tool workflow."""
    print("=" * 70)
    print("MCP Workflow Demo")
    print("=" * 70)

    try:
        from src.presentation.mcp.client import MCPClient

        client = MCPClient(server_script="src/presentation/mcp/server.py")

        # Discover tools
        tools = await client.discover_tools()
        print(f"\nFound {len(tools)} MCP tools")

        # Formalize task
        print("\n1. Formalizing Task")
        result = await client.call_tool(
            "formalize_task",
            {"informal_request": "Create a REST API for authentication", "context": "FastAPI"}
        )
        print(f"Result: {result.get('plan', {}).get('requirements', [])[:3]}...")

        # Generate code
        print("\n2. Generating Code")
        result = await client.call_tool(
            "generate_code",
            {"description": "Create a fibonacci function", "model": "starcoder"}
        )
        print(f"Generated: {result.get('code', '')[:100]}...")

        # Review code
        print("\n3. Reviewing Code")
        test_code = """def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
"""
        result = await client.call_tool(
            "review_code",
            {"code": test_code, "model": "starcoder"}
        )
        print(f"Quality Score: {result.get('quality_score', 0)}/10")

    except Exception as e:
        print(f"Error: {e}")


async def demo_mistral_workflow():
    """Demonstrate Mistral orchestration workflow."""
    print("\n" + "=" * 70)
    print("Mistral Orchestration Demo")
    print("=" * 70)

    try:
        from shared_package.clients.unified_client import UnifiedModelClient
        from src.application.orchestrators.mistral_orchestrator import MistralChatOrchestrator
        from src.infrastructure.repositories.json_conversation_repository import (
            JsonConversationRepository,
        )
        from src.presentation.mcp.orchestrators.mcp_mistral_wrapper import MCPMistralWrapper

        # Setup
        conversations_path = Path("data/conversations/conversations.json")
        conversation_repo = JsonConversationRepository(conversations_path)
        unified_client = UnifiedModelClient()

        wrapper = MCPMistralWrapper(
            server_script="src/presentation/mcp/server.py",
            orchestrator=None,
        )
        await wrapper.initialize()

        orchestrator = MistralChatOrchestrator(
            unified_client=unified_client,
            conversation_repo=conversation_repo,
            model_name="mistral",
            mcp_wrapper=wrapper,
        )

        await orchestrator.initialize()
        conversation_id = "demo_workflow"

        # Example 1: Simple request
        print("\nExample 1: Code Generation Request")
        response = await orchestrator.handle_message(
            "Create a fibonacci function", conversation_id
        )
        print(f"Response: {response[:200]}...")

        # Example 2: Follow-up
        print("\nExample 2: Follow-up Request")
        response = await orchestrator.handle_message(
            "Add tests for the fibonacci function", conversation_id
        )
        print(f"Response: {response[:200]}...")

    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all workflow demos."""
    print("Full Workflow Demonstrations")
    print("Assumes local_models docker-compose is running")

    await demo_mcp_workflow()
    await demo_mistral_workflow()

    print("\n" + "=" * 70)
    print("Demo Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

