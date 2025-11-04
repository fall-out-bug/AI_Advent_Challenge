"""Value objects for fine-tuning tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FineTuningTask:
    """Configuration for fine-tuning task.

    Purpose:
        Extensible configuration object that supports different task types
        (summarization, classification, etc.) for fine-tuning LLM models.

    Args:
        task_type: Type of task ("summarization" | "classification" | "qa" | etc.).
        model_name: Base model to fine-tune (e.g., "mistralai/Mistral-7B-Instruct-v0.2").
        dataset_path: Path to training dataset (JSONL format).
        output_dir: Directory to save fine-tuned model.
        num_epochs: Number of training epochs.
        batch_size: Training batch size.
        learning_rate: Learning rate for training.
        max_steps: Maximum training steps (None = use epochs).
        task_specific_config: Additional task-specific configuration.

    Example:
        >>> task = FineTuningTask(
        ...     task_type="summarization",
        ...     model_name="mistralai/Mistral-7B-Instruct-v0.2",
        ...     dataset_path="data/fine_tuning_dataset.jsonl",
        ...     output_dir="/models/fine_tuned/summarization",
        ...     num_epochs=3,
        ...     batch_size=4,
        ...     learning_rate=2e-5,
        ... )
    """

    task_type: str
    model_name: str
    dataset_path: str
    output_dir: str
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-5
    max_steps: int | None = None
    task_specific_config: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate task configuration."""
        valid_task_types = ("summarization", "classification", "qa", "custom")
        if self.task_type not in valid_task_types:
            raise ValueError(
                f"Invalid task_type: {self.task_type}. "
                f"Must be one of {valid_task_types}"
            )
        if self.num_epochs < 1:
            raise ValueError("num_epochs must be >= 1")
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be > 0")
