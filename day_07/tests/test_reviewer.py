"""Unit tests for code reviewer agent."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from agents.core.code_reviewer import CodeReviewerAgent
from communication.message_schema import (
    CodeQualityMetrics,
    CodeReviewRequest,
    TaskMetadata,
)


class TestCodeReviewerAgent:
    """Test cases for CodeReviewerAgent."""

    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return CodeReviewerAgent(
            model_name="starcoder", max_tokens=800, temperature=0.2
        )

    @pytest.fixture
    def mock_model_response(self):
        """Mock StarCoder response."""
        return {
            "response": """
```json
{
    "overall_score": 8.5,
    "metrics": {
        "pep8_compliance": true,
        "pep8_score": 9.0,
        "has_docstrings": true,
        "has_type_hints": true,
        "test_coverage": "good",
        "complexity_score": 7.0
    },
    "issues": [
        "Consider adding error handling for edge cases",
        "Missing input validation"
    ],
    "recommendations": [
        "Add comprehensive error handling",
        "Consider performance optimization",
        "Add more test cases"
    ]
}
```
""",
            "total_tokens": 250,
        }

    @pytest.fixture
    def review_request(self):
        """Create a test review request."""
        return CodeReviewRequest(
            task_description="Create a function to calculate factorial",
            generated_code="""
def factorial(n: int) -> int:
    \"\"\"Calculate factorial.\"\"\"
    if n <= 1:
        return 1
    return n * factorial(n - 1)
""",
            tests="""
def test_factorial():
    assert factorial(5) == 120
""",
            metadata=TaskMetadata(
                complexity="medium", lines_of_code=10, dependencies=["typing"]
            ),
        )

    @pytest.mark.asyncio
    async def test_process_success(self, agent, review_request, mock_model_response):
        """Test successful code review."""
        with patch.object(agent, "_call_model", return_value=mock_model_response):
            result = await agent.process(review_request)

            assert result.code_quality_score == 8.5
            assert result.metrics.pep8_compliance is True
            assert result.metrics.pep8_score == 9.0
            assert result.metrics.has_docstrings is True
            assert result.metrics.has_type_hints is True
            assert result.metrics.test_coverage == "good"
            assert result.metrics.complexity_score == 7.0
            assert len(result.issues) == 2
            assert len(result.recommendations) == 3
            assert result.tokens_used == 250
            assert isinstance(result.review_time, datetime)

    @pytest.mark.asyncio
    async def test_process_starcoder_failure(self, agent, review_request):
        """Test handling of StarCoder failure."""
        with patch.object(
            agent, "_call_model", side_effect=Exception("StarCoder error")
        ):
            with pytest.raises(Exception, match="StarCoder error"):
                await agent.process(review_request)

            assert agent.stats["failed_requests"] == 1

    @pytest.mark.asyncio
    async def test_process_json_parsing_failure(self, agent, review_request):
        """Test handling of JSON parsing failure."""
        mock_response = {"response": "Invalid JSON response", "total_tokens": 100}

        with patch.object(agent, "_call_model", return_value=mock_response):
            result = await agent.process(review_request)

            # Should fallback to text parsing
            assert result.code_quality_score == 5.0  # Default score
            assert isinstance(result.metrics, CodeQualityMetrics)

    def test_parse_json_response_valid(self, agent):
        """Test parsing of valid JSON response."""
        response = """
Some text before
```json
{
    "overall_score": 9.0,
    "metrics": {
        "pep8_compliance": true,
        "pep8_score": 8.5
    },
    "issues": ["Issue 1"],
    "recommendations": ["Rec 1"]
}
```
Some text after
"""
        result = agent._parse_json_response(response)
        assert result["overall_score"] == 9.0
        assert result["metrics"]["pep8_compliance"] is True
        assert result["issues"] == ["Issue 1"]

    def test_parse_json_response_invalid(self, agent):
        """Test parsing of invalid JSON response."""
        response = "No JSON here"
        with pytest.raises(ValueError, match="No valid JSON found"):
            agent._parse_json_response(response)

    def test_parse_text_response(self, agent):
        """Test text response parsing fallback."""
        response = """
overall_score: 7.5
pep8_compliance: true
pep8_score: 8.0
has_docstrings: true
has_type_hints: false

issues:
- Missing type hints
- No error handling

recommendations:
- Add type hints
- Improve error handling
"""
        result = agent._parse_text_response(response)
        assert result["overall_score"] == 7.5
        assert result["metrics"]["pep8_compliance"] is True
        assert result["metrics"]["pep8_score"] == 8.0
        assert result["metrics"]["has_docstrings"] is True
        assert result["metrics"]["has_type_hints"] is False
        assert len(result["issues"]) == 2
        assert len(result["recommendations"]) == 2

    def test_extract_list_items(self, agent):
        """Test extraction of list items from text."""
        text = """
issues:
- First issue
- Second issue
- Third issue

