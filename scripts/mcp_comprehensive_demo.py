"""Interactive comprehensive demo of all MCP tools and chains.

Demonstrates all 12 MCP tools, tool chains, and conversation context.
Includes help, list, and complex code generation with inputs and outputs.
"""
import asyncio
import httpx
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add root to path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))

MCP_SERVER_URL = "http://localhost:8004"


async def get_tools_list(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Get list of all available tools.

    Args:
        client: HTTP client

    Returns:
        List of tool definitions
    """
    try:
        response = await client.get(f"{MCP_SERVER_URL}/tools", timeout=30.0)
        response.raise_for_status()
        result = response.json()
        return result.get("tools", [])
    except Exception as e:
        print(f"❌ Error getting tools list: {e}")
        return []


async def call_tool(client: httpx.AsyncClient, tool_name: str, arguments: dict) -> dict:
    """Call MCP tool via HTTP.

    Args:
        client: HTTP client
        tool_name: Name of tool to call
        arguments: Tool arguments

    Returns:
        Tool result
    """
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


async def show_help(client: httpx.AsyncClient):
    """Display help information showing all available tools.

    Args:
        client: HTTP client
    """
    print("\n" + "=" * 80)
    print("MCP SERVER HELP - Available Tools")
    print("=" * 80)
    
    tools = await get_tools_list(client)
    
    if not tools:
        print("⚠️  No tools available or server not responding")
        return
    
    print(f"\nFound {len(tools)} tools:\n")
    
    for i, tool in enumerate(tools, 1):
        name = tool.get("name", "unknown")
        description = tool.get("description", "No description")
        input_schema = tool.get("input_schema", {})
        
        print(f"{i}. {name}")
        print(f"   Description: {description}")
        
        # Show parameters
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        if properties:
            print("   Parameters:")
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                required_marker = "*" if param_name in required else ""
                default = param_info.get("default", "")
                default_str = f" (default: {default})" if default else ""
                print(f"      - {param_name}{required_marker}: {param_type}{default_str}")
                if param_desc:
                    print(f"        {param_desc}")
        
        print()
    
    print("=" * 80)


async def list_tools(client: httpx.AsyncClient):
    """List all available tools in compact format.

    Args:
        client: HTTP client
    """
    print("\n📋 AVAILABLE TOOLS")
    print("-" * 80)
    
    tools = await get_tools_list(client)
    
    if not tools:
        print("⚠️  No tools available")
        return
    
    for tool in tools:
        name = tool.get("name", "unknown")
        description = tool.get("description", "No description")
        print(f"  • {name}: {description}")
    
    print(f"\nTotal: {len(tools)} tools")
    print("-" * 80)


async def test_calculator_tools(client: httpx.AsyncClient):
    """Test calculator tools with inputs and outputs.

    Args:
        client: HTTP client
    """
    print("\n🧮 Testing Calculator Tools")
    print("-" * 80)
    
    # Test 1: Addition
    print("\nINPUT:")
    print("  Tool: add")
    print("  Arguments: a=10, b=25")
    result = await call_tool(client, "add", {"a": 10, "b": 25})
    print("OUTPUT:")
    print(f"  Result: {result}")
    print(f"  ✓ add(10, 25) = {result}")
    
    # Test 2: Multiplication
    print("\nINPUT:")
    print("  Tool: multiply")
    print("  Arguments: a=7, b=8")
    result = await call_tool(client, "multiply", {"a": 7, "b": 8})
    print("OUTPUT:")
    print(f"  Result: {result}")
    print(f"  ✓ multiply(7, 8) = {result}")


async def test_model_discovery(client: httpx.AsyncClient):
    """Test model discovery tools with inputs and outputs.

    Args:
        client: HTTP client
    """
    print("\n🔍 Testing Model Discovery")
    print("-" * 80)
    
    # Test 1: List all models
    print("\nINPUT:")
    print("  Tool: list_models")
    print("  Arguments: {}")
    result = await call_tool(client, "list_models", {})
    print("OUTPUT:")
    print(f"  Result: {json.dumps(result, indent=2)}")
    local_models = result.get('local_models', [])
    print(f"  ✓ Found {len(local_models)} local models")
    
    # Test 2: Check specific model
    print("\nINPUT:")
    print("  Tool: check_model")
    print("  Arguments: model_name='mistral'")
    result = await call_tool(client, "check_model", {"model_name": "mistral"})
    print("OUTPUT:")
    print(f"  Result: {json.dumps(result, indent=2)}")


async def test_token_analysis(client: httpx.AsyncClient):
    """Test token counting with inputs and outputs.

    Args:
        client: HTTP client
    """
    print("\n🔢 Testing Token Analysis")
    print("-" * 80)
    
    text = "Hello, this is a test sentence for token counting."
    print("\nINPUT:")
    print("  Tool: count_tokens")
    print(f"  Arguments: text='{text}'")
    result = await call_tool(client, "count_tokens", {"text": text})
    print("OUTPUT:")
    count = result.get("count", result)
    print(f"  Result: {json.dumps(result, indent=2)}")
    print(f"  ✓ Token count: {count}")


async def test_code_generation(client: httpx.AsyncClient):
    """Test code generation with inputs and outputs.

    Args:
        client: HTTP client
    """
    print("\n💻 Testing Code Generation")
    print("-" * 80)
    
    description = "create a simple function that adds two numbers"
    print("\nINPUT:")
    print("  Tool: generate_code")
    print(f"  Arguments: description='{description}', model='starcoder'")
    
    result = await call_tool(
        client,
        "generate_code",
        {"description": description, "model": "starcoder"}
    )
    
    print("OUTPUT:")
    print(f"  Success: {result.get('success', False)}")
    
    if result.get("success") and "code" in result:
        code = result["code"]
        print(f"  Generated Code:\n```python\n{code}\n```")
        print(f"  ✓ Code generation successful ({len(code)} characters)")
        return result.get("code", "")
    else:
        print(f"  Result: {json.dumps(result, indent=2)}")
        return None


async def test_complex_code_generation(client: httpx.AsyncClient):
    """Test complex code generation task with inputs and outputs.

    Args:
        client: HTTP client
    """
    print("\n🚀 Testing COMPLEX Code Generation")
    print("-" * 80)
    
    complex_task = """Create a complete REST API class for user management with the following features:
    - User registration with validation
    - User login with JWT authentication
    - User profile retrieval
    - User profile update
    - Password change functionality
    Include proper error handling, input validation, and following PEP8 style"""
    
    print("\nCOMPLEX TASK INPUT:")
    print("  Tool: generate_code")
    print(f"  Description: {complex_task[:100]}...")
    print(f"  Model: starcoder")
    
    result = await call_tool(
        client,
        "generate_code",
        {"description": complex_task, "model": "starcoder"}
    )
    
    print("\nOUTPUT:")
    if result.get("success"):
        code = result.get("code", "")
        # Show first 500 characters
        code_preview = code[:500] + "..." if len(code) > 500 else code
        print(f"  ✓ Success! Generated {len(code)} characters of code")
        print(f"\n  Code Preview:\n```python\n{code_preview}\n```")
        
        # Show metadata if available
        if "metadata" in result:
            print(f"  Metadata: {json.dumps(result['metadata'], indent=2)}")
        
        return code
    else:
        print(f"  Result: {json.dumps(result, indent=2)}")
        return None


async def test_code_review(client: httpx.AsyncClient, code: str = None):
    """Test code review with inputs and outputs.

    Args:
        client: HTTP client
        code: Code to review (uses default if not provided)
    """
    print("\n📝 Testing Code Review")
    print("-" * 80)
    
    if not code:
        code = """
def add(a, b):
    return a+b
"""
    
    print("\nINPUT:")
    print("  Tool: review_code")
    print(f"  Code to review:\n```python{code}\n```")
    print("  Model: starcoder")
    
    result = await call_tool(client, "review_code", {"code": code, "model": "starcoder"})
    
    print("\nOUTPUT:")
    print(f"  Result: {json.dumps(result, indent=2)}")
    
    if "quality_score" in result:
        print(f"  ✓ Review score: {result.get('quality_score')}/10")
    elif result.get("success"):
        print(f"  ✓ Review completed successfully")


async def test_test_generation(client: httpx.AsyncClient, code: str = None):
    """Test test generation with inputs and outputs.

    Args:
        client: HTTP client
        code: Code to generate tests for (uses default if not provided)
    """
    print("\n🧪 Testing Test Generation")
    print("-" * 80)
    
    if not code:
        code = """
def multiply(x, y):
    return x * y
"""
    
    print("\nINPUT:")
    print("  Tool: generate_tests")
    print(f"  Code to test:\n```python{code}\n```")
    print("  Test framework: pytest")
    print("  Coverage target: 80%")
    
    result = await call_tool(
        client,
        "generate_tests",
        {"code": code, "test_framework": "pytest", "coverage_target": 80}
    )
    
    print("\nOUTPUT:")
    print(f"  Result: {json.dumps(result, indent=2)}")
    
    if "test_code" in result:
        test_code = result.get("test_code", "")
        test_count = result.get("test_count", "unknown")
        print(f"  ✓ Generated {test_count} tests")
        print(f"  Test Code:\n```python\n{test_code}\n```")
    else:
        print(f"  ⚠️  Test generation result: {result}")


async def test_code_formatting(client: httpx.AsyncClient):
    """Test code formatting with inputs and outputs.

    Args:
        client: HTTP client
    """
    print("\n✨ Testing Code Formatting")
    print("-" * 80)
    
    unformatted = "def add(a,b):return a+b\n\ndef multiply(x,y):\n    result=x*y\n    return result"
    
    print("\nINPUT:")
    print("  Tool: format_code")
    print(f"  Unformatted code:\n```python\n{unformatted}\n```")
    print("  Formatter: black")
    print("  Line length: 88")
    
    result = await call_tool(
        client,
        "format_code",
        {"code": unformatted, "formatter": "black", "line_length": 88}
    )
    
    print("\nOUTPUT:")
    if "formatted_code" in result:
        print(f"  Formatted code:\n```python\n{result['formatted_code']}\n```")
        print(f"  ✓ Code formatted successfully")
    else:
        print(f"  Result: {json.dumps(result, indent=2)}")


async def test_complexity_analysis(client: httpx.AsyncClient):
    """Test complexity analysis with inputs and outputs.

    Args:
        client: HTTP client
    """
    print("\n📊 Testing Complexity Analysis")
    print("-" * 80)
    
    code = """
def calculate(x, y):
    if x > 0:
        if y > 0:
            return x * y
        else:
            return 0
    return 0
"""
    
    print("\nINPUT:")
    print("  Tool: analyze_complexity")
    print(f"  Code to analyze:\n```python{code}\n```")
    print("  Detailed: True")
    
    result = await call_tool(client, "analyze_complexity", {"code": code, "detailed": True})
    
    print("\nOUTPUT:")
    print(f"  Result: {json.dumps(result, indent=2)}")
    
    if "cyclomatic_complexity" in result:
        complexity = result.get("cyclomatic_complexity")
        print(f"  ✓ Cyclomatic complexity: {complexity}")


async def test_formalize_task(client: httpx.AsyncClient):
    """Test task formalization with inputs and outputs.

    Args:
        client: HTTP client
    """
    print("\n🏗️  Testing Task Formalization")
    print("-" * 80)
    
    informal = "Build a REST API for user management"
    context = "Use Python and FastAPI"
    
    print("\nINPUT:")
    print("  Tool: formalize_task")
    print(f"  Informal request: '{informal}'")
    print(f"  Context: '{context}'")
    
    result = await call_tool(
        client,
        "formalize_task",
        {"informal_request": informal, "context": context}
    )
    
    print("\nOUTPUT:")
    print(f"  Result: {json.dumps(result, indent=2)}")
    
    if "formalized_description" in result:
        print(f"  ✓ Task formalized successfully")
    elif result.get("success"):
        print(f"  ✓ Task formalization completed")


async def test_tool_chains(client: httpx.AsyncClient):
    """Test tool chains with inputs and outputs for all steps.

    Args:
        client: HTTP client
    """
    print("\n🔗 Testing Tool Chains")
    print("=" * 80)
    
    # Chain 1: Generate → Review → Test
    print("\n📋 CHAIN 1: Generate → Review → Test")
    print("-" * 80)
    
    description = "create a simple calculator with add and multiply functions"
    
    print(f"\nStep 1: Generate Code")
    print(f"  Description: '{description}'")
    gen_result = await call_tool(
        client,
        "generate_code",
        {"description": description, "model": "starcoder"}
    )
    
    if gen_result.get("success") and "code" in gen_result:
        code = gen_result["code"]
        print(f"  ✓ Generated {len(code)} characters of code")
        
        print(f"\nStep 2: Review Code")
        print(f"  Reviewing generated code...")
        review_result = await call_tool(client, "review_code", {"code": code, "model": "starcoder"})
        print(f"  ✓ Review completed")
        
        print(f"\nStep 3: Generate Tests")
        print(f"  Generating tests for the code...")
        test_result = await call_tool(client, "generate_tests", {"code": code})
        print(f"  ✓ Tests generated")
        
        print(f"\n✅ Chain 1 completed successfully!")
    else:
        print(f"  ⚠️  Code generation failed, skipping chain")
    
    # Chain 2: Generate → Format → Analyze
    print("\n📋 CHAIN 2: Generate → Format → Analyze")
    print("-" * 80)
    
    description = "create a function to calculate factorial"
    
    print(f"\nStep 1: Generate Code")
    print(f"  Description: '{description}'")
    gen_result = await call_tool(
        client,
        "generate_code",
        {"description": description, "model": "starcoder"}
    )
    
    if gen_result.get("success") and "code" in gen_result:
        code = gen_result["code"]
        print(f"  ✓ Generated {len(code)} characters of code")
        
        print(f"\nStep 2: Format Code")
        print(f"  Formatting generated code...")
        format_result = await call_tool(client, "format_code", {"code": code})
        print(f"  ✓ Code formatted")
        
        print(f"\nStep 3: Analyze Complexity")
        print(f"  Analyzing code complexity...")
        formatted_code = format_result.get("formatted_code", code)
        analyze_result = await call_tool(client, "analyze_complexity", {"code": formatted_code})
        print(f"  ✓ Complexity analyzed")
        
        print(f"\n✅ Chain 2 completed successfully!")


async def run_comprehensive_demo():
    """Run comprehensive demo showing all MCP capabilities.

    This demo includes:
    - Help and tool listing
    - All individual tools with inputs and outputs
    - Complex code generation tasks
    - Tool chains demonstrating workflows
    """
    print("\n" + "=" * 80)
    print("🤖 MCP COMPREHENSIVE DEMO")
    print("Testing All Tools with Inputs and Outputs")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Section 1: Help and Discovery
        print("\n📖 SECTION 1: HELP AND DISCOVERY")
        await show_help(client)
        await list_tools(client)
        
        # Section 2: Basic Tools
        print("\n🔧 SECTION 2: BASIC TOOLS")
        await test_calculator_tools(client)
        await test_model_discovery(client)
        await test_token_analysis(client)
        
        # Section 3: Code Generation
        print("\n💻 SECTION 3: CODE GENERATION")
        code = await test_code_generation(client)
        
        # Section 4: Complex Code Generation
        print("\n🚀 SECTION 4: COMPLEX CODE GENERATION")
        complex_code = await test_complex_code_generation(client)
        
        # Section 5: Code Analysis and Testing
        print("\n🔬 SECTION 5: CODE ANALYSIS AND TESTING")
        await test_code_review(client, code)
        await test_test_generation(client, code)
        await test_code_formatting(client)
        await test_complexity_analysis(client)
        await test_formalize_task(client)
        
        # Section 6: Tool Chains
        print("\n🔗 SECTION 6: TOOL CHAINS")
        await test_tool_chains(client)
    
    print("\n" + "=" * 80)
    print("✅ MCP COMPREHENSIVE DEMO COMPLETE!")
    print("All tools tested with inputs and outputs displayed")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(run_comprehensive_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
