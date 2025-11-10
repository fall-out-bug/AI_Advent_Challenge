"""Unit tests for base agent.

Following TDD principles and the Zen of Python:
- Tests should be simple and readable
- One test per behavior
- Clear assertions
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.agents.base_agent import BaseAgent, TaskMetadata


# Mock implementation of BaseAgent for testing
# Note: TestAgent is not a test class, it's a concrete implementation
class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    def __init__(self, model_client=None):
        """Initialize test agent."""
        super().__init__(
            model_name="test_model",
            agent_type="test",
            model_client=model_client,
        )

    async def process(self, request: str) -> str:
        """Process a request."""
        response = await self._call_model(prompt=request)
        return response.get("response", "")


class MockModelClient:
    """Mock model client for testing."""

    def __init__(self):
        """Initialize mock client."""
        self.call_count = 0

    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        """Generate mock response."""
        self.call_count += 1
        return {
            "response": f"Response to: {prompt}",
            "total_tokens": 100,
        }


@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test base agent initialization."""
    agent = ConcreteTestAgent()

    assert agent.model_name == "test_model"
    assert agent.agent_type == "test"
    assert agent.max_tokens == 1000  # DEFAULT_MAX_TOKENS
    assert agent.temperature == 0.7  # DEFAULT_TEMPERATURE
    assert agent.stats["total_requests"] == 0
    assert agent.stats["successful_requests"] == 0


@pytest.mark.asyncio
async def test_base_agent_stats_tracking():
    """Test that agent tracks statistics."""
    mock_client = MockModelClient()
    agent = ConcreteTestAgent(model_client=mock_client)

    # Make a call
    await agent.process("test prompt")

    # Check stats
    assert agent.stats["total_requests"] == 1
    assert agent.stats["successful_requests"] == 1
    assert agent.stats["failed_requests"] == 0
    assert agent.stats["total_tokens_used"] == 100
    assert len(agent.stats["response_times"]) == 1


@pytest.mark.asyncio
async def test_base_agent_error_handling():
    """Test that agent handles errors properly."""

    async def failing_generate(*args, **kwargs):
        """Simulate failing model call."""
        raise Exception("Model error")

    client = MagicMock()
    client.generate = AsyncMock(side_effect=failing_generate)

    agent = ConcreteTestAgent(model_client=client)

    # Should raise exception
    with pytest.raises(Exception, match="Model error"):
        await agent.process("test prompt")

    # Stats should reflect failure
    assert agent.stats["total_requests"] == 1
    assert agent.stats["successful_requests"] == 0
    assert agent.stats["failed_requests"] == 1


def test_task_metadata_creation():
    """Test task metadata creation."""
    metadata = TaskMetadata(
        complexity="high",
        lines_of_code=50,
        estimated_time="10 minutes",
        dependencies=["requests", "pydantic"],
    )

    assert metadata.complexity == "high"
    assert metadata.lines_of_code == 50
    assert metadata.estimated_time == "10 minutes"
    assert metadata.dependencies == ["requests", "pydantic"]


def test_task_metadata_defaults():
    """Test task metadata with default values."""
    metadata = TaskMetadata()

    assert metadata.complexity == "medium"
    assert metadata.lines_of_code == 0
    assert metadata.estimated_time is None
    assert metadata.dependencies == []


def test_task_metadata_to_dict():
    """Test converting metadata to dictionary."""
    metadata = TaskMetadata(
        complexity="low",
        lines_of_code=10,
        dependencies=["test"],
    )

    data = metadata.to_dict()

    assert data["complexity"] == "low"
    assert data["lines_of_code"] == 10
    assert data["dependencies"] == ["test"]


def test_task_metadata_from_dict():
    """Test creating metadata from dictionary."""
    data = {
        "complexity": "high",
        "lines_of_code": 100,
        "estimated_time": "1 hour",
        "dependencies": ["pytest"],
    }

    metadata = TaskMetadata.from_dict(data)

    assert metadata.complexity == "high"
    assert metadata.lines_of_code == 100
    assert metadata.estimated_time == "1 hour"
    assert metadata.dependencies == ["pytest"]


