"""Service for fine-tuning LLM models using Hugging Face Transformers."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.domain.value_objects.finetuning.finetuning_result import (
    FineTuningResult,
)
from src.domain.value_objects.finetuning.finetuning_task import FineTuningTask
from src.infrastructure.logging import get_logger

logger = get_logger("finetuning_service")

# Try to import transformers, fail gracefully if not available
try:
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
        DataCollatorForLanguageModeling,
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning(
        "Hugging Face Transformers not available. "
        "Install with: pip install transformers datasets torch"
    )


class FineTuningService:
    """Service for fine-tuning LLM models.

    Purpose:
        Provides full fine-tuning of Mistral and other models using
        Hugging Face Transformers. Supports extensible task types.
    """

    def __init__(self, output_base_dir: str = "/models/fine_tuned") -> None:
        """Initialize fine-tuning service.

        Args:
            output_base_dir: Base directory for storing fine-tuned models.
        """
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "Hugging Face Transformers not installed. "
                "Required for fine-tuning."
            )

        self._output_base_dir = Path(output_base_dir)
        self._output_base_dir.mkdir(parents=True, exist_ok=True)

    async def fine_tune(self, task: FineTuningTask) -> FineTuningResult:
        """Fine-tune model using full fine-tuning.

        Purpose:
            Performs full fine-tuning (not LoRA) of the specified model
            on the provided dataset.

        Args:
            task: Fine-tuning task configuration.

        Returns:
            FineTuningResult with training metrics and model path.

        Raises:
            RuntimeError: If Transformers not available or training fails.
        """
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Hugging Face Transformers not available")

        logger.info(
            f"Starting fine-tuning: task_type={task.task_type}, "
            f"model={task.model_name}, samples={self._count_samples(task.dataset_path)}"
        )

        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        try:
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(task.model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            model = AutoModelForCausalLM.from_pretrained(
                task.model_name,
                device_map="auto",
                torch_dtype="float16",
            )

            # Load dataset
            dataset = load_dataset("json", data_files=task.dataset_path, split="train")
            num_samples = len(dataset)

            # Format dataset for training
            def format_prompts(examples):
                """Format prompts for Mistral instruct format."""
                prompts = []
                for prompt, completion in zip(examples["prompt"], examples["completion"]):
                    formatted = f"<s>[INST] {prompt} [/INST] {completion} </s>"
                    prompts.append(formatted)
                return {"text": prompts}

            dataset = dataset.map(format_prompts, batched=True)

            # Tokenize
            def tokenize_function(examples):
                return tokenizer(
                    examples["text"],
                    truncation=True,
                    padding=True,
                    max_length=2048,
                )

            tokenized_dataset = dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=dataset.column_names,
            )

            # Set up training arguments
            output_dir = Path(task.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            training_args = TrainingArguments(
                output_dir=str(output_dir),
                num_train_epochs=task.num_epochs,
                per_device_train_batch_size=task.batch_size,
                learning_rate=task.learning_rate,
                fp16=True,
                save_strategy="epoch",
                logging_steps=10,
                max_steps=task.max_steps,
                remove_unused_columns=False,
            )

            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer, mlm=False
            )

            # Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
            )

            # Train
            train_result = trainer.train()

            # Save final model
            trainer.save_model()
            tokenizer.save_pretrained(output_dir)

            completed_at = datetime.now(timezone.utc)
            duration = time.time() - start_time

            result = FineTuningResult(
                task_type=task.task_type,
                model_name=task.model_name,
                fine_tuned_model_path=str(output_dir),
                training_loss=float(train_result.training_loss),
                validation_loss=None,  # Can add validation split later
                num_samples=num_samples,
                num_epochs=task.num_epochs,
                training_duration_seconds=duration,
                started_at=started_at,
                completed_at=completed_at,
                metadata={
                    "log_history": train_result.log_history,
                    "global_step": train_result.global_step,
                },
            )

            logger.info(
                f"Fine-tuning completed: loss={result.training_loss:.4f}, "
                f"duration={duration:.1f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}", exc_info=True)
            raise RuntimeError(f"Fine-tuning failed: {e}") from e

    def _count_samples(self, dataset_path: str) -> int:
        """Count samples in JSONL dataset."""
        count = 0
        with open(dataset_path, "r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return count
