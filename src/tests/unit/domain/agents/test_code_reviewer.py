"""Unit tests for code reviewer agent.

Following TDD principles and the Zen of Python.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.agents.base_agent import BaseAgent
from src.domain.agents.code_reviewer import CodeReviewerAgent, ReviewerPrompts
from src.domain.messaging.message_schema import (
    CodeQualityMetrics,
    CodeReviewRequest,
    CodeReviewResponse,
    TaskMetadata,
)


class MockCodeReviewer(BaseAgent):
    """Concrete implementation for testing."""

    def __init__(self, model_client=None):
        """Initialize code reviewer."""
        super().__init__(
            model_name="test_model",
            agent_type="reviewer",
            max_tokens=1200,
            temperature=0.2,
            model_client=model_client,
        )

    async def _prepare_review_prompt(self, request: CodeReviewRequest) -> str:
        """Prepare review prompt."""
        return f"Review code for: {request.task_description}"

    async def _call_model_for_review(self, prompt: str) -> dict:
        """Call model for review."""
        return await self._call_model(prompt=prompt)

    async def _parse_review_response(self, response: dict) -> dict:
        """Parse review response."""
        response_text = response.get("response", "")

        # Mock parsed data
        return {
            "overall_score": 8.5,
            "metrics": {
                "pep8_compliance": True,
                "pep8_score": 8.0,
                "has_docstrings": True,
                "has_type_hints": True,
                "test_coverage": "excellent",
                "complexity_score": 2.0,
            },
            "issues": [],
            "recommendations": [],
        }

    async def _create_quality_metrics(self, review_data: dict) -> CodeQualityMetrics:
        """Create quality metrics."""
        metrics_data = review_data.get("metrics", {})
        return CodeQualityMetrics(
            pep8_compliance=metrics_data.get("pep8_compliance", False),
            pep8_score=metrics_data.get("pep8_score", 5.0),
            has_docstrings=metrics_data.get("has_docstrings", False),
            has_type_hints=metrics_data.get("has_type_hints", False),
            test_coverage=metrics_data.get("test_coverage", "unknown"),
            complexity_score=metrics_data.get("complexity_score", 5.0),
        )

    async def process(self, request: CodeReviewRequest) -> CodeReviewResponse:
        """Process code review request."""
        # Prepare prompt
        prompt = await self._prepare_review_prompt(request)

        # Call model
        response = await self._call_model_for_review(prompt)

        # Parse response
        review_data = await self._parse_review_response(response)

        # Create metrics
        metrics = await self._create_quality_metrics(review_data)

        # Create response
        return CodeReviewResponse(
            code_quality_score=review_data["overall_score"],
            metrics=metrics,
            issues=review_data.get("issues", []),
            recommendations=review_data.get("recommendations", []),
            review_time=datetime.now(),
            tokens_used=response.get("total_tokens", 0),
        )


class MockModelClient:
    """Mock model client for testing."""

    def __init__(self, response_text="Review complete"):
        """Initialize mock client."""
        self.response_text = response_text

    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """Generate mock response."""
        return {
            "response": self.response_text,
            "total_tokens": 150,
        }


@pytest.mark.asyncio
async def test_code_reviewer_initialization():
    """Test code reviewer initialization."""
    reviewer = MockCodeReviewer()

    assert reviewer.model_name == "test_model"
    assert reviewer.agent_type == "reviewer"
    assert reviewer.max_tokens == 1200
    assert reviewer.temperature == 0.2


@pytest.mark.asyncio
async def test_code_reviewer_process_request():
    """Test processing a review request."""
    mock_client = MockModelClient()
    reviewer = MockCodeReviewer(model_client=mock_client)

    request = CodeReviewRequest(
        task_description="Review code",
        generated_code="def hello(): pass",
        tests="def test_hello(): pass",
        metadata=TaskMetadata(),
    )

    response = await reviewer.process(request)

    assert response.code_quality_score == 8.5
    assert len(response.issues) == 0
    assert isinstance(response.metrics, CodeQualityMetrics)


@pytest.mark.asyncio
async def test_code_reviewer_prepare_prompt():
    """Test preparing review prompt."""
    reviewer = MockCodeReviewer()

    request = CodeReviewRequest(
        task_description="Review code",
        generated_code="def hello(): pass",
        tests="",
        metadata=TaskMetadata(),
    )

    prompt = await reviewer._prepare_review_prompt(request)
    assert "Review code for: Review code" in prompt


@pytest.mark.asyncio
async def test_code_reviewer_parse_response():
    """Test parsing review response."""
    reviewer = MockCodeReviewer()

    response = {
        "response": "Overall score: 8.5\nPEP8 compliant",
        "total_tokens": 150,
    }

    review_data = await reviewer._parse_review_response(response)
    assert review_data["overall_score"] == 8.5


@pytest.mark.asyncio
async def test_code_reviewer_create_metrics():
    """Test creating quality metrics."""
    reviewer = MockCodeReviewer()

    review_data = {
        "metrics": {
            "pep8_compliance": True,
            "pep8_score": 8.0,
            "has_docstrings": True,
            "has_type_hints": True,
            "test_coverage": "excellent",
            "complexity_score": 2.0,
        }
    }

    metrics = await reviewer._create_quality_metrics(review_data)
    assert metrics.pep8_compliance is True
    assert metrics.pep8_score == 8.0


@pytest.mark.asyncio
async def test_code_reviewer_error_handling():
    """Test error handling."""

    async def failing_generate(*args, **kwargs):
        raise Exception("Model error")

    client = MagicMock()
    client.generate = AsyncMock(side_effect=failing_generate)

    reviewer = MockCodeReviewer(model_client=client)

    request = CodeReviewRequest(
        task_description="Test",
        generated_code="def hello(): pass",
        tests="",
        metadata=TaskMetadata(),
    )

    with pytest.raises(Exception, match="Model error"):
        await reviewer.process(request)

    assert reviewer.stats["failed_requests"] == 1


@pytest.mark.asyncio
async def test_code_reviewer_stats_tracking():
    """Test stats tracking."""
    mock_client = MockModelClient()
    reviewer = MockCodeReviewer(model_client=mock_client)

    request = CodeReviewRequest(
        task_description="Test",
        generated_code="def hello(): pass",
        tests="",
        metadata=TaskMetadata(),
    )

    await reviewer.process(request)

    assert reviewer.stats["total_requests"] == 1
    assert reviewer.stats["successful_requests"] == 1
    assert reviewer.stats["total_tokens_used"] == 150


@pytest.mark.asyncio
async def test_code_reviewer_review_time():
    """Test that review time is tracked."""
    mock_client = MockModelClient()
    reviewer = MockCodeReviewer(model_client=mock_client)

    request = CodeReviewRequest(
        task_description="Test",
        generated_code="def hello(): pass",
        tests="",
        metadata=TaskMetadata(),
    )

    response = await reviewer.process(request)
    assert isinstance(response.review_time, datetime)


def test_code_reviewer_is_subclass_of_base():
    """Test that code reviewer is a subclass of BaseAgent."""
    assert issubclass(MockCodeReviewer, BaseAgent)


@pytest.mark.asyncio
async def test_code_reviewer_issues_and_recommendations():
    """Test that issues and recommendations are returned."""

    class ReviewerWithIssues(MockCodeReviewer):
        async def _parse_review_response(self, response: dict) -> dict:
            return {
                "overall_score": 7.0,
                "metrics": {
                    "pep8_compliance": False,
                    "pep8_score": 6.0,
                    "has_docstrings": False,
                    "has_type_hints": True,
                    "test_coverage": "good",
                    "complexity_score": 4.0,
                },
                "issues": ["Missing docstrings", "PEP8 violations"],
                "recommendations": [
                    "Add docstrings",
                    "Fix PEP8 issues",
                ],
            }

    mock_client = MockModelClient()
    reviewer = ReviewerWithIssues(model_client=mock_client)

    request = CodeReviewRequest(
        task_description="Test",
        generated_code="def hello(): pass",
        tests="",
        metadata=TaskMetadata(),
    )

    response = await reviewer.process(request)

    assert response.code_quality_score == 7.0
    assert len(response.issues) == 2
    assert len(response.recommendations) == 2


# Tests for real CodeReviewerAgent implementation
@pytest.mark.asyncio
async def test_real_code_reviewer_initialization():
    """Test real CodeReviewerAgent initialization."""
    reviewer = CodeReviewerAgent(
        model_name="test_model",
        max_tokens=2000,
        temperature=0.3,
    )

    assert reviewer.model_name == "test_model"
    assert reviewer.agent_type == "reviewer"
    assert reviewer.max_tokens == 2000
    assert reviewer.temperature == 0.3


@pytest.mark.asyncio
async def test_real_code_reviewer_prepare_review_prompt():
    """Test real CodeReviewerAgent prompt preparation."""
    reviewer = CodeReviewerAgent()

    request = CodeReviewRequest(
        task_description="Review calculator function",
        generated_code="def add(a, b): return a + b",
        tests="def test_add(): assert add(2, 3) == 5",
        metadata=TaskMetadata(),
    )

    prompt = reviewer._prepare_review_prompt(request)

    assert "Review calculator function" in prompt
    assert "def add(a, b):" in prompt
    assert "def test_add():" in prompt
    assert "pep8 compliance" in prompt.lower()


@pytest.mark.asyncio
async def test_code_reviewer_parse_text_response():
    """Test parsing text response."""
    reviewer = CodeReviewerAgent()

    text_response = """
    Overall_score: 7.5
    PEP8_compliance: true
    PEP8_score: 8.0
    Has_docstrings: true
    Has_type_hints: false
    """

    review_data = reviewer._parse_text_response(text_response)

    assert review_data["overall_score"] == 7.5
    assert review_data["metrics"]["pep8_compliance"] is True
    assert review_data["metrics"]["pep8_score"] == 8.0
    assert review_data["metrics"]["has_docstrings"] is True
    assert review_data["metrics"]["has_type_hints"] is False


@pytest.mark.asyncio
async def test_code_reviewer_extract_list_items():
    """Test extracting list items from text."""
    reviewer = CodeReviewerAgent()

    # Test with proper format expected by the regex
    text = """Issues:
