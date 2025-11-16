"""Unit tests for Day 7 agent interaction example."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

from examples.day07_agent_interaction import (
    AgentOrchestrator,
    ReviewerAgent,
    ReviewResult,
    TaskAgent,
    TaskResult,
)


def test_task_agent_executes_task() -> None:
    """Test that TaskAgent executes a task and produces output."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
                }
            }
        ],
        "usage": {"total_tokens": 50},
        "model": "gpt-4",
    }

    agent = TaskAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        result = agent.execute_task("Write a function to calculate factorial")

        assert result.task == "Write a function to calculate factorial"
        assert "factorial" in result.output
        assert result.status == "success"
        assert result.metadata["tokens_used"] == 50

    agent.close()


def test_task_agent_formats_for_review() -> None:
    """Test that TaskAgent formats result for reviewer."""
    result = TaskResult(
        task="test task",
        output="test output",
        status="success",
        metadata={"tokens_used": 30},
    )

    agent = TaskAgent(llm_url="http://mock")

    formatted = agent.format_for_review(result)

    assert "test task" in formatted
    assert "test output" in formatted
    assert "success" in formatted
    assert "30" in formatted

    agent.close()


def test_reviewer_agent_reviews_result() -> None:
    """Test that ReviewerAgent reviews task result."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "score": 0.9,
                        "issues": ["Minor: add docstring"],
                        "approval": True,
                        "feedback": "Good implementation",
                    }),
                }
            }
        ]
    }

    task_result = TaskResult(
        task="test task",
        output="test output",
        status="success",
        metadata={},
    )

    agent = ReviewerAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        review = agent.review(task_result, "Task Result: test output")

        assert review.review_score == 0.9
        assert len(review.issues) == 1
        assert review.approval is True

    agent.close()


def test_orchestrator_executes_and_reviews() -> None:
    """Test that AgentOrchestrator coordinates both agents."""
    task_response = Mock()
    task_response.raise_for_status = Mock()
    task_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "def add(a, b): return a + b",
                }
            }
        ],
        "usage": {"total_tokens": 20},
        "model": "gpt-4",
    }

    review_response = Mock()
    review_response.raise_for_status = Mock()
    review_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "score": 0.8,
                        "issues": [],
                        "approval": True,
                        "feedback": "Good",
                    }),
                }
            }
        ]
    }

    task_agent = TaskAgent(llm_url="http://mock")
    reviewer_agent = ReviewerAgent(llm_url="http://mock")

    with patch.object(task_agent._client, "post", return_value=task_response), \
         patch.object(reviewer_agent._client, "post", return_value=review_response):

        orchestrator = AgentOrchestrator(task_agent, reviewer_agent)
        task_result, review_result = orchestrator.execute_and_review("Write add function")

        assert task_result.task == "Write add function"
        assert "add" in task_result.output
        assert review_result.review_score == 0.8
        assert review_result.approval is True

    task_agent.close()
    reviewer_agent.close()


def test_task_result_dataclass() -> None:
    """Test TaskResult dataclass structure."""
    result = TaskResult(
        task="test",
        output="output",
        status="success",
        metadata={"key": "value"},
    )

    assert result.task == "test"
    assert result.output == "output"
    assert result.status == "success"
    assert result.metadata == {"key": "value"}


def test_review_result_dataclass() -> None:
    """Test ReviewResult dataclass structure."""
    task_result = TaskResult(
        task="test",
        output="output",
        status="success",
        metadata={},
    )

    review = ReviewResult(
        task_result=task_result,
        review_score=0.75,
        issues=["issue1"],
        approval=True,
    )

    assert review.task_result == task_result
    assert review.review_score == 0.75
    assert review.issues == ["issue1"]
    assert review.approval is True