recommendations:
- First recommendation
- Second recommendation
"""
        issues = agent._extract_list_items(text, "issues")
        recommendations = agent._extract_list_items(text, "recommendations")

        assert len(issues) == 3
        assert "First issue" in issues[0]
        assert "Second issue" in issues[1]
        assert "Third issue" in issues[2]

        assert len(recommendations) == 2
        assert "First recommendation" in recommendations[0]
        assert "Second recommendation" in recommendations[1]

    def test_extract_list_items_empty(self, agent):
        """Test extraction of list items when none found."""
        text = "No lists here"
        items = agent._extract_list_items(text, "issues")
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_analyze_pep8_compliance(self, agent):
        """Test PEP8 compliance analysis."""
        code = "def test_function():\n    return 'hello'"

        mock_response = {
            "response": """
PEP8 COMPLIANCE: COMPLIANT
SCORE: 9.5

VIOLATIONS:
- Line too long (line 1)

RECOMMENDATIONS:
- Break long lines
- Add blank lines
""",
            "total_tokens": 100,
        }

        with patch.object(agent, "_call_model", return_value=mock_response):
            result = await agent.analyze_pep8_compliance(code)

            assert result["compliant"] is True
            assert result["score"] == 9.5
            assert len(result["violations"]) == 1
            assert len(result["recommendations"]) == 2

    @pytest.mark.asyncio
    async def test_analyze_pep8_compliance_failure(self, agent):
        """Test PEP8 analysis failure fallback."""
        code = "def test_function():\n    return 'hello'"

        with patch.object(
            agent, "_call_model", side_effect=Exception("Analysis failed")
        ):
            result = await agent.analyze_pep8_compliance(code)

            assert result["compliant"] is False
            assert result["score"] == 5.0
            assert "Unable to analyze" in result["violations"][0]

    @pytest.mark.asyncio
    async def test_analyze_test_coverage(self, agent):
        """Test test coverage analysis."""
        function_code = "def add(a, b): return a + b"
        test_code = "def test_add(): assert add(1, 2) == 3"

        mock_response = {
            "response": """
COVERAGE ASSESSMENT: GOOD

COVERED SCENARIOS:
- Normal addition
- Basic functionality

MISSING SCENARIOS:
- Edge cases
- Error conditions

RECOMMENDATIONS:
- Add more test cases
- Test edge cases
""",
            "total_tokens": 100,
        }

        with patch.object(agent, "_call_model", return_value=mock_response):
            result = await agent.analyze_test_coverage(function_code, test_code)

            assert result["coverage"] == "good"
            assert len(result["covered_scenarios"]) == 2
            assert len(result["missing_scenarios"]) == 2
            assert len(result["recommendations"]) == 2

    @pytest.mark.asyncio
    async def test_analyze_test_coverage_failure(self, agent):
        """Test test coverage analysis failure fallback."""
        function_code = "def add(a, b): return a + b"
        test_code = "def test_add(): assert add(1, 2) == 3"

        with patch.object(
            agent, "_call_model", side_effect=Exception("Analysis failed")
        ):
            result = await agent.analyze_test_coverage(function_code, test_code)

            assert result["coverage"] == "unknown"
            assert "Unable to analyze" in result["missing_scenarios"][0]

    def test_calculate_complexity_score_simple(self, agent):
        """Test complexity score calculation for simple code."""
        simple_code = """
def simple_function():
    return 42
"""
        score = agent.calculate_complexity_score(simple_code)
        assert score < 5.0  # Should be low complexity

    def test_calculate_complexity_score_complex(self, agent):
        """Test complexity score calculation for complex code."""
        complex_code = """
def complex_function(data):
    result = []
    for item in data:
        if item > 0:
            try:
                processed = item * 2
                if processed > 100:
                    result.append(processed)
                else:
                    result.append(item)
            except Exception as e:
                print(f"Error: {e}")
    return result
"""
        score = agent.calculate_complexity_score(complex_code)
        assert score > 5.0  # Should be higher complexity

    def test_calculate_complexity_score_with_good_practices(self, agent):
        """Test complexity score with good practices."""
        good_code = """
from typing import List

def process_items(items: List[int]) -> List[int]:
    \"\"\"Process a list of items.\"\"\"
    return [item * 2 for item in items if item > 0]
"""
        score = agent.calculate_complexity_score(good_code)
        assert score < 5.0  # Should be low due to good practices

    def test_get_uptime(self, agent):
        """Test uptime calculation."""
        uptime = agent.get_uptime()
        assert uptime >= 0
        assert isinstance(uptime, float)

    def test_get_average_response_time(self, agent):
        """Test average response time calculation."""
        # Add some mock response times
        agent.stats["response_times"] = [1.5, 2.5, 3.5]
        avg_time = agent.get_average_response_time()
        assert avg_time == 2.5

        # Test with no response times
        agent.stats["response_times"] = []
        avg_time = agent.get_average_response_time()
        assert avg_time == 0.0