- Missing docstrings
- PEP8 violations
- No type hints

Recommendations:
- Add docstrings
- Fix PEP8 issues
"""

    issues = reviewer._extract_list_items(text, "Issues")
    recommendations = reviewer._extract_list_items(text, "Recommendations")

    assert len(issues) == 3
    assert "Missing docstrings" in issues
    assert len(recommendations) == 2
    assert "Add docstrings" in recommendations


@pytest.mark.asyncio
async def test_code_reviewer_calculate_complexity_score_simple():
    """Test complexity score calculation for simple code."""
    reviewer = CodeReviewerAgent()

    simple_code = "def hello(): pass"

    score = reviewer.calculate_complexity_score(simple_code)

    assert 0.0 <= score <= 10.0
    assert score < 3.0  # Simple code should have low complexity


@pytest.mark.asyncio
async def test_code_reviewer_calculate_complexity_score_complex():
    """Test complexity score calculation for complex code."""
    reviewer = CodeReviewerAgent()

    complex_code = """
    def complex_function():
        for i in range(10):
            if i > 5:
                try:
                    while True:
                        if condition:
                            pass
                except:
                    pass
        lambda x: x**2
    """

    score = reviewer.calculate_complexity_score(complex_code)

    assert 0.0 <= score <= 10.0
    assert score > 5.0  # Complex code should have higher complexity


@pytest.mark.asyncio
async def test_code_reviewer_calculate_complexity_score_with_docstrings():
    """Test complexity score with good practices reduces complexity."""
    reviewer = CodeReviewerAgent()

    good_code = '''"""Docstring."""
    from typing import List

    def func(x: int) -> List[int]:
        """Function docstring."""
        return [x]
    '''

    score = reviewer.calculate_complexity_score(good_code)

    # Good practices reduce complexity
    assert score < 3.0


@pytest.mark.asyncio
async def test_reviewer_prompts_get_code_review_prompt():
    """Test ReviewerPrompts.get_code_review_prompt."""
    prompt = ReviewerPrompts.get_code_review_prompt(
        task_description="Test task",
        generated_code="def hello(): pass",
        tests="def test_hello(): pass",
        metadata={},
    )

    assert "Test task" in prompt
    assert "def hello()" in prompt
    assert "def test_hello()" in prompt
    assert "pep8 compliance" in prompt.lower()


@pytest.mark.asyncio
async def test_code_reviewer_call_model():
    """Test model calling functionality."""
    reviewer = CodeReviewerAgent()

    # Create a mock client
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        return_value={
            "response": "Review complete",
            "total_tokens": 100,
        }
    )

    reviewer.model_client = mock_client

    prompt = "Review this code"
    response = await reviewer._call_model_for_review(prompt)

    assert response["response"] == "Review complete"
    assert response["total_tokens"] == 100
    mock_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_code_reviewer_prepare_prompt_without_tests():
    """Test prompt preparation without tests."""
    reviewer = CodeReviewerAgent()

    request = CodeReviewRequest(
        task_description="Review simple code",
        generated_code="def simple(): pass",
        tests="",
        metadata=TaskMetadata(),
    )

    prompt = reviewer._prepare_review_prompt(request)

    assert "simple(): pass" in prompt
    assert "Tests:" not in prompt or len(request.tests) == 0


@pytest.mark.asyncio
async def test_code_reviewer_create_quality_metrics():
    """Test creating quality metrics from review data."""
    reviewer = CodeReviewerAgent()

    review_data = {
        "metrics": {
            "pep8_compliance": True,
            "pep8_score": 9.0,
            "has_docstrings": True,
            "has_type_hints": True,
            "test_coverage": "excellent",
            "complexity_score": 1.5,
        }
    }

    metrics = reviewer._create_quality_metrics(review_data)

    assert metrics.pep8_compliance is True
    assert metrics.pep8_score == 9.0
    assert metrics.has_docstrings is True
    assert metrics.test_coverage == "excellent"
