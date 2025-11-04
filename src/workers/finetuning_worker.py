"""Background worker for automatic fine-tuning when threshold reached."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.domain.value_objects.finetuning.finetuning_task import FineTuningTask
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.finetuning.finetuning_service import FineTuningService
from src.infrastructure.logging import get_logger
from src.infrastructure.repositories.summarization_evaluation_repository import (
    SummarizationEvaluationRepository,
)

logger = get_logger("finetuning_worker")


class FineTuningWorker:
    """Worker for automatic fine-tuning.

    Purpose:
        Checks if sufficient high-quality samples are available and triggers
        fine-tuning automatically when threshold is reached.
    """

    def __init__(self) -> None:
        """Initialize worker."""
        self.settings = get_settings()
        self._running = False

    async def check_and_trigger(self) -> bool:
        """Check if fine-tuning should be triggered and execute.

        Purpose:
            Checks evaluation repository for sufficient high-quality samples.
            If threshold reached, exports dataset and starts fine-tuning.

        Returns:
            True if fine-tuning was triggered, False otherwise.
        """
        if not self.settings.enable_auto_finetuning:
            logger.debug("Auto fine-tuning disabled")
            return False

        try:
            db = await get_db()
            repo = SummarizationEvaluationRepository(db)

            # Check if threshold reached
            should_trigger = await repo.should_trigger_finetuning(
                min_score=self.settings.evaluation_min_score_for_dataset,
                min_samples=self.settings.finetuning_min_samples,
            )

            if not should_trigger:
                count = await repo.count_evaluations(
                    min_score=self.settings.evaluation_min_score_for_dataset
                )
                logger.debug(
                    f"Fine-tuning threshold not reached: {count}/"
                    f"{self.settings.finetuning_min_samples} samples"
                )
                return False

            logger.info("Fine-tuning threshold reached, starting fine-tuning...")

            # Export dataset
            dataset = await repo.export_fine_tuning_dataset(
                min_score=self.settings.evaluation_min_score_for_dataset,
                limit=1000,  # Use all available high-quality samples
            )

            if not dataset:
                logger.warning("No samples exported for fine-tuning")
                return False

            # Save dataset to file
            dataset_path = Path("data/fine_tuning_dataset.jsonl")
            dataset_path.parent.mkdir(parents=True, exist_ok=True)

            import json

            with open(dataset_path, "w", encoding="utf-8") as f:
                for sample in dataset:
                    f.write(json.dumps(sample, ensure_ascii=False) + "\n")

            logger.info(f"Exported {len(dataset)} samples to {dataset_path}")

            # Create fine-tuning task
            output_dir = Path(self.settings.finetuning_model_output_dir) / "summarization"
            output_dir.mkdir(parents=True, exist_ok=True)

            task = FineTuningTask(
                task_type="summarization",
                model_name=self.settings.finetuning_base_model,
                dataset_path=str(dataset_path),
                output_dir=str(output_dir),
                num_epochs=self.settings.finetuning_num_epochs,
                batch_size=self.settings.finetuning_batch_size,
                learning_rate=self.settings.finetuning_learning_rate,
            )

            # Run fine-tuning (in background to not block)
            asyncio.create_task(self._run_finetuning(task))

            return True

        except Exception as e:
            logger.error(f"Error checking/triggering fine-tuning: {e}", exc_info=True)
            return False

    async def _run_finetuning(self, task: FineTuningTask) -> None:
        """Run fine-tuning in background.

        Args:
            task: Fine-tuning task configuration.
        """
        try:
            service = FineTuningService(
                output_base_dir=self.settings.finetuning_model_output_dir
            )
            result = await service.fine_tune(task)

            logger.info(
                f"Fine-tuning completed: loss={result.training_loss:.4f}, "
                f"duration={result.training_duration_seconds:.1f}s, "
                f"model_path={result.fine_tuned_model_path}"
            )
        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}", exc_info=True)
