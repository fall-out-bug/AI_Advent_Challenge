"""Unit tests for Day 5 model comparison example."""

from __future__ import annotations

import time
from unittest.mock import Mock, patch

from examples.day05_model_comparison import (
    ModelComparisonAgent,
    ModelResult,
    MODEL_PRICING,
)


def test_agent_tests_model_with_metrics() -> None:
    """Test that agent measures response time, tokens, and cost."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Test response from gpt-3.5-turbo",
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    }

    agent = ModelComparisonAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        result = agent.test_model("Test prompt", "gpt-3.5-turbo")

        assert result.model == "gpt-3.5-turbo"
        assert "gpt-3.5-turbo" in result.response
        assert result.tokens_prompt == 10
        assert result.tokens_completion == 20
        assert result.tokens_total == 30
        assert result.response_time_ms > 0
        assert result.cost_usd >= 0.0
        assert 0.0 <= result.quality_score <= 1.0

    agent.close()


def test_agent_calculates_cost_correctly() -> None:
    """Test that agent calculates cost based on model pricing."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Response",
                }
            }
        ],
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
        },
    }

    agent = ModelComparisonAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        # Test paid model
        result_gpt4 = agent.test_model("Test", "gpt-4")
        expected_cost = (
            1000 * MODEL_PRICING["gpt-4"]["prompt"]
            + 500 * MODEL_PRICING["gpt-4"]["completion"]
        )
        assert abs(result_gpt4.cost_usd - expected_cost) < 0.000001

        # Test free model
        result_free = agent.test_model("Test", "mistral-7b-instruct")
        assert result_free.cost_usd == 0.0

    agent.close()


def test_agent_compares_multiple_models() -> None:
    """Test that agent runs prompt with multiple models."""
    def mock_post_side_effect(*args: any, **kwargs: any) -> Mock:
        model = kwargs.get("json", {}).get("model", "unknown")
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": f"Response from {model}",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15,
            },
        }
        return mock_resp

    agent = ModelComparisonAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", side_effect=mock_post_side_effect):
        models = ["gpt-3.5-turbo", "gpt-4", "mistral-7b-instruct"]
        results = agent.compare_models("Test", models)

        assert len(results) == 3
        assert {r.model for r in results} == set(models)

        # Verify all results have metrics
        for result in results:
            assert result.response_time_ms > 0
            assert result.tokens_total > 0
            assert 0.0 <= result.quality_score <= 1.0

    agent.close()


def test_model_result_dataclass() -> None:
    """Test ModelResult dataclass structure."""
    result = ModelResult(
        model="test-model",
        response="Test response",
        response_time_ms=100.5,
        tokens_prompt=10,
        tokens_completion=20,
        tokens_total=30,
        cost_usd=0.001,
        quality_score=0.75,
    )

    assert result.model == "test-model"
    assert result.response == "Test response"
    assert result.response_time_ms == 100.5
    assert result.tokens_prompt == 10
    assert result.tokens_completion == 20
    assert result.tokens_total == 30
    assert result.cost_usd == 0.001
    assert result.quality_score == 0.75


def test_quality_score_calculation() -> None:
    """Test that quality score is calculated from response length."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    # Long response (should have high quality score)
    long_content = " ".join(["word"] * 150)  # 150 words
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": long_content,
                }
            }
        ],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 10,
            "total_tokens": 15,
        },
    }

    agent = ModelComparisonAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        result = agent.test_model("Test", "gpt-4")

        # 150 words should give quality_score = min(1.0, 150/100) = 1.0
        assert result.quality_score == 1.0

    agent.close()
