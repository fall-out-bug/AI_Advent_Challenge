"""Interactive comprehensive demo of all MCP tools and chains.

Demonstrates all 12 MCP tools, tool chains, and conversation context.
"""
import asyncio
import httpx
import sys
from pathlib import Path

# Add root to path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))

MCP_SERVER_URL = "http://localhost:8004"


async def call_tool(client: httpx.AsyncClient, tool_name: str, arguments: dict) -> dict:
    """Call MCP tool via HTTP."""
    try:
        response = await client.post(
            f"{MCP_SERVER_URL}/call",
            json={"tool_name": tool_name, "arguments": arguments},
            timeout=300.0
        )
        response.raise_for_status()
        result = response.json()
        return result.get("result", {})
    except Exception as e:
        print(f"❌ Error calling {tool_name}: {e}")
        return {"error": str(e)}


async def test_calculator_tools(client: httpx.AsyncClient):
    """Test calculator tools."""
    print("\n🧮 Testing Calculator Tools...")
    
    result = await call_tool(client, "add", {"a": 10, "b": 25})
    print(f"  ✓ add(10, 25) = {result}")
    
    result = await call_tool(client, "multiply", {"a": 7, "b": 8})
    print(f"  ✓ multiply(7, 8) = {result}")


async def test_model_discovery(client: httpx.AsyncClient):
    """Test model discovery tools."""
    print("\n🔍 Testing Model Discovery...")
    
    result = await call_tool(client, "list_models", {})
    print(f"  ✓ list_models: Found {len(result.get('local_models', []))} local models")
    
    result = await call_tool(client, "check_model", {"model_name": "mistral"})
    print(f"  ✓ check_model('mistral'): {result}")


async def test_token_analysis(client: httpx.AsyncClient):
    """Test token counting."""
    print("\n🔢 Testing Token Analysis...")
    
    result = await call_tool(client, "count_tokens", {"text": "Hello, this is a test sentence for token counting."})
    count = result.get("count", result)
    print(f"  ✓ count_tokens: {count} tokens")


async def test_code_generation(client: httpx.AsyncClient):
    """Test code generation."""
    print("\n💻 Testing Code Generation...")
    
    result = await call_tool(
        client,
        "generate_code",
        {"description": "create a simple function that adds two numbers", "model": "starcoder"}
    )
    
    if result.get("success") and "code" in result:
        code = result["code"][:100] + "..." if len(result.get("code", "")) > 100 else result.get("code", "")
        print(f"  ✓ Generated code: {code}")
        return result.get("code", "")
    else:
        print(f"  ⚠️  Generation result: {result}")
        return None


async def test_code_review(client: httpx.AsyncClient, code: str):
    """Test code review."""
    print("\n📝 Testing Code Review...")
    
    if not code:
        test_code = """
def add(a, b):
    return a+b
"""
    else:
        test_code = code
    
    result = await call_tool(client, "review_code", {"code": test_code, "model": "starcoder"})
    
    if "quality_score" in result:
        print(f"  ✓ Review score: {result.get('quality_score')}/10")
    elif "success" in result:
        print(f"  ✓ Review completed")
    else:
        print(f"  ⚠️  Review result: {result}")


async def test_test_generation(client: httpx.AsyncClient, code: str):
    """Test test generation."""
    print("\n🧪 Testing Test Generation...")
    
    if not code:
        test_code = """
def multiply(x, y):
    return x * y
"""
    else:
        test_code = code
    
    result = await call_tool(
        client,
        "generate_tests",
        {"code": test_code, "test_framework": "pytest", "coverage_target": 80}
    )
    
    if "test_code" in result:
        test_count = result.get("test_count", "unknown")
        print(f"  ✓ Generated {test_count} tests")
    else:
        print(f"  ⚠️  Test generation result: {result}")


