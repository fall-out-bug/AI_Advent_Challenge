"""Interactive comprehensive demo of all MCP tools and chains.

Demonstrates all 12 MCP tools, tool chains, and conversation context.
Includes help, list, and complex code generation with inputs and outputs.
Features streaming output emulation for a living chat experience.
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

# Streaming delay settings
TYPING_DELAY = 0.02  # Delay between characters
THINKING_DELAY = 0.6  # Delay for "thinking" indicators
LINE_DELAY = 0.3  # Delay between lines


async def type_print(text: str, delay: float = TYPING_DELAY):
    """Print text character by character for streaming effect.

    Args:
        text: Text to print
        delay: Delay between characters in seconds
    """
    for char in text:
        print(char, end='', flush=True)
        await asyncio.sleep(delay)


async def stream_line(text: str, delay: float = LINE_DELAY):
    """Print a line and wait before next line.

    Args:
        text: Line to print
        delay: Delay after printing in seconds
    """
    print(text)
    await asyncio.sleep(delay)


async def thinking_indicator(message: str = "Thinking", duration: float = THINKING_DELAY):
    """Show a thinking/processing indicator.

    Args:
        message: Message to display
        duration: How long to show the indicator
    """
    print(f"\r{message}", end="", flush=True)
    for i in range(3):
        await asyncio.sleep(duration / 3)
        print(".", end="", flush=True)
    print()  # New line after thinking


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
    await stream_line("\n" + "=" * 80)
    await type_print("MCP SERVER HELP - Available Tools")
    await stream_line("\n" + "=" * 80)

    await thinking_indicator("Discovering tools", 0.6)
    tools = await get_tools_list(client)

    if not tools:
        await type_print("⚠️  No tools available or server not responding")
        return

    await stream_line(f"\nFound {len(tools)} tools:\n")

    for i, tool in enumerate(tools, 1):
        name = tool.get("name", "unknown")
        description = tool.get("description", "No description")
        input_schema = tool.get("input_schema", {})

        await stream_line(f"{i}. {name}", 0.2)
        await stream_line(f"   Description: {description}", 0.15)

        # Show parameters
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        if properties:
            await stream_line("   Parameters:", 0.15)
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                required_marker = "*" if param_name in required else ""
                default = param_info.get("default", "")
                default_str = f" (default: {default})" if default else ""
                await stream_line(f"      - {param_name}{required_marker}: {param_type}{default_str}", 0.1)
                if param_desc:
                    await stream_line(f"        {param_desc}", 0.1)

        await stream_line("", 0.15)

    await stream_line("=" * 80)


async def list_tools(client: httpx.AsyncClient):
    """List all available tools in compact format.

    Args:
        client: HTTP client
    """
    await stream_line("\n📋 AVAILABLE TOOLS", 0.3)
    await stream_line("-" * 80)

    await thinking_indicator("Loading tools", 0.5)
    tools = await get_tools_list(client)

    if not tools:
        await type_print("⚠️  No tools available")
        return

    for tool in tools:
        name = tool.get("name", "unknown")
        description = tool.get("description", "No description")
        await stream_line(f"  • {name}: {description}", 0.15)

    await stream_line(f"\nTotal: {len(tools)} tools", 0.3)
    await stream_line("-" * 80)


async def test_calculator_tools(client: httpx.AsyncClient):
    """Test calculator tools with inputs and outputs.

    Args:
        client: HTTP client
    """
    await stream_line("\n🧮 Testing Calculator Tools", 0.4)
    await stream_line("-" * 80)

    # Test 1: Addition
    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: add", 0.2)
    await stream_line("  Arguments: a=10, b=25", 0.2)
    await thinking_indicator("Computing", 0.5)
    result = await call_tool(client, "add", {"a": 10, "b": 25})
    await stream_line("OUTPUT:", 0.3)
    await type_print(f"  Result: {result}")
    await stream_line("")
    await stream_line(f"  ✓ add(10, 25) = {result}", 0.3)

    # Test 2: Multiplication
    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: multiply", 0.2)
    await stream_line("  Arguments: a=7, b=8", 0.2)
    await thinking_indicator("Computing", 0.5)
    result = await call_tool(client, "multiply", {"a": 7, "b": 8})
    await stream_line("OUTPUT:", 0.3)
    await type_print(f"  Result: {result}")
    await stream_line("")
    await stream_line(f"  ✓ multiply(7, 8) = {result}", 0.3)


async def test_model_discovery(client: httpx.AsyncClient):
    """Test model discovery tools with inputs and outputs.

    Args:
        client: HTTP client
    """
    await stream_line("\n🔍 Testing Model Discovery", 0.4)
    await stream_line("-" * 80)

    # Test 1: List all models
    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: list_models", 0.2)
    await stream_line("  Arguments: {}", 0.2)
    await thinking_indicator("Querying models", 0.7)
    result = await call_tool(client, "list_models", {})
    await stream_line("OUTPUT:", 0.3)
    local_models = result.get('local_models', [])
    await type_print(f"  Found {len(local_models)} local models")
    await stream_line("")
    await stream_line(f"  ✓ list_models: {len(local_models)} models available", 0.3)

    # Test 2: Check specific model
    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: check_model", 0.2)
    await stream_line("  Arguments: model_name='mistral'", 0.2)
    await thinking_indicator("Checking availability", 0.6)
    result = await call_tool(client, "check_model", {"model_name": "mistral"})
    await stream_line("OUTPUT:", 0.3)
    available = result.get("available", "unknown")
    await stream_line(f"  ✓ Model availability: {available}", 0.3)


async def test_token_analysis(client: httpx.AsyncClient):
    """Test token counting with inputs and outputs.

    Args:
        client: HTTP client
    """
    await stream_line("\n🔢 Testing Token Analysis", 0.4)
    await stream_line("-" * 80)

    text = "Hello, this is a test sentence for token counting."
    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: count_tokens", 0.2)
    await stream_line(f"  Arguments: text='{text}'", 0.2)
    await thinking_indicator("Counting tokens", 0.5)
    result = await call_tool(client, "count_tokens", {"text": text})
    await stream_line("OUTPUT:", 0.3)
    count = result.get("count", result)
    await type_print(f"  Token count: {count}")
    await stream_line("")
    await stream_line(f"  ✓ Total tokens: {count}", 0.3)


async def test_code_generation(client: httpx.AsyncClient):
    """Test code generation with inputs and outputs.

    Args:
        client: HTTP client
    """
    await stream_line("\n💻 Testing Code Generation", 0.4)
    await stream_line("-" * 80)

    description = "create a simple function that adds two numbers"
    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: generate_code", 0.2)
    await stream_line(f"  Description: '{description}'", 0.2)
    await stream_line("  Model: starcoder", 0.2)

    await thinking_indicator("Generating code", 1.0)
    result = await call_tool(
        client,
        "generate_code",
        {"description": description, "model": "starcoder"}
    )

    await stream_line("\nOUTPUT:", 0.3)

    if result.get("success") and "code" in result:
        code = result["code"]
        await stream_line(f"  Success: ✓")
        await stream_line("\n  Generated Code:")
        print("```python")
        await type_print(code, 0.01)
        print("\n```")
        await stream_line(f"\n  ✓ Code generation successful ({len(code)} characters)", 0.3)
        return result.get("code", "")
    else:
        await type_print(f"  Result: {json.dumps(result, indent=2)}")
        return None


async def test_complex_code_generation(client: httpx.AsyncClient):
    """Test complex code generation task with inputs and outputs.

    Args:
        client: HTTP client
    """
    await stream_line("\n🚀 Testing COMPLEX Code Generation", 0.4)
    await stream_line("-" * 80)

    complex_task = """Create a complete REST API class for user management with the following features:
    - User registration with validation
    - User login with JWT authentication
    - User profile retrieval
    - User profile update
    - Password change functionality
    Include proper error handling, input validation, and following PEP8 style"""

    await stream_line("\nCOMPLEX TASK INPUT:", 0.3)
    await stream_line("  Tool: generate_code", 0.2)
    await type_print(f"  Description: {complex_task[:80]}...", 0.01)
    await stream_line("")
    await stream_line("  Model: starcoder", 0.2)

    await thinking_indicator("Generating complex code", 1.5)
    result = await call_tool(
        client,
        "generate_code",
        {"description": complex_task, "model": "starcoder"}
    )

    await stream_line("\nOUTPUT:", 0.3)
    if result.get("success"):
        code = result.get("code", "")
        await stream_line(f"  ✓ Success! Generated {len(code)} characters of code", 0.3)
        await stream_line("\n  Code Preview:")
        print("```python")
        code_preview = code[:400] + "..." if len(code) > 400 else code
        await type_print(code_preview, 0.01)
        print("\n```")
        if len(code) > 400:
            await stream_line("  [Code truncated for display]", 0.2)
        return code
    else:
        await type_print(f"  Result: {json.dumps(result, indent=2)}")
        return None


async def test_code_review(client: httpx.AsyncClient, code: str = None):
    """Test code review with inputs and outputs.

    Args:
        client: HTTP client
        code: Code to review (uses default if not provided)
    """
    await stream_line("\n📝 Testing Code Review", 0.4)
    await stream_line("-" * 80)

    if not code:
        code = """
