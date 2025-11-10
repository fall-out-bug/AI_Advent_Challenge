"""Repository for summarization evaluation results."""

from __future__ import annotations

import asyncio
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.value_objects.summarization_evaluation import SummarizationEvaluation
from src.infrastructure.logging import get_logger

logger = get_logger("evaluation_repository")


class SummarizationEvaluationRepository:
    """Repository for summarization evaluations."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize repository."""
        self._db = db
        self._collection = db.summarization_evaluations

    async def save_evaluation(self, evaluation: SummarizationEvaluation) -> str:
        """Save evaluation to MongoDB."""
        doc = {
            "summary_id": evaluation.summary_id,
            "original_text": evaluation.original_text,
            "summary_text": evaluation.summary_text,
            "coverage_score": evaluation.coverage_score,
            "accuracy_score": evaluation.accuracy_score,
            "coherence_score": evaluation.coherence_score,
            "informativeness_score": evaluation.informativeness_score,
            "overall_score": evaluation.overall_score,
            "evaluation_method": evaluation.evaluation_method,
            "evaluator_model": evaluation.evaluator_model,
            "evaluation_prompt": evaluation.evaluation_prompt,
            "raw_response": evaluation.raw_response,
            "summarization_context": evaluation.summarization_context,
            "summary_metadata": evaluation.summary_metadata,
            "evaluated_at": evaluation.evaluated_at,
        }

        result = await self._collection.insert_one(doc)
        evaluation_id = str(result.inserted_id)

        logger.debug(
            f"Saved evaluation: id={evaluation_id}, "
            f"score={evaluation.overall_score:.2f}"
        )

        # Trigger fine-tuning check if enabled (fire-and-forget)
        try:
            from src.infrastructure.config.settings import get_settings
            from src.workers.finetuning_worker import FineTuningWorker

            settings = get_settings()
            if settings.enable_auto_finetuning:
                # Check if threshold reached (async, non-blocking)
                worker = FineTuningWorker()
                asyncio.create_task(worker.check_and_trigger())
        except Exception as e:
            # Don't fail on fine-tuning check errors
            logger.debug(f"Fine-tuning check skipped: {e}")

        return evaluation_id

    async def count_evaluations(self, min_score: float = 0.0) -> int:
        """Count evaluations above minimum score."""
        count = await self._collection.count_documents(
            {"overall_score": {"$gte": min_score}}
        )
        return count

    async def export_fine_tuning_dataset(
        self,
        min_score: float = 0.7,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Export high-quality samples for fine-tuning."""
        cursor = (
            self._collection.find({"overall_score": {"$gte": min_score}})
            .sort("overall_score", -1)
            .limit(limit)
        )

        evaluations = await cursor.to_list(length=limit)

        dataset = []
        for eval_doc in evaluations:
            dataset.append(
                {
                    "prompt": f"Summarize:\n{eval_doc['original_text']}",
                    "completion": eval_doc["summary_text"],
                    "score": eval_doc["overall_score"],
                    "metrics": {
                        "coverage": eval_doc["coverage_score"],
                        "accuracy": eval_doc["accuracy_score"],
                        "coherence": eval_doc["coherence_score"],
                        "informativeness": eval_doc["informativeness_score"],
                    },
                }
            )

        logger.info(
            f"Exported {len(dataset)} samples for fine-tuning "
            f"(min_score={min_score})"
        )

        return dataset

    async def should_trigger_finetuning(
        self, min_score: float, min_samples: int
    ) -> bool:
        """Check if fine-tuning should be triggered.

        Args:
            min_score: Minimum score threshold.
            min_samples: Minimum number of samples required.

        Returns:
            True if fine-tuning should be triggered.
        """
        count = await self.count_evaluations(min_score=min_score)
        return count >= min_samples
