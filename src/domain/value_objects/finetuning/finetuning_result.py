"""Value objects for fine-tuning results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class FineTuningResult:
    """Result of fine-tuning operation.

    Purpose:
        Stores results and metadata from fine-tuning process for tracking
        and analysis.

    Args:
        task_type: Type of task that was fine-tuned.
        model_name: Base model name.
        fine_tuned_model_path: Path to fine-tuned model.
        training_loss: Final training loss.
        validation_loss: Final validation loss (if validation set used).
        num_samples: Number of training samples.
        num_epochs: Number of epochs completed.
        training_duration_seconds: Total training time in seconds.
        started_at: Training start timestamp.
        completed_at: Training completion timestamp.
        metadata: Additional metadata (checkpoints, metrics, etc.).

    Example:
        >>> result = FineTuningResult(
        ...     task_type="summarization",
        ...     model_name="mistralai/Mistral-7B-Instruct-v0.2",
        ...     fine_tuned_model_path="/models/fine_tuned/summarization",
        ...     training_loss=0.15,
        ...     num_samples=500,
        ...     num_epochs=3,
        ...     training_duration_seconds=3600,
        ...     started_at=datetime.now(timezone.utc),
        ...     completed_at=datetime.now(timezone.utc),
        ... )
    """

    task_type: str
    model_name: str
    fine_tuned_model_path: str
    training_loss: float
    validation_loss: float | None
    num_samples: int
    num_epochs: int
    training_duration_seconds: float
    started_at: datetime
    completed_at: datetime
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate result data."""
        if self.training_loss < 0:
            raise ValueError("training_loss must be >= 0")
        if self.validation_loss is not None and self.validation_loss < 0:
            raise ValueError("validation_loss must be >= 0")
        if self.num_samples < 1:
            raise ValueError("num_samples must be >= 1")
        if self.num_epochs < 1:
            raise ValueError("num_epochs must be >= 1")
        if self.training_duration_seconds < 0:
            raise ValueError("training_duration_seconds must be >= 0")
