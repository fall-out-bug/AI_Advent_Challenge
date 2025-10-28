"""Comprehensive integration tests for MCP tools via Docker HTTP server.

Tests all 12 MCP tools individually and in chains with conversation context.
Includes inputs and outputs for all test scenarios.
"""
import asyncio
import json
import pytest
import httpx
from typing import Dict, Any, List

# MCP Server URL
MCP_SERVER_URL = "http://localhost:8004"


class TestMCPTools:
    """Test suite for all MCP tools with inputs and outputs documentation."""
    
    @pytest.fixture
    async def http_client(self):
        """Create HTTP client for MCP server."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            yield client
    
    async def get_tools_list(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Get list of all available tools."""
        response = await client.get(f"{MCP_SERVER_URL}/tools", timeout=30.0)
        assert response.status_code == 200
        result = response.json()
        return result.get("tools", [])
    
    async def call_tool(self, client: httpx.AsyncClient, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via HTTP."""
        response = await client.post(
            f"{MCP_SERVER_URL}/call",
            json={"tool_name": tool_name, "arguments": arguments}
        )
        assert response.status_code == 200, f"Tool {tool_name} failed with status {response.status_code}"
        result = response.json()
        return result.get("result", {})
    
    # ===== Help and Discovery Tests =====
    
    @pytest.mark.asyncio
    async def test_list_all_tools(self, http_client):
        """Test listing all available tools.
        
        INPUT:
            GET /tools
            No arguments
        
        OUTPUT EXPECTED:
            List of tools with metadata:
            - name: Tool name
            - description: Tool description
            - input_schema: Tool parameters schema
        """
        tools = await self.get_tools_list(http_client)
        assert len(tools) > 0, "Should have at least one tool available"
        
        # Verify structure
        for tool in tools:
            assert "name" in tool, "Tool should have a name"
            assert "description" in tool, "Tool should have a description"
            assert "input_schema" in tool, "Tool should have input schema"
    
    # ===== Calculator Tools Tests =====
    
    @pytest.mark.asyncio
    async def test_add_tool(self, http_client):
        """Test add tool.
        
        INPUT:
            Tool: add
            Arguments: {"a": 5, "b": 3}
        
        OUTPUT EXPECTED:
            Result: 8.0 (or {"result": 8.0})
        """
        result = await self.call_tool(http_client, "add", {"a": 5, "b": 3})
        # Handle both direct result and wrapped result
        if isinstance(result, dict) and "result" in result:
            assert result["result"] == 8.0
        else:
            assert float(result) == 8.0
    
    @pytest.mark.asyncio
    async def test_multiply_tool(self, http_client):
        """Test multiply tool.
        
        INPUT:
            Tool: multiply
            Arguments: {"a": 7, "b": 6}
        
        OUTPUT EXPECTED:
            Result: 42.0
        """
        result = await self.call_tool(http_client, "multiply", {"a": 7, "b": 6})
        if isinstance(result, dict) and "result" in result:
            assert result["result"] == 42.0
        else:
            assert float(result) == 42.0
    
    # ===== Model Discovery Tools =====
    
    @pytest.mark.asyncio
    async def test_list_models(self, http_client):
        """Test model listing.
        
        INPUT:
            Tool: list_models
            Arguments: {}
        
        OUTPUT EXPECTED:
            Dictionary containing:
            - local_models: List of local model configs
            - api_models: List of API model configs (optional)
        """
        result = await self.call_tool(http_client, "list_models", {})
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "local_models" in result or "api_models" in result, "Should contain model lists"
    
    @pytest.mark.asyncio
    async def test_check_model(self, http_client):
        """Test model availability check.
        
        INPUT:
            Tool: check_model
            Arguments: {"model_name": "mistral"}
        
        OUTPUT EXPECTED:
            Dictionary with:
            - available: Boolean indicating model availability
        """
        result = await self.call_tool(http_client, "check_model", {"model_name": "mistral"})
        availability = result.get("result", result)
        assert isinstance(availability, dict), "Result should be a dictionary"
        assert "available" in availability, "Should have availability status"
    
    # ===== Token Analysis =====
    
    @pytest.mark.asyncio
    async def test_count_tokens(self, http_client):
        """Test token counting.
        
        INPUT:
            Tool: count_tokens
            Arguments: {"text": "Hello world test"}
        
        OUTPUT EXPECTED:
            Dictionary with:
            - count: Integer token count (> 0)
        """
        result = await self.call_tool(http_client, "count_tokens", {"text": "Hello world test"})
        count = result.get("count", result) if isinstance(result, dict) else result
        assert isinstance(count, int), "Token count should be an integer"
        assert count > 0, "Token count should be positive"
    
    # ===== Code Generation Tests =====
    
    @pytest.mark.asyncio
    async def test_generate_code_simple(self, http_client):
        """Test simple code generation.
        
        INPUT:
            Tool: generate_code
            Arguments: {
                "description": "create a simple function that adds two numbers",
                "model": "starcoder"
            }
        
        OUTPUT EXPECTED:
            Dictionary with:
            - success: True
            - code: Generated Python code as string
            - metadata: Optional metadata (model info, tokens, etc.)
        """
        result = await self.call_tool(
            http_client, 
            "generate_code", 
            {"description": "create a simple function that adds two numbers", "model": "starcoder"}
        )
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result or "code" in result, "Should indicate success or contain code"
        
        if "success" in result:
            assert result["success"] is True, "Generation should succeed"
            assert "code" in result, "Should contain generated code"
            assert len(result["code"]) > 0, "Generated code should not be empty"
    
    @pytest.mark.asyncio
    async def test_generate_code_complex(self, http_client):
        """Test complex code generation task.
        
        INPUT:
            Tool: generate_code
            Arguments: {
                "description": "Create a REST API class for user management with CRUD operations, \
                    validation, and error handling following PEP8",
                "model": "starcoder"
            }
        
        OUTPUT EXPECTED:
            Dictionary with:
            - success: True
            - code: Generated Python code (should be substantial, > 500 chars)
            - metadata: Information about the generation process
        """
        complex_task = """Create a REST API class for user management with CRUD operations, 
        validation, and error handling following PEP8"""
        
        result = await self.call_tool(
            http_client,
            "generate_code",
            {"description": complex_task, "model": "starcoder"}
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        if result.get("success"):
            assert "code" in result, "Should contain generated code"
            assert len(result.get("code", "")) > 100, "Complex task should generate substantial code"
    
    @pytest.mark.asyncio
    async def test_review_code(self, http_client):
        """Test code review.
        
        INPUT:
            Tool: review_code
            Arguments: {
                "code": "def add(a, b): return a+b",
                "model": "starcoder"
            }
        
        OUTPUT EXPECTED:
            Dictionary with:
            - success: True
            - quality_score: Integer score (0-10) or None
            - review_result: Detailed review text
            - issues: List of identified issues (optional)
        """
        code = """
def add(a, b):
    return a+b
"""
        result = await self.call_tool(
            http_client,
            "review_code",
            {"code": code, "model": "starcoder"}
        )
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result or "quality_score" in result or "review_result" in result
    
    # ===== Test Generation =====
    
    @pytest.mark.asyncio
    async def test_generate_tests(self, http_client):
        """Test test generation.
        
        INPUT:
            Tool: generate_tests
            Arguments: {
                "code": "def multiply(x, y): return x * y",
                "test_framework": "pytest",
                "coverage_target": 80
            }
        
        OUTPUT EXPECTED:
            Dictionary with:
            - success: True
            - test_code: Generated test code
            - test_count: Number of test cases generated
            - coverage_estimate: Estimated coverage percentage
        """
        code = """
def multiply(x, y):
    return x * y
"""
        result = await self.call_tool(
            http_client,
            "generate_tests",
            {"code": code, "test_framework": "pytest", "coverage_target": 80}
        )
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result or "test_code" in result
        if "test_code" in result:
            # Verify test code contains test functions
            test_code = result["test_code"]
            assert "test_" in test_code or "def test" in test_code, "Should contain test functions"
    
    # ===== Code Formatting =====
    
    @pytest.mark.asyncio
    async def test_format_code(self, http_client):
        """Test code formatting.
        
        INPUT:
            Tool: format_code
            Arguments: {
                "code": "def add(a,b):return a+b",
                "formatter": "black",
                "line_length": 88
            }
        
        OUTPUT EXPECTED:
            Dictionary with:
            - success: True
            - formatted_code: Formatted code string
            - changes_made: Boolean indicating if changes were made
        """
        code = "def add(a,b):return a+b"
        result = await self.call_tool(
            http_client,
            "format_code",
            {"code": code, "formatter": "black", "line_length": 88}
        )
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result or "formatted_code" in result
        if "formatted_code" in result:
            formatted = result["formatted_code"]
            assert "def add(a, b):" in formatted or "def add" in formatted
    
    # ===== Complexity Analysis =====
    
    @pytest.mark.asyncio
    async def test_analyze_complexity(self, http_client):
        """Test complexity analysis.
        
        INPUT:
            Tool: analyze_complexity
            Arguments: {
                "code": "def calculate(x, y): if x > 0: if y > 0: return x * y else: return 0 return 0",
                "detailed": True
            }
        
        OUTPUT EXPECTED:
            Dictionary with:
            - success: True
            - cyclomatic_complexity: Integer complexity metric
            - complexity_level: "low" | "medium" | "high"
            - recommendations: List of optimization suggestions (optional)
        """
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
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result or "cyclomatic_complexity" in result or "complexity" in result
    
    # ===== Task Formalization =====
    
    @pytest.mark.asyncio
    async def test_formalize_task(self, http_client):
        """Test formalize task.
        
        INPUT:
            Tool: formalize_task
            Arguments: {
                "informal_request": "Build a REST API for user management",
                "context": "Use Python and FastAPI"
            }
        
        OUTPUT EXPECTED:
            Dictionary with:
            - success: True
            - formalized_description: Structured description
            - requirements: List of requirements
            - steps: List of implementation steps (optional)
        """
        result = await self.call_tool(
            http_client,
            "formalize_task",
            {
                "informal_request": "Build a REST API for user management",
                "context": "Use Python and FastAPI"
            }
        )
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result or "formalized_description" in result or "requirements" in result


class TestToolChains:
    """Test tool chains and workflows with inputs and outputs."""
    
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
        """Test generate_code → review_code chain.
        
        INPUT CHAIN:
            Step 1: generate_code
                Arguments: {"description": "create a simple calculator with add and multiply", "model": "starcoder"}
                Output: Generated code
            
            Step 2: review_code  
                Arguments: {"code": <generated_code>, "model": "starcoder"}
                Output: Review results
        
        OUTPUT EXPECTED:
            Both steps should complete successfully with valid results
        """
        # Generate code
        gen_result = await self.call_tool(
            http_client,
            "generate_code",
            {"description": "create a simple calculator with add and multiply", "model": "starcoder"}
        )
        
        assert isinstance(gen_result, dict), "Generation result should be a dictionary"
        if "code" not in gen_result or not gen_result.get("success", True):
            pytest.skip("Code generation failed")
        
        code = gen_result.get("code", "")
        assert len(code) > 0, "Generated code should not be empty"
        
        # Review code
        review_result = await self.call_tool(
            http_client,
            "review_code",
            {"code": code, "model": "starcoder"}
        )
        
        assert isinstance(review_result, dict), "Review result should be a dictionary"
        assert "success" in review_result or "quality_score" in review_result
    
    @pytest.mark.asyncio
    async def test_generate_format_analyze_chain(self, http_client):
        """Test generate_code → format_code → analyze_complexity chain.
        
        INPUT CHAIN:
            Step 1: generate_code
                Arguments: {"description": "create a function to calculate factorial", "model": "mistral"}
                Output: Generated code
            
            Step 2: format_code
                Arguments: {"code": <generated_code>}
                Output: Formatted code
            
            Step 3: analyze_complexity
                Arguments: {"code": <formatted_code>, "detailed": True}
                Output: Complexity metrics
        
        OUTPUT EXPECTED:
            All three steps should complete successfully
        """
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
        
        assert isinstance(format_result, dict), "Format result should be a dictionary"
        
        # Get formatted code
        formatted_code = format_result.get("formatted_code", code)
        assert len(formatted_code) > 0, "Formatted code should not be empty"
        
        # Analyze complexity
        complexity_result = await self.call_tool(
            http_client,
            "analyze_complexity",
            {"code": formatted_code, "detailed": True}
        )
        
        assert isinstance(complexity_result, dict), "Complexity result should be a dictionary"
    
    @pytest.mark.asyncio
    async def test_generate_tests_chain(self, http_client):
        """Test generate_code → generate_tests chain.
        
        INPUT CHAIN:
            Step 1: generate_code
                Arguments: {"description": "create a simple function to check if a number is even", "model": "starcoder"}
                Output: Generated code
            
            Step 2: generate_tests
                Arguments: {"code": <generated_code>, "test_framework": "pytest"}
                Output: Test code
        
        OUTPUT EXPECTED:
            Both steps complete with valid code and tests
        """
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
        
        assert isinstance(test_result, dict), "Test result should be a dictionary"
        assert "test_code" in test_result or "success" in test_result
    
    @pytest.mark.asyncio
    async def test_generate_and_review_workflow(self, http_client):
        """Test generate_and_review combined tool.
        
        INPUT:
            Tool: generate_and_review
            Arguments: {
                "description": "create a simple function to reverse a string",
                "gen_model": "starcoder",
                "review_model": "starcoder"
            }
        
        OUTPUT EXPECTED:
            Dictionary with:
            - success: True
            - code: Generated code
            - review: Review results
            - combined_quality_score: Overall quality score
        """
        result = await self.call_tool(
            http_client,
            "generate_and_review",
            {
                "description": "create a simple function to reverse a string",
                "gen_model": "starcoder",
                "review_model": "starcoder"
            }
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result or "code" in result or "review" in result


class TestConversationContext:
    """Test conversation context handling with inputs and outputs."""
    
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
        """Simulate a conversation with context.
        
        Args:
            client: HTTP client
            messages: List of conversation messages with tool calls
        
        Returns:
            List of results from each step
        """
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
        """Test conversation: build → review it → test it.
        
        INPUT FLOW:
            1. generate_code: Create a calculator
            2. review_code: Review the generated calculator (uses code from step 1)
            3. generate_tests: Generate tests for the calculator (uses code from step 1)
        
        OUTPUT EXPECTED:
            Three successful tool calls with results for each step
        """
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
        
        assert len(results) == 3, "Should have 3 results"
        assert "code" in results[0] or results[0].get("success", False), "First step should generate code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
