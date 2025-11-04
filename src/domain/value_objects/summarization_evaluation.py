"""Value objects for summarization evaluation results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class SummarizationEvaluation:
    """Quality evaluation of a summary.

    Purpose:
        Represents the evaluation result of a summarization operation,
        including quality metrics and metadata for fine-tuning dataset creation.

    Args:
        summary_id: Unique ID for this summary.
        original_text: Source text that was summarized.
        summary_text: Generated summary text.
        coverage_score: Completeness score - covers all key topics (0.0-1.0).
        accuracy_score: Truthfulness score - no hallucinations (0.0-1.0).
        coherence_score: Readability and logical flow score (0.0-1.0).
        informativeness_score: Information density score (0.0-1.0).
        overall_score: Weighted average quality score (0.0-1.0).
        evaluation_method: Method used for evaluation (e.g., "llm_judge").
        evaluator_model: Model used for evaluation.
        evaluation_prompt: Prompt used for evaluation.
        raw_response: LLM's raw response before parsing.
        summarization_context: SummarizationContext as dictionary.
        summary_metadata: SummaryResult.metadata dictionary.
        evaluated_at: Timestamp when evaluation was performed.

    Example:
        >>> evaluation = SummarizationEvaluation(
        ...     summary_id="eval_123",
        ...     original_text="Long text...",
        ...     summary_text="Summary...",
        ...     coverage_score=0.85,
        ...     accuracy_score=0.95,
        ...     coherence_score=0.90,
        ...     informativeness_score=0.80,
        ...     overall_score=0.87,
        ...     evaluation_method="llm_judge",
        ...     evaluator_model="mistralai/Mistral-7B-Instruct-v0.2",
        ...     evaluation_prompt="Evaluate...",
        ...     raw_response='{"coverage": 0.85, ...}',
        ...     summarization_context={},
        ...     summary_metadata={},
        ...     evaluated_at=datetime.now(timezone.utc),
        ... )
        >>> sample = evaluation.to_fine_tuning_sample()
    """

    summary_id: str
    original_text: str
    summary_text: str
    coverage_score: float
    accuracy_score: float
    coherence_score: float
    informativeness_score: float
    overall_score: float
    evaluation_method: str
    evaluator_model: str
    evaluation_prompt: str
    raw_response: str
    summarization_context: dict[str, Any]
    summary_metadata: dict[str, Any]
    evaluated_at: datetime

    def __post_init__(self) -> None:
        """Validate evaluation data."""
        if not self.summary_id:
            raise ValueError("summary_id cannot be empty")
        if not self.original_text:
            raise ValueError("original_text cannot be empty")
        if not self.summary_text:
            raise ValueError("summary_text cannot be empty")
        
        # Validate scores are in range [0.0, 1.0]
        for score_name, score_value in [
            ("coverage_score", self.coverage_score),
            ("accuracy_score", self.accuracy_score),
            ("coherence_score", self.coherence_score),
            ("informativeness_score", self.informativeness_score),
            ("overall_score", self.overall_score),
        ]:
            if not 0.0 <= score_value <= 1.0:
                raise ValueError(
                    f"{score_name} must be between 0.0 and 1.0, got {score_value}"
                )
        
        if not self.evaluation_method:
            raise ValueError("evaluation_method cannot be empty")
        if not self.evaluator_model:
            raise ValueError("evaluator_model cannot be empty")

    def to_fine_tuning_sample(self) -> dict[str, Any]:
        """Convert to fine-tuning dataset format.

        Purpose:
            Convert evaluation to format suitable for fine-tuning,
            typically used with Hugging Face Transformers or similar frameworks.

        Returns:
            Dictionary with prompt, completion, score, and metrics.

        Example:
            >>> sample = evaluation.to_fine_tuning_sample()
            >>> sample["prompt"]
            'Summarize:\\nOriginal text...'
            >>> sample["completion"]
            'Summary text...'
            >>> sample["score"]
            0.87
        """
        return {
            "prompt": f"Summarize:\n{self.original_text}",
            "completion": self.summary_text,
            "score": self.overall_score,
            "metrics": {
                "coverage": self.coverage_score,
                "accuracy": self.accuracy_score,
                "coherence": self.coherence_score,
                "informativeness": self.informativeness_score,
            },
        }
