"""Quality metrics value objects."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class QualityScore:
    """
    Immutable quality score value object.

    Attributes:
        score: Quality score from 0 to 1
        metric_name: Name of the metric
        details: Optional additional details
    """

    score: float
    metric_name: str
    details: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate quality score."""
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("Quality score must be between 0 and 1")
        if not self.metric_name:
            raise ValueError("Metric name cannot be empty")

    @property
    def percentage(self) -> float:
        """Convert score to percentage."""
        return self.score * 100

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """
        Check if score meets acceptable threshold.

        Args:
            threshold: Minimum acceptable score

        Returns:
            True if score meets threshold
        """
        return self.score >= threshold


@dataclass(frozen=True)
class Metrics:
    """
    Comprehensive metrics value object.

    Attributes:
        scores: Dictionary of metric names to scores
        overall_score: Overall quality score
        timestamp: Optional timestamp
    """

    scores: Dict[str, float]
    overall_score: float
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate metrics."""
        if not (0.0 <= self.overall_score <= 1.0):
            raise ValueError("Overall score must be between 0 and 1")

        for score in self.scores.values():
            if not (0.0 <= score <= 1.0):
                raise ValueError("All scores must be between 0 and 1")

    def get_score(self, metric_name: str) -> Optional[float]:
        """
        Get score for specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Score value or None if not found
        """
        return self.scores.get(metric_name)
