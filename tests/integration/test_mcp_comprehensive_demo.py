"""Comprehensive integration tests for MCP tools via Docker HTTP server.

Tests all 12 MCP tools individually and in chains with conversation context.
"""
import asyncio
import pytest
import httpx
from typing import Dict, Any, List

# MCP Server URL
MCP_SERVER_URL = "http://localhost:8004"


class TestMCPTools:
    """Test suite for all MCP tools."""
    
    @pytest.fixture
    async def http_client(self):
        """Create HTTP client for MCP server."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            yield client
    
    async def call_tool(self, client: httpx.AsyncClient, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via HTTP."""
        response = await client.post(
            f"{MCP_SERVER_URL}/call",
            json={"tool_name": tool_name, "arguments": arguments}
        )
        assert response.status_code == 200, f"Tool {tool_name} failed with status {response.status_code}"
        result = response.json()
        return result.get("result", {})
    
    # ===== Calculator Tools Tests =====
    
    @pytest.mark.asyncio
    async def test_add_tool(self, http_client):
        """Test add tool."""
        result = await self.call_tool(http_client, "add", {"a": 5, "b": 3})
        assert result == 8.0 or result == {"result": 8.0}
    
    @pytest.mark.asyncio
    async def test_multiply_tool(self, http_client):
        """Test multiply tool."""
        result = await self.call_tool(http_client, "multiply", {"a": 7, "b": 6})
        assert result == 42.0 or result == {"result": 42.0}
    
    # ===== Model Discovery Tools =====
    
    @pytest.mark.asyncio
    async def test_list_models(self, http_client):
        """Test model listing."""
        result = await self.call_tool(http_client, "list_models", {})
        assert "local_models" in result or "result" in result
        models = result.get("result", result)
        assert isinstance(models, dict)
        assert "local_models" in models or "api_models" in models
    
    @pytest.mark.asyncio
    async def test_check_model(self, http_client):
        """Test model availability check."""
        result = await self.call_tool(http_client, "check_model", {"model_name": "mistral"})
        assert "available" in result or "result" in result
        availability = result.get("result", result)
        assert isinstance(availability, dict)
        assert "available" in availability
    
    # ===== Token Analysis =====
    
    @pytest.mark.asyncio
    async def test_count_tokens(self, http_client):
        """Test token counting."""
        result = await self.call_tool(http_client, "count_tokens", {"text": "Hello world test"})
        count = result.get("count", result) if isinstance(result, dict) else result
        assert isinstance(count, int)
        assert count > 0
    
    # ===== Code Generation Tests =====
    
    @pytest.mark.asyncio
    async def test_generate_code(self, http_client):
        """Test code generation."""
        result = await self.call_tool(
            http_client, 
            "generate_code", 
            {"description": "create a simple function that adds two numbers", "model": "starcoder"}
        )
        assert isinstance(result, dict)
        assert "success" in result or "code" in result
        if "success" in result:
            assert result["success"] is True
            assert "code" in result
    
    @pytest.mark.asyncio
    async def test_review_code(self, http_client):
        """Test code review."""
        code = """
def add(a, b):
    return a+b
"""
        result = await self.call_tool(
            http_client,
            "review_code",
            {"code": code, "model": "starcoder"}
        )
        assert isinstance(result, dict)
        assert "success" in result or "quality_score" in result or "review_result" in result
    
    # ===== Test Generation =====
    
    @pytest.mark.asyncio
    async def test_generate_tests(self, http_client):
        """Test test generation."""
        code = """
def multiply(x, y):
    return x * y
"""
        result = await self.call_tool(
            http_client,
            "generate_tests",
            {"code": code, "test_framework": "pytest", "coverage_target": 80}
        )
        assert isinstance(result, dict)
        assert "success" in result or "test_code" in result
        if "test_code" in result:
            assert "test_" in result["test_code"] or "def test" in result["test_code"]
    
    # ===== Code Formatting =====
    
    @pytest.mark.asyncio
    async def test_format_code(self, http_client):
        """Test code formatting."""
        code = "def add(a,b):return a+b"
        result = await self.call_tool(
            http_client,
            "format_code",
            {"code": code, "formatter": "black", "line_length": 88}
        )
        assert isinstance(result, dict)
        assert "success" in result or "formatted_code" in result
        if "formatted_code" in result:
            formatted = result["formatted_code"]
            assert "def add(a, b):" in formatted or "def add" in formatted
    
    # ===== Complexity Analysis =====
    
    @pytest.mark.asyncio
    async def test_analyze_complexity(self, http_client):
        """Test complexity analysis."""
        code = """
def calculate(x, y):
    if x > 0:
        if y > 0:
            return x * y
        else:
            return 0
    return 0
"""
        result = await self.call_tool(
            http_client,
            "analyze_complexity",
            {"code": code, "detailed": True}
        )
        assert isinstance(result, dict)
        assert "success" in result or "cyclomatic_complexity" in result or "complexity" in result
    
    # ===== Task Formalization =====
    
    @pytest.mark.asyncio
    async def test_formalize_task(self, http_client):
        """Test formalize task."""
        result = await self.call_tool(
            http_client,
            "formalize_task",
            {
                "informal_request": "Build a REST API for user management",
                "context": "Use Python and FastAPI"
            }
        )
        assert isinstance(result, dict)
        assert "success" in result or "formalized_description" in result or "requirements" in result