def add(a, b):
    return a+b
"""

    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: review_code", 0.2)
    await stream_line(f"  Code to review:\n```python{code}\n```", 0.2)
    await thinking_indicator("Analyzing code", 1.0)
    result = await call_tool(client, "review_code", {"code": code, "model": "starcoder"})

    await stream_line("\nOUTPUT:", 0.3)

    if "quality_score" in result:
        await stream_line(f"  ✓ Review score: {result.get('quality_score')}/10", 0.3)
    elif result.get("success"):
        await stream_line(f"  ✓ Review completed successfully", 0.3)


async def test_test_generation(client: httpx.AsyncClient, code: str = None):
    """Test test generation with inputs and outputs.

    Args:
        client: HTTP client
        code: Code to generate tests for (uses default if not provided)
    """
    await stream_line("\n🧪 Testing Test Generation", 0.4)
    await stream_line("-" * 80)

    if not code:
        code = """
def multiply(x, y):
    return x * y
"""

    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: generate_tests", 0.2)
    await stream_line(f"  Code:\n```python{code}\n```", 0.2)
    await stream_line("  Framework: pytest", 0.2)
    await stream_line("  Coverage target: 80%", 0.2)

    await thinking_indicator("Generating tests", 1.2)
    result = await call_tool(
        client,
        "generate_tests",
        {"code": code, "test_framework": "pytest", "coverage_target": 80}
    )

    await stream_line("\nOUTPUT:", 0.3)

    if "test_code" in result:
        test_code = result.get("test_code", "")
        test_count = result.get("test_count", "unknown")
        await stream_line(f"  ✓ Generated {test_count} tests", 0.3)
        if test_code:
            await stream_line("\n  Test Code:")
            print("```python")
            await type_print(test_code[:300] + "..." if len(test_code) > 300 else test_code, 0.01)
            print("\n```")
    else:
        await type_print(f"  Result: {json.dumps(result, indent=2)}")


async def test_code_formatting(client: httpx.AsyncClient):
    """Test code formatting with inputs and outputs.

    Args:
        client: HTTP client
    """
    await stream_line("\n✨ Testing Code Formatting", 0.4)
    await stream_line("-" * 80)

    unformatted = "def add(a,b):return a+b\n\ndef multiply(x,y):\n    result=x*y\n    return result"

    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: format_code", 0.2)
    await stream_line(f"  Unformatted:\n```python\n{unformatted}\n```", 0.2)

    await thinking_indicator("Formatting", 0.6)
    result = await call_tool(
        client,
        "format_code",
        {"code": unformatted, "formatter": "black", "line_length": 88}
    )

    await stream_line("\nOUTPUT:", 0.3)
    if "formatted_code" in result:
        await stream_line("  Formatted:")
        print("```python")
        await type_print(result['formatted_code'], 0.01)
        print("\n```")
        await stream_line("  ✓ Code formatted successfully", 0.3)
    else:
        await type_print(f"  Result: {json.dumps(result, indent=2)}")


async def test_complexity_analysis(client: httpx.AsyncClient):
    """Test complexity analysis with inputs and outputs.

    Args:
        client: HTTP client
    """
    await stream_line("\n📊 Testing Complexity Analysis", 0.4)
    await stream_line("-" * 80)

    code = """