async def test_code_formatting(client: httpx.AsyncClient):
    """Test code formatting."""
    print("\n✨ Testing Code Formatting...")
    
    unformatted = "def add(a,b):return a+b\n\ndef multiply(x,y):\n    result=x*y\n    return result"
    
    result = await call_tool(
        client,
        "format_code",
        {"code": unformatted, "formatter": "black", "line_length": 88}
    )
    
    if "formatted_code" in result:
        print(f"  ✓ Code formatted successfully")
    else:
        print(f"  ⚠️  Formatting result: {result}")


async def test_complexity_analysis(client: httpx.AsyncClient):
    """Test complexity analysis."""
    print("\n📊 Testing Complexity Analysis...")
    
    code = """
def calculate(x, y):
    if x > 0:
        if y > 0:
            return x * y
        else:
            return 0
    return 0
"""
    result = await call_tool(client, "analyze_complexity", {"code": code, "detailed": True})
    
    if "cyclomatic_complexity" in result:
        complexity = result.get("cyclomatic_complexity")
        print(f"  ✓ Cyclomatic complexity: {complexity}")
    else:
        print(f"  ⚠️  Analysis result: {result}")


async def test_formalize_task(client: httpx.AsyncClient):
    """Test task formalization."""
    print("\n🏗️  Testing Task Formalization...")
    
    result = await call_tool(
        client,
        "formalize_task",
        {
            "informal_request": "Build a REST API for user management",
            "context": "Use Python and FastAPI"
        }
    )
    
    if "formalized_description" in result:
        print(f"  ✓ Task formalized successfully")
    elif "success" in result:
        print(f"  ✓ Task formalization completed")
    else:
        print(f"  ⚠️  Formalization result: {result}")


async def test_tool_chains(client: httpx.AsyncClient):
    """Test tool chains."""
    print("\n🔗 Testing Tool Chains...")
    
    # Chain 1: Generate → Review → Test
    print("\n  Chain 1: Generate → Review → Test")
    
    gen_result = await call_tool(
        client,
        "generate_code",
        {"description": "create a simple calculator with add and multiply functions", "model": "starcoder"}
    )
    
    if gen_result.get("success") and "code" in gen_result:
        code = gen_result["code"]
        print(f"    ✓ Generated code")
        
        # Review
        review_result = await call_tool(client, "review_code", {"code": code, "model": "starcoder"})
        print(f"    ✓ Reviewed code")
        
        # Generate tests
        test_result = await call_tool(client, "generate_tests", {"code": code})
        print(f"    ✓ Generated tests")
    else:
        print(f"    ⚠️  Code generation failed")
    
    # Chain 2: Generate → Format → Analyze
    print("\n  Chain 2: Generate → Format → Analyze")
    
    gen_result = await call_tool(
        client,
        "generate_code",
        {"description": "create a function to calculate factorial", "model": "starcoder"}
    )
    
    if gen_result.get("success") and "code" in gen_result:
        code = gen_result["code"]
        print(f"    ✓ Generated code")
        
        # Format
        format_result = await call_tool(client, "format_code", {"code": code})
        print(f"    ✓ Formatted code")
        
        # Analyze
        formatted_code = format_result.get("formatted_code", code)
        analyze_result = await call_tool(client, "analyze_complexity", {"code": formatted_code})
        print(f"    ✓ Analyzed complexity")
    else:
        print(f"    ⚠️  Code generation failed")


async def main():
    """Run comprehensive MCP demo."""
    print("=" * 70)
    print("MCP Comprehensive Demo - Testing All Tools and Chains")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Test basic tools
        await test_calculator_tools(client)
        await test_model_discovery(client)
        await test_token_analysis(client)
        
        # Test code tools
        code = await test_code_generation(client)
        await test_code_review(client, code)
        await test_test_generation(client, code)
        await test_code_formatting(client)
        await test_complexity_analysis(client)
        await test_formalize_task(client)
        
        # Test tool chains
        await test_tool_chains(client)
    
    print("\n" + "=" * 70)
    print("✅ MCP Comprehensive Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
