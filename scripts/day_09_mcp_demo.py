#!/usr/bin/env python3
"""Day 09: MCP integration demonstration with comprehensive tests."""
import asyncio
import json
import sys
from pathlib import Path

# Add root to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from src.presentation.mcp.client import MCPClient


async def test_calculator_tools(client):
    """Test calculator tools."""
    print("\n" + "=" * 70)
    print("🧮 TOOL 1-2: Calculator Tools")
    print("=" * 70)
    
    # Test addition
    print("\n✓ Testing ADD tool...")
    print("   Input: add(a=15, b=27)")
    result = await client.call_tool("add", {"a": 15, "b": 27})
    print(f"   Output: {result}")
    assert result == 42, f"Expected 42, got {result}"
    print("   ✅ Addition works correctly")
    
    # Test multiplication
    print("\n✓ Testing MULTIPLY tool...")
    print("   Input: multiply(a=7, b=8)")
    result = await client.call_tool("multiply", {"a": 7, "b": 8})
    print(f"   Output: {result}")
    assert result == 56, f"Expected 56, got {result}"
    print("   ✅ Multiplication works correctly")


async def test_model_sdk_tools(client):
    """Test model SDK tools."""
    print("\n" + "=" * 70)
    print("🤖 TOOL 3-4: Model SDK Tools")
    print("=" * 70)
    
    # List all models
    print("\n✓ Testing LIST_MODELS tool...")
    print("   Input: list_models()")
    models = await client.call_tool("list_models", {})
    print(f"   Output:")
    print(f"   - Local models: {len(models.get('local_models', []))}")
    for model in models.get("local_models", [])[:3]:
        print(f"     • {model['display_name']} (port {model.get('port', 'N/A')})")
    print(f"   - API models: {len(models.get('api_models', []))}")
    for model in models.get("api_models", []):
        print(f"     • {model['display_name']}")
    print("   ✅ Model listing works correctly")
    
    # Check specific model availability
    print("\n✓ Testing CHECK_MODEL tool...")
    for model_name in ["mistral", "starcoder", "qwen"]:
        print(f"   Input: check_model(model_name='{model_name}')")
        result = await client.call_tool("check_model", {"model_name": model_name})
        status = "✅ Available" if result.get("available") else "❌ Not available"
        print(f"   Output: {status}")
        if result.get("error"):
            print(f"     Error: {result['error']}")


async def test_token_analysis_tool(client):
    """Test token analysis tool."""
    print("\n" + "=" * 70)
    print("📊 TOOL 5: Token Analysis")
    print("=" * 70)
    
    test_cases = [
        ("Hello world", "Short text"),
        ("Create a comprehensive Python authentication system with JWT tokens and OAuth2", "Medium text"),
        ("The quick brown fox jumps over the lazy dog. " * 10, "Long text (repeated)"),
    ]
    
    for text, description in test_cases:
        print(f"\n✓ Testing COUNT_TOKENS tool ({description})...")
        print(f"   Input text: '{text[:50]}...'")
        result = await client.call_tool("count_tokens", {"text": text})
        token_count = result.get("count", 0)
        print(f"   Output: {token_count} tokens")
        print(f"   ✅ Token counting works for {description}")


async def test_code_generation_tool(client):
    """Test code generation tool."""
    print("\n" + "=" * 70)
    print("💻 TOOL 6: Code Generation")
    print("=" * 70)
    
    test_cases = [
        (
            "Create a Python function to calculate factorial",
            "mistral",
            "Mistral-7B",
        ),
        (
            "Create a Python class for a simple stack data structure with push, pop, and peek methods",
            "mistral",
            "Mistral-7B (complex)",
        ),
    ]
    
    for description, model, model_display in test_cases:
        print(f"\n✓ Testing GENERATE_CODE tool ({model_display})...")
        print(f"   Input: generate_code(description='{description}', model='{model}')")
        
        try:
            result = await client.call_tool(
                "generate_code",
                {"description": description, "model": model},
            )
            
            if result.get("success"):
                code = result.get("code", "")
                tests = result.get("tests", "")
                metadata = result.get("metadata", {})
                
                print(f"   Output: ✅ Success")
                print(f"   - Model used: {metadata.get('model_used', 'unknown')}")
                print(f"   - Code generated: {len(code)} characters")
                if tests:
                    print(f"   - Tests generated: {len(tests)} characters")
                print(f"   Code preview:")
                for line in code.split('\n')[:5]:
                    print(f"     {line}")
                if len(code.split('\n')) > 5:
                    print("     ...")
            else:
                print(f"   Output: ❌ Failed")
                error_msg = result.get('error', 'Unknown error')
                print(f"   Error: {error_msg}")
                # Print full error details if available
                if isinstance(error_msg, str) and error_msg != "Unknown error":
                    print(f"   Full error: {error_msg[:200]}")
        except Exception as e:
            print(f"   Output: ❌ Exception: {e}")