def test_extract_code_from_response():
    """Test extracting code from response."""
    agent = ConcreteTestAgent()

    # Test with markdown code block
    response = "Here's the code:\n```python\ndef hello():\n    pass\n```"
    code = agent._extract_code_from_response(response)
    assert "def hello():" in code

    # Test with function definition
    response = "def test():\n    return True"
    code = agent._extract_code_from_response(response)
    assert "def test():" in code
    assert "return True" in code


def test_extract_tests_from_response():
    """Test extracting tests from response."""
    agent = ConcreteTestAgent()

    # Test with test patterns
    response = "### TESTS\n```python\nimport pytest\n\ndef test_func():\n    pass\n```"
    tests = agent._extract_tests_from_response(response)
    assert "import pytest" in tests
    assert "def test_func():" in tests

    # Test empty response
    response = "No tests here"
    tests = agent._extract_tests_from_response(response)
    assert tests == ""


def test_extract_metadata_from_response():
    """Test extracting metadata from response."""
    agent = ConcreteTestAgent()

    response = """
    Complexity: high
    Lines of Code: 25
    Dependencies: [requests, pydantic]
    Estimated Time: 5 minutes
    """

    metadata = agent._extract_metadata_from_response(response)

    assert metadata.complexity == "high"
    assert metadata.lines_of_code == 25
    assert metadata.dependencies == ["requests", "pydantic"]
    assert metadata.estimated_time == "5 minutes"


def test_extract_metadata_defaults():
    """Test metadata extraction with defaults."""
    agent = ConcreteTestAgent()

    response = "No metadata here"

    metadata = agent._extract_metadata_from_response(response)

    assert metadata.complexity == "medium"
    assert metadata.lines_of_code == 0
    assert metadata.dependencies == []


def test_parse_json_response():
    """Test parsing JSON response."""
    agent = ConcreteTestAgent()

    # Test with JSON code block
    response = '```json\n{"key": "value"}\n```'
    data = agent._parse_json_response(response)
    assert data["key"] == "value"

    # Test with plain JSON
    response = 'Some text {"result": 42} more text'
    data = agent._parse_json_response(response)
    assert data["result"] == 42


def test_parse_json_response_invalid():
    """Test parsing invalid JSON."""
    agent = ConcreteTestAgent()

    response = "Not valid JSON at all"

    with pytest.raises(ValueError, match="No valid JSON"):
        agent._parse_json_response(response)


def test_get_uptime():
    """Test getting agent uptime."""
    agent = ConcreteTestAgent()

    # Should be close to 0 initially
    uptime = agent.get_uptime()
    assert uptime >= 0
    assert uptime < 1  # Should be less than 1 second


def test_get_average_response_time():
    """Test getting average response time."""
    mock_client = MockModelClient()
    agent = ConcreteTestAgent(model_client=mock_client)

    # Initially should be 0
    assert agent.get_average_response_time() == 0.0

    # After making calls, should calculate average
    # Note: We can't easily test this without actual timing,
    # so we just verify the method exists and handles empty case
    agent.stats["response_times"] = [0.1, 0.2, 0.3]
    avg_time = agent.get_average_response_time()
    # Use pytest.approx for floating point comparison
    assert avg_time == pytest.approx(0.2, abs=0.001)


def test_abstract_method():
    """Test that abstract method is enforced."""
    # Abstract base class should enforce abstract methods
    # Python's ABC will prevent instantiation of IncompleteAgent

    class IncompleteAgent(BaseAgent):
        """Agent without process implementation."""

        def __init__(self):
            """Initialize."""
            super().__init__()

    # Should NOT be able to instantiate - abstract method not implemented
    with pytest.raises(TypeError, match="abstract method"):
        _ = IncompleteAgent()
