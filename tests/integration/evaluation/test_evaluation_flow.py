"""Integration tests for evaluation flow."""

import pytest
from datetime import datetime, timezone, timedelta
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summarization_evaluation import SummarizationEvaluation
from src.infrastructure.repositories.summarization_evaluation_repository import (
    SummarizationEvaluationRepository,
)


@pytest.mark.asyncio
async def test_save_and_export_evaluation(real_mongodb):
    """Test saving evaluation and exporting dataset."""
    repo = SummarizationEvaluationRepository(real_mongodb)

    # Create evaluation
    evaluation = SummarizationEvaluation(
        summary_id="test_eval_123",
        original_text="Original long text here",
        summary_text="Summary here",
        coverage_score=0.85,
        accuracy_score=0.95,
        coherence_score=0.90,
        informativeness_score=0.80,
        overall_score=0.87,
        evaluation_method="llm_judge",
        evaluator_model="mistralai/Mistral-7B-Instruct-v0.2",
        evaluation_prompt="Evaluate...",
        raw_response='{"coverage": 0.85}',
        summarization_context={},
        summary_metadata={},
        evaluated_at=datetime.now(timezone.utc),
    )

    # Save
    eval_id = await repo.save_evaluation(evaluation)
    assert eval_id is not None

    # Count
    count = await repo.count_evaluations(min_score=0.7)
    assert count >= 1

    # Export
    dataset = await repo.export_fine_tuning_dataset(min_score=0.7, limit=10)
    assert len(dataset) >= 1
    assert dataset[0]["score"] == 0.87
    assert "prompt" in dataset[0]
    assert "completion" in dataset[0]


@pytest.mark.asyncio
async def test_should_trigger_finetuning(real_mongodb):
    """Test fine-tuning trigger logic."""
    repo = SummarizationEvaluationRepository(real_mongodb)

    # Create multiple high-quality evaluations
    for i in range(5):
        evaluation = SummarizationEvaluation(
            summary_id=f"test_eval_{i}",
            original_text=f"Original text {i}",
            summary_text=f"Summary {i}",
            coverage_score=0.85,
            accuracy_score=0.95,
            coherence_score=0.90,
            informativeness_score=0.80,
            overall_score=0.87,
            evaluation_method="llm_judge",
            evaluator_model="mistralai/Mistral-7B-Instruct-v0.2",
            evaluation_prompt="Evaluate...",
            raw_response="{}",
            summarization_context={},
            summary_metadata={},
            evaluated_at=datetime.now(timezone.utc),
        )
        await repo.save_evaluation(evaluation)

    # Check trigger with min_samples=3 (should trigger)
    should_trigger = await repo.should_trigger_finetuning(
        min_score=0.7, min_samples=3
    )
    assert should_trigger is True

    # Check trigger with min_samples=10 (should not trigger)
    should_trigger = await repo.should_trigger_finetuning(
        min_score=0.7, min_samples=10
    )
    assert should_trigger is False