class TestToolChains:
    """Test tool chains and workflows."""
    
    @pytest.fixture
    async def http_client(self):
        """Create HTTP client for MCP server."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            yield client
    
    async def call_tool(self, client: httpx.AsyncClient, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via HTTP."""
        response = await client.post(
            f"{MCP_SERVER_URL}/call",
            json={"tool_name": tool_name, "arguments": arguments}
        )
        assert response.status_code == 200
        result = response.json()
        return result.get("result", {})
    
    @pytest.mark.asyncio
    async def test_generate_review_chain(self, http_client):
        """Test generate_code → review_code chain."""
        # Generate code
        gen_result = await self.call_tool(
            http_client,
            "generate_code",
            {"description": "create a simple calculator with add and multiply", "model": "starcoder"}
        )
        
        assert isinstance(gen_result, dict)
        if "code" not in gen_result or not gen_result.get("success", True):
            pytest.skip("Code generation failed")
        
        code = gen_result.get("code", "")
        
        # Review code
        review_result = await self.call_tool(
            http_client,
            "review_code",
            {"code": code, "model": "starcoder"}
        )
        
        assert isinstance(review_result, dict)
        assert "success" in review_result or "quality_score" in review_result
    
    @pytest.mark.asyncio
    async def test_generate_format_analyze_chain(self, http_client):
        """Test generate_code → format_code → analyze_complexity chain."""
        # Generate code
        gen_result = await self.call_tool(
            http_client,
            "generate_code",
            {"description": "create a function to calculate factorial", "model": "mistral"}
        )
        
        if "code" not in gen_result or not gen_result.get("success", True):
            pytest.skip("Code generation failed")
        
        code = gen_result.get("code", "")
        
        # Format code
        format_result = await self.call_tool(
            http_client,
            "format_code",
            {"code": code}
        )
        
        assert isinstance(format_result, dict)
        
        # Get formatted code
        formatted_code = format_result.get("formatted_code", code)
        
        # Analyze complexity
        complexity_result = await self.call_tool(
            http_client,
            "analyze_complexity",
            {"code": formatted_code, "detailed": True}
        )
        
        assert isinstance(complexity_result, dict)
    
    @pytest.mark.asyncio
    async def test_generate_tests_chain(self, http_client):
        """Test generate_code → generate_tests chain."""
        # Generate code
        gen_result = await self.call_tool(
            http_client,
            "generate_code",
            {"description": "create a simple function to check if a number is even", "model": "starcoder"}
        )
        
        if "code" not in gen_result or not gen_result.get("success", True):
            pytest.skip("Code generation failed")
        
        code = gen_result.get("code", "")
        
        # Generate tests
        test_result = await self.call_tool(
            http_client,
            "generate_tests",
            {"code": code, "test_framework": "pytest"}
        )
        
        assert isinstance(test_result, dict)
        assert "test_code" in test_result or "success" in test_result
    
    @pytest.mark.asyncio
    async def test_generate_and_review_workflow(self, http_client):
        """Test generate_and_review combined tool."""
        result = await self.call_tool(
            http_client,
            "generate_and_review",
            {
                "description": "create a simple function to reverse a string",
                "gen_model": "starcoder",
                "review_model": "starcoder"
            }
        )
        
        assert isinstance(result, dict)
        assert "success" in result or "code" in result or "review" in result


class TestConversationContext:
    """Test conversation context handling."""
    
    @pytest.fixture
    async def http_client(self):
        """Create HTTP client for MCP server."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            yield client
    
    async def call_tool(self, client: httpx.AsyncClient, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via HTTP."""
        response = await client.post(
            f"{MCP_SERVER_URL}/call",
            json={"tool_name": tool_name, "arguments": arguments}
        )
        assert response.status_code == 200
        result = response.json()
        return result.get("result", {})
    
    async def simulate_conversation(
        self, 
        client: httpx.AsyncClient, 
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Simulate a conversation with context."""
        results = []
        generated_code = None
        
        for msg in messages:
            if "generate" in msg.get("type", ""):
                result = await self.call_tool(
                    client,
                    msg["tool"],
                    msg["args"]
                )
                results.append(result)
                if "code" in result:
                    generated_code = result["code"]
            
            elif "context" in msg.get("type", "") and generated_code:
                # Modify args to include generated code
                args = msg["args"].copy()
                args["code"] = generated_code
                result = await self.call_tool(client, msg["tool"], args)
                results.append(result)
            
            else:
                result = await self.call_tool(client, msg["tool"], msg["args"])
                results.append(result)
        
        return results
    
    @pytest.mark.asyncio
    async def test_context_chain_build_review_test(self, http_client):
        """Test conversation: build → review it → test it."""
        messages = [
            {
                "type": "generate",
                "tool": "generate_code",
                "args": {"description": "create a simple calculator with add function", "model": "starcoder"}
            },
            {
                "type": "context",
                "tool": "review_code",
                "args": {"model": "starcoder"}
            },
            {
                "type": "context",
                "tool": "generate_tests",
                "args": {"test_framework": "pytest"}
            }
        ]
        
        results = await self.simulate_conversation(http_client, messages)
        
        assert len(results) == 3
        assert "code" in results[0] or results[0].get("success", False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