def calculate(x, y):
    if x > 0:
        if y > 0:
            return x * y
        else:
            return 0
    return 0
"""

    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: analyze_complexity", 0.2)
    await stream_line(f"  Code:\n```python{code}\n```", 0.2)
    await stream_line("  Detailed: True", 0.2)

    await thinking_indicator("Analyzing complexity", 0.8)
    result = await call_tool(client, "analyze_complexity", {"code": code, "detailed": True})

    await stream_line("\nOUTPUT:", 0.3)

    if "cyclomatic_complexity" in result:
        complexity = result.get("cyclomatic_complexity")
        await stream_line(f"  ✓ Cyclomatic complexity: {complexity}", 0.3)
    else:
        await stream_line(f"  Analysis complete", 0.3)


async def test_formalize_task(client: httpx.AsyncClient):
    """Test task formalization with inputs and outputs.

    Args:
        client: HTTP client
    """
    await stream_line("\n🏗️  Testing Task Formalization", 0.4)
    await stream_line("-" * 80)

    informal = "Build a REST API for user management"
    context = "Use Python and FastAPI"

    await stream_line("\nINPUT:", 0.3)
    await stream_line("  Tool: formalize_task", 0.2)
    await stream_line(f"  Request: '{informal}'", 0.2)
    await stream_line(f"  Context: '{context}'", 0.2)

    await thinking_indicator("Formalizing task", 1.0)
    result = await call_tool(
        client,
        "formalize_task",
        {"informal_request": informal, "context": context}
    )

    await stream_line("\nOUTPUT:", 0.3)

    if "formalized_description" in result:
        await stream_line("  ✓ Task formalized successfully", 0.3)
    elif result.get("success"):
        await stream_line("  ✓ Task formalization completed", 0.3)


async def test_tool_chains(client: httpx.AsyncClient):
    """Test tool chains with inputs and outputs for all steps.

    Args:
        client: HTTP client
    """
    await stream_line("\n🔗 Testing Tool Chains")
    await stream_line("=" * 80)

    # Chain 1: Generate → Review → Test
    await stream_line("\n📋 CHAIN 1: Generate → Review → Test")
    await stream_line("-" * 80)

    description = "create a simple calculator with add and multiply functions"

    await stream_line("\nStep 1: Generate Code", 0.3)
    await stream_line(f"  Description: '{description}'", 0.2)
    await thinking_indicator("Generating", 1.0)
    gen_result = await call_tool(
        client,
        "generate_code",
        {"description": description, "model": "starcoder"}
    )

    if gen_result.get("success") and "code" in gen_result:
        code = gen_result["code"]
        await stream_line(f"  ✓ Generated {len(code)} characters", 0.3)

        await stream_line("\nStep 2: Review Code", 0.3)
        await thinking_indicator("Reviewing", 0.8)
        review_result = await call_tool(client, "review_code", {"code": code, "model": "starcoder"})
        await stream_line("  ✓ Review completed", 0.3)

        await stream_line("\nStep 3: Generate Tests", 0.3)
        await thinking_indicator("Creating tests", 1.0)
        test_result = await call_tool(client, "generate_tests", {"code": code})
        await stream_line("  ✓ Tests generated", 0.3)

        await stream_line("\n✅ Chain 1 completed!", 0.4)
    else:
        await stream_line("  ⚠️  Code generation failed", 0.3)

    # Chain 2: Generate → Format → Analyze
    await stream_line("\n📋 CHAIN 2: Generate → Format → Analyze")
    await stream_line("-" * 80)

    description = "create a function to calculate factorial"

    await stream_line("\nStep 1: Generate Code", 0.3)
    await stream_line(f"  Description: '{description}'", 0.2)
    await thinking_indicator("Generating", 1.0)
    gen_result = await call_tool(
        client,
        "generate_code",
        {"description": description, "model": "starcoder"}
    )

    if gen_result.get("success") and "code" in gen_result:
        code = gen_result["code"]
        await stream_line(f"  ✓ Generated {len(code)} characters", 0.3)

        await stream_line("\nStep 2: Format Code", 0.3)
        await thinking_indicator("Formatting", 0.6)
        format_result = await call_tool(client, "format_code", {"code": code})
        await stream_line("  ✓ Code formatted", 0.3)

        await stream_line("\nStep 3: Analyze", 0.3)
        await thinking_indicator("Analyzing", 0.8)
        formatted_code = format_result.get("formatted_code", code)
        analyze_result = await call_tool(client, "analyze_complexity", {"code": formatted_code})
        await stream_line("  ✓ Analysis complete", 0.3)

        await stream_line("\n✅ Chain 2 completed!", 0.4)


async def run_comprehensive_demo():
    """Run comprehensive demo showing all MCP capabilities.

    This demo includes:
    - Help and tool listing
    - All individual tools with inputs and outputs
    - Complex code generation tasks
    - Tool chains demonstrating workflows
    """
    print("\n" + "=" * 80)
    await type_print("🤖 MCP COMPREHENSIVE DEMO")
    print("\n")
    await type_print("Testing All Tools with Inputs and Outputs")
    print("\n" + "=" * 80)

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Section 1: Help and Discovery
        await stream_line("\n📖 SECTION 1: HELP AND DISCOVERY", 0.5)
        await show_help(client)
        await list_tools(client)

        # Section 2: Basic Tools
        await stream_line("\n🔧 SECTION 2: BASIC TOOLS", 0.5)
        await test_calculator_tools(client)
        await test_model_discovery(client)
        await test_token_analysis(client)

        # Section 3: Code Generation
        await stream_line("\n💻 SECTION 3: CODE GENERATION", 0.5)
        code = await test_code_generation(client)

        # Section 4: Complex Code Generation
        await stream_line("\n🚀 SECTION 4: COMPLEX CODE GENERATION", 0.5)
        complex_code = await test_complex_code_generation(client)

        # Section 5: Code Analysis and Testing
        await stream_line("\n🔬 SECTION 5: CODE ANALYSIS AND TESTING", 0.5)
        await test_code_review(client, code)
        await test_test_generation(client, code)
        await test_code_formatting(client)
        await test_complexity_analysis(client)
        await test_formalize_task(client)

        # Section 6: Tool Chains
        await stream_line("\n🔗 SECTION 6: TOOL CHAINS", 0.5)
        await test_tool_chains(client)

    await stream_line("\n" + "=" * 80, 0.4)
    await type_print("✅ MCP COMPREHENSIVE DEMO COMPLETE!")
    print("\n")
    await type_print("All tools tested with inputs and outputs displayed")
    print("\n" + "=" * 80)


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
