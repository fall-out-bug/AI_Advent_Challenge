"""
Domain entities for the token analysis system.

This module contains the core business entities that represent the fundamental
concepts in the token analysis domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


@dataclass
class TokenAnalysisDomain:
    """
    Core domain entity representing a token analysis operation.

    This entity encapsulates the business logic and rules around token analysis,
    including validation, calculation, and state management.
    """

    # Identity
    analysis_id: str
    created_at: datetime = field(default_factory=datetime.now)

    # Core data
    input_text: str
    model_name: str
    model_version: str

    # Analysis results
    token_count: Optional[int] = None
    compression_ratio: Optional[float] = None
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None

    # Status and metadata
    status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start_processing(self) -> None:
        """Mark analysis as processing."""
        if self.status != "pending":
            raise ValueError(f"Cannot start processing from status: {self.status}")
        self.status = "processing"

    def complete_analysis(
        self,
        token_count: int,
        compression_ratio: float,
        processing_time: float,
        confidence_score: float,
    ) -> None:
        """
        Complete the analysis with results.

        Args:
            token_count: Number of tokens in the input
            compression_ratio: Compression ratio achieved
            processing_time: Time taken for processing
            confidence_score: Confidence in the analysis
        """
        if self.status != "processing":
            raise ValueError(f"Cannot complete analysis from status: {self.status}")

        self.token_count = token_count
        self.compression_ratio = compression_ratio
        self.processing_time = processing_time
        self.confidence_score = confidence_score
        self.status = "completed"

    def fail_analysis(self, error_message: str) -> None:
        """
        Mark analysis as failed.

        Args:
            error_message: Error message describing the failure
        """
        self.status = "failed"
        self.error_message = error_message

    def is_completed(self) -> bool:
        """Check if analysis is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if analysis has failed."""
        return self.status == "failed"

    def get_quality_score(self) -> float:
        """
        Calculate quality score based on analysis results.

        Returns:
            float: Quality score between 0 and 1
        """
        if not self.is_completed():
            return 0.0

        # Quality factors
        confidence_factor = self.confidence_score or 0.0
        compression_factor = min(1.0, self.compression_ratio or 1.0)
        time_factor = max(
            0.0, 1.0 - (self.processing_time or 0.0) / 10.0
        )  # Penalize slow processing

        return (confidence_factor + compression_factor + time_factor) / 3.0

    def validate(self) -> List[str]:
        """
        Validate the analysis entity.

        Returns:
            List[str]: List of validation errors
        """
        errors = []

        if not self.input_text.strip():
            errors.append("Input text cannot be empty")

        if not self.model_name.strip():
            errors.append("Model name cannot be empty")

        if not self.model_version.strip():
            errors.append("Model version cannot be empty")

        if self.is_completed():
            if self.token_count is None or self.token_count < 0:
                errors.append("Token count must be non-negative")

            if self.compression_ratio is None or not (
                0.0 <= self.compression_ratio <= 1.0
            ):
                errors.append("Compression ratio must be between 0 and 1")

            if self.processing_time is None or self.processing_time < 0:
                errors.append("Processing time must be non-negative")

            if self.confidence_score is None or not (
                0.0 <= self.confidence_score <= 1.0
            ):
                errors.append("Confidence score must be between 0 and 1")

        return errors


@dataclass
class CompressionJob:
    """
    Domain entity representing a compression job.

    This entity manages the lifecycle and business rules of text compression
    operations within the token analysis system.
    """

    # Identity
    job_id: str
    created_at: datetime = field(default_factory=datetime.now)

    # Job data
    original_text: str
    target_compression_ratio: float
    compression_strategy: str

    # Job state
    status: str = "queued"  # queued, processing, completed, failed
    priority: int = 1  # 1=low, 2=medium, 3=high

    # Results
    compressed_text: Optional[str] = None
    actual_compression_ratio: Optional[float] = None
    processing_time: Optional[float] = None
    quality_score: Optional[float] = None

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def start_processing(self) -> None:
        """Start processing the compression job."""
        if self.status != "queued":
            raise ValueError(f"Cannot start processing from status: {self.status}")
        self.status = "processing"

    def complete_compression(
        self,
        compressed_text: str,
        actual_ratio: float,
        processing_time: float,
        quality_score: float,
    ) -> None:
        """
        Complete the compression job.

        Args:
            compressed_text: The compressed text result
            actual_ratio: Actual compression ratio achieved
            processing_time: Time taken for compression
            quality_score: Quality score of the compression
        """
        if self.status != "processing":
            raise ValueError(f"Cannot complete compression from status: {self.status}")

        self.compressed_text = compressed_text
        self.actual_compression_ratio = actual_ratio
        self.processing_time = processing_time
        self.quality_score = quality_score
        self.status = "completed"

    def fail_compression(self, error_message: str) -> None:
        """
        Mark compression as failed.

        Args:
            error_message: Error message describing the failure
        """
        self.status = "failed"
        self.error_message = error_message
        self.retry_count += 1

    def can_retry(self) -> bool:
        """Check if the job can be retried."""
        return self.status == "failed" and self.retry_count < self.max_retries

    def retry(self) -> None:
        """Retry the compression job."""
        if not self.can_retry():
            raise ValueError("Job cannot be retried")

        self.status = "queued"
        self.error_message = None

    def is_completed(self) -> bool:
        """Check if compression is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if compression has failed."""
        return self.status == "failed"

    def get_compression_efficiency(self) -> float:
        """
        Calculate compression efficiency.

        Returns:
            float: Efficiency score between 0 and 1
        """
        if not self.is_completed():
            return 0.0

        # Efficiency based on how close we got to target ratio
        if self.target_compression_ratio == 0:
            return 1.0 if self.actual_compression_ratio == 0 else 0.0

        ratio_diff = abs(self.actual_compression_ratio - self.target_compression_ratio)
        efficiency = max(0.0, 1.0 - ratio_diff / self.target_compression_ratio)

        return efficiency

    def validate(self) -> List[str]:
        """
        Validate the compression job.

        Returns:
            List[str]: List of validation errors
        """
        errors = []

        if not self.original_text.strip():
            errors.append("Original text cannot be empty")

        if not (0.0 <= self.target_compression_ratio <= 1.0):
            errors.append("Target compression ratio must be between 0 and 1")

        if not self.compression_strategy.strip():
            errors.append("Compression strategy cannot be empty")

        if not (1 <= self.priority <= 3):
            errors.append("Priority must be between 1 and 3")

        if self.is_completed():
            if not self.compressed_text:
                errors.append("Compressed text is required for completed jobs")

            if self.actual_compression_ratio is None or not (
                0.0 <= self.actual_compression_ratio <= 1.0
            ):
                errors.append("Actual compression ratio must be between 0 and 1")

            if self.processing_time is None or self.processing_time < 0:
                errors.append("Processing time must be non-negative")

        return errors


class ExperimentSession:
    """
    Domain entity representing an experiment session.

    This entity manages the lifecycle of ML experiments, including configuration,
    execution, and result collection.
    """

    def __init__(
        self,
        session_id: str,
        experiment_name: str,
        model_name: str,
        configuration: Dict[str, Any],
    ):
        """
        Initialize experiment session.

        Args:
            session_id: Unique session identifier
            experiment_name: Name of the experiment
            model_name: Name of the model being tested
            configuration: Experiment configuration
        """
        self.session_id = session_id
        self.experiment_name = experiment_name
        self.model_name = model_name
        self.configuration = configuration

        self.created_at = datetime.now()
        self.status = "created"  # created, running, completed, failed
        self.results: List[TokenAnalysisDomain] = []
        self.metrics: Dict[str, Any] = {}

        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None

    def start_experiment(self) -> None:
        """Start the experiment session."""
        if self.status != "created":
            raise ValueError(f"Cannot start experiment from status: {self.status}")

        self.status = "running"
        self.started_at = datetime.now()

    def add_result(self, analysis: TokenAnalysisDomain) -> None:
        """
        Add an analysis result to the session.

        Args:
            analysis: Token analysis result
        """
        if self.status != "running":
            raise ValueError(
                f"Cannot add results to session with status: {self.status}"
            )

        self.results.append(analysis)

    def complete_experiment(self, metrics: Dict[str, Any]) -> None:
        """
        Complete the experiment session.

        Args:
            metrics: Final experiment metrics
        """
        if self.status != "running":
            raise ValueError(f"Cannot complete experiment from status: {self.status}")

        self.status = "completed"
        self.completed_at = datetime.now()
        self.metrics = metrics

    def fail_experiment(self, error_message: str) -> None:
        """
        Mark experiment as failed.

        Args:
            error_message: Error message describing the failure
        """
        self.status = "failed"
        self.completed_at = datetime.now()
        self.error_message = error_message

    def get_success_rate(self) -> float:
        """
        Calculate success rate of the experiment.

        Returns:
            float: Success rate between 0 and 1
        """
        if not self.results:
            return 0.0

        successful_results = [r for r in self.results if r.is_completed()]
        return len(successful_results) / len(self.results)

    def get_average_quality_score(self) -> float:
        """
        Calculate average quality score of completed analyses.

        Returns:
            float: Average quality score
        """
        completed_results = [r for r in self.results if r.is_completed()]
        if not completed_results:
            return 0.0

        total_score = sum(r.get_quality_score() for r in completed_results)
        return total_score / len(completed_results)

    def is_completed(self) -> bool:
        """Check if experiment is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if experiment has failed."""
        return self.status == "failed"

    def validate(self) -> List[str]:
        """
        Validate the experiment session.

        Returns:
            List[str]: List of validation errors
        """
        errors = []

        if not self.experiment_name.strip():
            errors.append("Experiment name cannot be empty")

        if not self.model_name.strip():
            errors.append("Model name cannot be empty")

        if not self.configuration:
            errors.append("Configuration cannot be empty")

        return errors