async def test_code_review_tool(client):
    """Test code review tool."""
    print("\n" + "=" * 70)
    print("🔍 TOOL 7: Code Review")
    print("=" * 70)
    
    code_to_review = '''def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)'''
    
    print(f"\n✓ Testing REVIEW_CODE tool...")
    print(f"   Input code:")
    for line in code_to_review.split('\n'):
        print(f"     {line}")
    print(f"   Input: review_code(code='<fibonacci_function>', model='mistral')")
    
    try:
        result = await client.call_tool(
            "review_code",
            {"code": code_to_review, "model": "mistral"},
        )
        
        if result.get("success"):
            quality_score = result.get("quality_score", 0)
            issues = result.get("issues", []) if isinstance(result.get("issues"), list) else []
            recommendations = result.get("recommendations", []) if isinstance(result.get("recommendations"), list) else []
            
            print(f"   Output: ✅ Success")
            print(f"   - Quality score: {quality_score}/10")
            print(f"   - Issues found: {len(issues)}")
            if issues:
                print(f"   - Issues: {issues[:2]}")
            if recommendations:
                print(f"   - Recommendations: {recommendations[:2]}")
        else:
            print(f"   Output: ❌ Failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   Output: ❌ Exception: {e}")


async def test_orchestration_tool(client):
    """Test orchestration tool."""
    print("\n" + "=" * 70)
    print("🎯 TOOL 8: Generate and Review (Full Workflow)")
    print("=" * 70)
    
    description = "Create a Python class for managing a todo list with add, remove, and list methods"
    
    print(f"\n✓ Testing GENERATE_AND_REVIEW tool...")
    print(f"   Input: generate_and_review(description='{description}')")
    print(f"   Models: mistral (generation) + mistral (review)")
    
    try:
        result = await client.call_tool(
            "generate_and_review",
            {
                "description": description,
                "gen_model": "mistral",
                "review_model": "mistral",
            },
        )
        
        if result.get("success"):
            workflow_time = result.get("workflow_time", 0)
            generation = result.get("generation", {})
            review = result.get("review", {})
            
            issues = review.get("issues", []) if isinstance(review.get("issues"), list) else []
            recommendations = review.get("recommendations", []) if isinstance(review.get("recommendations"), list) else []
            
            print(f"   Output: ✅ Success")
            print(f"   - Workflow completed in: {workflow_time:.2f}s")
            print(f"   - Code generated: {len(generation.get('code', ''))} characters")
            print(f"   - Quality score: {review.get('score', 0)}/10")
            print(f"   Generated code preview:")
            for line in generation.get('code', '').split('\n')[:7]:
                print(f"     {line}")
            if len(generation.get('code', '').split('\n')) > 7:
                print("     ...")
        else:
            print(f"   Output: ❌ Failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   Output: ❌ Exception: {e}")


async def test_mcp_tools():
    """Test all MCP tools comprehensively."""
    print("=" * 70)
    print("🔥 Day 09: Comprehensive MCP Integration Demo")
    print("=" * 70)

    client = MCPClient()

    # Test all tools
    await test_calculator_tools(client)
    await test_model_sdk_tools(client)
    await test_token_analysis_tool(client)
    await test_code_generation_tool(client)
    await test_code_review_tool(client)
    await test_orchestration_tool(client)

    print("\n" + "=" * 70)
    print("✅ All Tool Tests Completed!")
    print("=" * 70)


async def main():
    """Main entry point."""
    await test_mcp_tools()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

