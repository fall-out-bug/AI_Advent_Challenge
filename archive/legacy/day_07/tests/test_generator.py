"""Unit tests for code generator agent."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from agents.core.code_generator import CodeGeneratorAgent
from communication.message_schema import CodeGenerationRequest, TaskMetadata


class TestCodeGeneratorAgent:
    """Test cases for CodeGeneratorAgent."""

    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return CodeGeneratorAgent(
            model_name="starcoder", max_tokens=500, temperature=0.3
        )

    @pytest.fixture
    def mock_model_response(self):
        """Mock model response."""
        return {
            "response": """
### FUNCTION
```python
def factorial(n: int) -> int:
    \"\"\"Calculate factorial of a number.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n
        
    Raises:
        ValueError: If n is negative
    \"\"\"
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

### TESTS
```python
import pytest

def test_factorial():
    \"\"\"Test factorial function.\"\"\"
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120

def test_factorial_negative():
    \"\"\"Test factorial with negative input.\"\"\"
    with pytest.raises(ValueError):
        factorial(-1)
```

### METADATA
Complexity: medium
Lines of Code: 15
Dependencies: []
Estimated Time: O(n)
""",
            "input_tokens": 150,
            "response_tokens": 300,
            "total_tokens": 450,
        }

    @pytest.fixture
    def generation_request(self):
        """Create a test generation request."""
        return CodeGenerationRequest(
            task_description="Create a function to calculate factorial",
            language="python",
            requirements=["Include type hints", "Handle edge cases"],
            max_tokens=1000,
        )

    @pytest.mark.asyncio
    async def test_process_success(
        self, agent, generation_request, mock_model_response
    ):
        """Test successful code generation."""
        with patch.object(agent, "_call_model", return_value=mock_model_response):
            result = await agent.process(generation_request)

            assert result.task_description == generation_request.task_description
            assert "def factorial" in result.generated_code
            assert "test_factorial" in result.tests
            assert result.metadata.complexity == "medium"
            assert result.metadata.lines_of_code == 15
            assert result.tokens_used == 450
            assert isinstance(result.generation_time, datetime)

    @pytest.mark.asyncio
    async def test_process_model_failure(self, agent, generation_request):
        """Test handling of model failure."""
        with patch.object(agent, "_call_model", side_effect=Exception("Model error")):
            with pytest.raises(Exception, match="Model error"):
                await agent.process(generation_request)

            assert agent.stats["failed_requests"] == 1

    def test_extract_code_from_response(self, agent):
        """Test code extraction from response."""
        response = """
Some text before
```python
def test_function():
    return "hello"
```
Some text after
"""
        code = agent._extract_code_from_response(response)
        assert "def test_function" in code
        assert 'return "hello"' in code

    def test_extract_tests_from_response(self, agent):
        """Test test extraction from response."""
        response = """
### TESTS
```python
import pytest

def test_something():
    assert True
```
"""
        tests = agent._extract_tests_from_response(response)
        assert "import pytest" in tests
        assert "def test_something" in tests

    def test_extract_metadata_from_response(self, agent):
        """Test metadata extraction from response."""
        response = """
Complexity: high
Lines of Code: 42
Dependencies: ["requests", "pandas"]
Estimated Time: O(n log n)
"""
        metadata = agent._extract_metadata_from_response(response)
        assert metadata.complexity == "high"
        assert metadata.lines_of_code == 42
        assert "requests" in metadata.dependencies
        assert metadata.estimated_time == "O(n log n)"

    def test_validate_generated_code_valid(self, agent):
        """Test validation of valid code."""
        valid_code = """
import os
from typing import List

def process_data(items: List[str]) -> List[str]:
    \"\"\"Process a list of items.\"\"\"
    return [item.upper() for item in items]
"""
        issues = agent.validate_generated_code(valid_code)
        assert len(issues) == 0

    def test_validate_generated_code_invalid(self, agent):
        """Test validation of invalid code."""
        invalid_code = "def broken_function("  # Missing closing parenthesis
        issues = agent.validate_generated_code(invalid_code)
        assert len(issues) > 0
        assert any("Syntax error" in issue for issue in issues)

    def test_validate_generated_code_missing_elements(self, agent):
        """Test validation of code missing required elements."""
        incomplete_code = "print('hello')"  # No imports, no functions, no docstrings
        issues = agent.validate_generated_code(incomplete_code)
        assert len(issues) > 0
        assert any("No imports found" in issue for issue in issues)
        assert any("No function definitions found" in issue for issue in issues)

    @pytest.mark.asyncio
    async def test_generate_tests_separately(self, agent):
        """Test separate test generation."""
        function_code = "def add(a, b): return a + b"
        task_description = "Create addition function"

        mock_response = {
            "response": """
```python
import pytest

def test_add():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
```
""",
            "total_tokens": 100,
        }

        with patch.object(agent, "_call_model", return_value=mock_response):
            tests = await agent._generate_tests_separately(
                function_code, task_description
            )
            assert "def test_add" in tests
            assert "assert add(2, 3) == 5" in tests

    @pytest.mark.asyncio
    async def test_generate_tests_separately_failure(self, agent):
        """Test fallback when separate test generation fails."""
        function_code = "def add(a, b): return a + b"
        task_description = "Create addition function"

        with patch.object(
            agent, "_call_model", side_effect=Exception("Test generation failed")
        ):
            tests = await agent._generate_tests_separately(
                function_code, task_description
            )
            assert "def test_add" in tests  # Should create basic template
            assert "TODO" in tests  # Should have TODO comments

    def test_create_basic_test_template(self, agent):
        """Test creation of basic test template."""
        function_code = "def calculate_sum(a, b): return a + b"
        template = agent._create_basic_test_template(function_code)

        assert "def test_calculate_sum" in template
        assert "TODO" in template
        assert "import pytest" in template

    def test_create_basic_test_template_no_function(self, agent):
        """Test basic test template when no function found."""
        function_code = "print('hello')"
        template = agent._create_basic_test_template(function_code)

        assert "# No function found to test" in template

    @pytest.mark.asyncio
    async def test_refine_code(self, agent):
        """Test code refinement."""
        original_code = "def add(a, b): return a + b"
        feedback = "Add type hints and docstring"

        mock_response = {
            "response": """
```python
def add(a: int, b: int) -> int:
    \"\"\"Add two integers.\"\"\"
    return a + b
```
""",
            "total_tokens": 50,
        }

        with patch.object(agent, "_call_model", return_value=mock_response):
            refined_code = await agent.refine_code(original_code, feedback)
            assert ": int" in refined_code
            assert '"""' in refined_code

    @pytest.mark.asyncio
    async def test_refine_code_failure(self, agent):
        """Test code refinement failure fallback."""
        original_code = "def add(a, b): return a + b"
        feedback = "Add type hints"

        with patch.object(
            agent, "_call_model", side_effect=Exception("Refinement failed")
        ):
            refined_code = await agent.refine_code(original_code, feedback)
            assert refined_code == original_code  # Should return original code

    def test_get_uptime(self, agent):
        """Test uptime calculation."""
        uptime = agent.get_uptime()
        assert uptime >= 0
        assert isinstance(uptime, float)

    def test_get_average_response_time(self, agent):
        """Test average response time calculation."""
        # Add some mock response times
        agent.stats["response_times"] = [1.0, 2.0, 3.0]
        avg_time = agent.get_average_response_time()
        assert avg_time == 2.0

        # Test with no response times
        agent.stats["response_times"] = []
        avg_time = agent.get_average_response_time()
        assert avg_time == 0.0
