"""Unit tests for SummarizationEvaluator."""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.value_objects.summarization_context import SummarizationContext
from src.infrastructure.llm.evaluation.summarization_evaluator import (
    SummarizationEvaluator,
)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = AsyncMock()
    client.generate = AsyncMock(
        return_value=json.dumps(
            {
                "coverage": 0.85,
                "accuracy": 0.95,
                "coherence": 0.90,
                "informativeness": 0.80,
                "overall": 0.87,
                "explanation": "Good summary",
            }
        )
    )
    return client


@pytest.fixture
def mock_token_counter():
    """Mock token counter."""
    counter = MagicMock()
    counter.count_tokens = MagicMock(return_value=100)
    return counter


@pytest.fixture
def evaluator(mock_llm_client, mock_token_counter):
    """Create evaluator instance."""
    return SummarizationEvaluator(
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
    )


@pytest.fixture
def context():
    """Create summarization context."""
    return SummarizationContext(
        time_period_hours=24,
        source_type="telegram_posts",
        language="ru",
        max_sentences=8,
    )


@pytest.mark.asyncio
async def test_evaluate_parses_scores_correctly(evaluator, context, mock_llm_client):
    """Test that evaluation correctly parses scores from LLM response."""
    original_text = "This is a long original text with multiple sentences."
    summary_text = "This is a summary."

    result = await evaluator.evaluate(
        original_text=original_text,
        summary_text=summary_text,
        context=context,
        summary_metadata={},
    )

    assert result.coverage_score == 0.85
    assert result.accuracy_score == 0.95
    assert result.coherence_score == 0.90
    assert result.informativeness_score == 0.80
    assert result.overall_score == 0.87
    assert result.evaluation_method == "llm_judge"
    assert result.summary_id.startswith("eval_")


@pytest.mark.asyncio
async def test_evaluate_handles_malformed_json(evaluator, context, mock_llm_client):
    """Test error handling for malformed JSON response."""
    mock_llm_client.generate = AsyncMock(return_value="Not valid JSON")

    with pytest.raises(ValueError, match="Invalid JSON"):
        await evaluator.evaluate(
            original_text="Original text",
            summary_text="Summary",
            context=context,
            summary_metadata={},
        )


@pytest.mark.asyncio
async def test_evaluate_handles_missing_scores(evaluator, context, mock_llm_client):
    """Test error handling for missing required scores."""
    mock_llm_client.generate = AsyncMock(
        return_value=json.dumps({"coverage": 0.85})  # Missing other scores
    )

    with pytest.raises(ValueError, match="Missing required scores"):
        await evaluator.evaluate(
            original_text="Original text",
            summary_text="Summary",
            context=context,
            summary_metadata={},
        )


@pytest.mark.asyncio
async def test_evaluate_truncates_long_text(evaluator, context, mock_token_counter):
    """Test that long text is truncated for evaluation."""
    # Create long text
    long_text = "Sentence. " * 1000  # Very long text

    # Mock token counter to return high token count
    mock_token_counter.count_tokens = MagicMock(return_value=5000)

    with patch(
        "src.infrastructure.llm.evaluation.summarization_evaluator.get_evaluation_prompt"
    ) as mock_prompt:
        mock_prompt.return_value = "Prompt"

        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            return_value=json.dumps(
                {
                    "coverage": 0.8,
                    "accuracy": 0.9,
                    "coherence": 0.85,
                    "informativeness": 0.75,
                    "overall": 0.82,
                }
            )
        )

        evaluator._llm_client = mock_llm

        await evaluator.evaluate(
            original_text=long_text,
            summary_text="Summary",
            context=context,
            summary_metadata={},
        )

        # Verify truncation happened (text passed to prompt is shorter)
        call_args = mock_prompt.call_args
        truncated_text = call_args[1]["original_text"]
        assert len(truncated_text) < len(long_text)
