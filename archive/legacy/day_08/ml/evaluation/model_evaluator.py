"""
Model evaluation framework for tracking token counting accuracy and performance.

This module provides comprehensive evaluation capabilities for ML models,
including accuracy metrics, performance tracking, and ground truth validation.
"""

import asyncio
import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from utils.logging import LoggerFactory


class EvaluationMetrics(BaseModel):
    """Metrics for model evaluation."""

    # Accuracy metrics
    mae: float = Field(description="Mean Absolute Error")
    rmse: float = Field(description="Root Mean Square Error")
    mape: float = Field(description="Mean Absolute Percentage Error")

    # Performance metrics
    avg_processing_time: float = Field(description="Average processing time in seconds")
    p50_processing_time: float = Field(description="50th percentile processing time")
    p95_processing_time: float = Field(description="95th percentile processing time")
    p99_processing_time: float = Field(description="99th percentile processing time")

    # Compression quality metrics
    compression_ratio: float = Field(description="Average compression ratio")
    quality_score: float = Field(description="Overall quality score (0-1)")

    # Token counting accuracy
    token_count_accuracy: float = Field(description="Token counting accuracy (0-1)")
    prediction_confidence: float = Field(description="Average prediction confidence")

    # Metadata
    evaluation_timestamp: datetime = Field(default_factory=datetime.now)
    model_version: str = Field(description="Model version evaluated")
    dataset_size: int = Field(description="Number of samples evaluated")


class GroundTruthData(BaseModel):
    """Ground truth data for evaluation."""

    input_text: str = Field(description="Input text")
    expected_token_count: int = Field(description="Expected token count")
    expected_compression_ratio: float = Field(description="Expected compression ratio")
    expected_processing_time: float = Field(description="Expected processing time")
    quality_label: str = Field(description="Quality label (good/fair/poor)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class EvaluationResult(BaseModel):
    """Result of model evaluation."""

    model_name: str = Field(description="Name of the evaluated model")
    metrics: EvaluationMetrics = Field(description="Evaluation metrics")
    ground_truth_samples: int = Field(description="Number of ground truth samples")
    evaluation_duration: float = Field(
        description="Total evaluation duration in seconds"
    )
    errors: List[str] = Field(default_factory=list, description="Evaluation errors")
    warnings: List[str] = Field(default_factory=list, description="Evaluation warnings")


class ModelEvaluator:
    """
    Model evaluator for tracking token counting accuracy and performance.

    Provides comprehensive evaluation capabilities including:
    - Token counting accuracy assessment
    - Performance metrics (latency, throughput)
    - Compression quality evaluation
    - Ground truth validation
    - Statistical analysis
    """

    def __init__(self, ground_truth_path: Optional[Path] = None):
        """
        Initialize model evaluator.

        Args:
            ground_truth_path: Path to ground truth data file
        """
        self.logger = LoggerFactory.create_logger(__name__)
        self.ground_truth_path = ground_truth_path or Path("data/ground_truth.json")
        self.ground_truth_data: List[GroundTruthData] = []
        self.evaluation_history: List[EvaluationResult] = []

        # Load ground truth data if available
        self._load_ground_truth_data()

    def _load_ground_truth_data(self) -> None:
        """Load ground truth data from file."""
        try:
            if self.ground_truth_path.exists():
                with open(self.ground_truth_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.ground_truth_data = [GroundTruthData(**item) for item in data]
                self.logger.info(
                    f"Loaded {len(self.ground_truth_data)} ground truth samples"
                )
            else:
                self.logger.warning(
                    f"Ground truth file not found: {self.ground_truth_path}"
                )
                self._create_sample_ground_truth()
        except Exception as e:
            self.logger.error(f"Failed to load ground truth data: {e}")
            self._create_sample_ground_truth()

    def _create_sample_ground_truth(self) -> None:
        """Create sample ground truth data for testing."""
        sample_data = [
            GroundTruthData(
                input_text="This is a short test text for token counting evaluation.",
                expected_token_count=12,
                expected_compression_ratio=0.8,
                expected_processing_time=0.1,
                quality_label="good",
            ),
            GroundTruthData(
                input_text="A longer text that contains more tokens and should be compressed more effectively to demonstrate the capabilities of our token counting and compression system.",
                expected_token_count=25,
                expected_compression_ratio=0.6,
                expected_processing_time=0.2,
                quality_label="good",
            ),
            GroundTruthData(
                input_text="Very long text " * 50,
                expected_token_count=200,
                expected_compression_ratio=0.4,
                expected_processing_time=0.5,
                quality_label="fair",
            ),
        ]

        self.ground_truth_data = sample_data
        self.logger.info(f"Created {len(sample_data)} sample ground truth entries")

    async def evaluate_model(
        self,
        model_name: str,
        model_version: str,
        token_counter_func: callable,
        compression_func: callable,
        sample_size: Optional[int] = None,
    ) -> EvaluationResult:
        """
        Evaluate model performance against ground truth data.

        Args:
            model_name: Name of the model to evaluate
            model_version: Version of the model
            token_counter_func: Function to count tokens
            compression_func: Function to compress text
            sample_size: Number of samples to evaluate (None for all)

        Returns:
            EvaluationResult: Comprehensive evaluation results
        """
        self.logger.info(f"Starting evaluation for model {model_name} v{model_version}")

        start_time = datetime.now()
        errors = []
        warnings = []

        # Prepare evaluation data
        eval_data = (
            self.ground_truth_data[:sample_size]
            if sample_size
            else self.ground_truth_data
        )

        if not eval_data:
            error_msg = "No ground truth data available for evaluation"
            self.logger.error(error_msg)
            errors.append(error_msg)
            return EvaluationResult(
                model_name=model_name,
                metrics=EvaluationMetrics(model_version=model_version),
                ground_truth_samples=0,
                evaluation_duration=0.0,
                errors=errors,
            )

        # Collect predictions and metrics
        predictions = []
        processing_times = []
        compression_ratios = []
        quality_scores = []

        for i, sample in enumerate(eval_data):
            try:
                # Measure processing time
                process_start = datetime.now()

                # Get token count prediction
                predicted_tokens = await self._safe_call(
                    token_counter_func, sample.input_text
                )

                # Get compression prediction
                compressed_text = await self._safe_call(
                    compression_func, sample.input_text
                )
                predicted_compression = len(compressed_text) / len(sample.input_text)

                process_end = datetime.now()
                processing_time = (process_end - process_start).total_seconds()

                # Calculate quality score
                quality_score = self._calculate_quality_score(
                    predicted_tokens,
                    sample.expected_token_count,
                    predicted_compression,
                    sample.expected_compression_ratio,
                )

                predictions.append(
                    {
                        "predicted_tokens": predicted_tokens,
                        "expected_tokens": sample.expected_token_count,
                        "predicted_compression": predicted_compression,
                        "expected_compression": sample.expected_compression_ratio,
                        "quality_score": quality_score,
                        "processing_time": processing_time,
                    }
                )

                processing_times.append(processing_time)
                compression_ratios.append(predicted_compression)
                quality_scores.append(quality_score)

            except Exception as e:
                error_msg = f"Error processing sample {i}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)

        # Calculate metrics
        metrics = self._calculate_metrics(
            predictions,
            processing_times,
            compression_ratios,
            quality_scores,
            model_version,
        )

        evaluation_duration = (datetime.now() - start_time).total_seconds()

        result = EvaluationResult(
            model_name=model_name,
            metrics=metrics,
            ground_truth_samples=len(eval_data),
            evaluation_duration=evaluation_duration,
            errors=errors,
            warnings=warnings,
        )

        # Store evaluation result
        self.evaluation_history.append(result)

        self.logger.info(
            f"Evaluation completed for {model_name}: MAE={metrics.mae:.3f}, RMSE={metrics.rmse:.3f}"
        )

        return result

    async def _safe_call(self, func: callable, *args, **kwargs) -> Any:
        """Safely call a function with error handling."""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Function call failed: {e}")
            raise

    def _calculate_quality_score(
        self,
        predicted_tokens: int,
        expected_tokens: int,
        predicted_compression: float,
        expected_compression: float,
    ) -> float:
        """
        Calculate quality score based on prediction accuracy.

        Args:
            predicted_tokens: Predicted token count
            expected_tokens: Expected token count
            predicted_compression: Predicted compression ratio
            expected_compression: Expected compression ratio

        Returns:
            float: Quality score between 0 and 1
        """
        # Token count accuracy (weighted 60%)
        token_error = abs(predicted_tokens - expected_tokens) / max(expected_tokens, 1)
        token_score = max(0, 1 - token_error)

        # Compression accuracy (weighted 40%)
        compression_error = abs(predicted_compression - expected_compression) / max(
            expected_compression, 0.01
        )
        compression_score = max(0, 1 - compression_error)

        return 0.6 * token_score + 0.4 * compression_score

    def _calculate_metrics(
        self,
        predictions: List[Dict],
        processing_times: List[float],
        compression_ratios: List[float],
        quality_scores: List[float],
        model_version: str,
    ) -> EvaluationMetrics:
        """Calculate comprehensive evaluation metrics."""

        if not predictions:
            return EvaluationMetrics(model_version=model_version, dataset_size=0)

        # Token count accuracy metrics
        token_errors = [
            abs(p["predicted_tokens"] - p["expected_tokens"]) for p in predictions
        ]

        token_percentage_errors = [
            abs(p["predicted_tokens"] - p["expected_tokens"])
            / max(p["expected_tokens"], 1)
            for p in predictions
        ]

        mae = statistics.mean(token_errors) if token_errors else 0.0
        rmse = (
            statistics.sqrt(statistics.mean([e**2 for e in token_errors]))
            if token_errors
            else 0.0
        )
        mape = (
            statistics.mean(token_percentage_errors) * 100
            if token_percentage_errors
            else 0.0
        )

        # Performance metrics
        avg_processing_time = (
            statistics.mean(processing_times) if processing_times else 0.0
        )
        p50_processing_time = (
            statistics.median(processing_times) if processing_times else 0.0
        )
        p95_processing_time = (
            self._percentile(processing_times, 95) if processing_times else 0.0
        )
        p99_processing_time = (
            self._percentile(processing_times, 99) if processing_times else 0.0
        )

        # Compression and quality metrics
        compression_ratio = (
            statistics.mean(compression_ratios) if compression_ratios else 0.0
        )
        quality_score = statistics.mean(quality_scores) if quality_scores else 0.0

        # Token counting accuracy
        token_count_accuracy = (
            statistics.mean(quality_scores) if quality_scores else 0.0
        )

        # Prediction confidence (simplified)
        prediction_confidence = max(0, 1 - mape / 100) if mape > 0 else 1.0

        return EvaluationMetrics(
            mae=mae,
            rmse=rmse,
            mape=mape,
            avg_processing_time=avg_processing_time,
            p50_processing_time=p50_processing_time,
            p95_processing_time=p95_processing_time,
            p99_processing_time=p99_processing_time,
            compression_ratio=compression_ratio,
            quality_score=quality_score,
            token_count_accuracy=token_count_accuracy,
            prediction_confidence=prediction_confidence,
            model_version=model_version,
            dataset_size=len(predictions),
        )

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]

    def get_evaluation_summary(
        self, model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary of evaluation results.

        Args:
            model_name: Optional model name filter

        Returns:
            Dict[str, Any]: Evaluation summary
        """
        results = self.evaluation_history
        if model_name:
            results = [r for r in results if r.model_name == model_name]

        if not results:
            return {"message": "No evaluation results available"}

        # Calculate summary statistics
        all_mae = [r.metrics.mae for r in results]
        all_rmse = [r.metrics.rmse for r in results]
        all_quality = [r.metrics.quality_score for r in results]

        return {
            "total_evaluations": len(results),
            "models_evaluated": len(set(r.model_name for r in results)),
            "average_mae": statistics.mean(all_mae) if all_mae else 0.0,
            "average_rmse": statistics.mean(all_rmse) if all_rmse else 0.0,
            "average_quality_score": statistics.mean(all_quality)
            if all_quality
            else 0.0,
            "best_performance": max(results, key=lambda r: r.metrics.quality_score),
            "latest_evaluation": results[-1] if results else None,
        }

    def save_evaluation_results(self, file_path: Path) -> None:
        """Save evaluation results to file."""
        try:
            data = [result.dict() for result in self.evaluation_history]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"Saved {len(data)} evaluation results to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save evaluation results: {e}")

    def load_evaluation_results(self, file_path: Path) -> None:
        """Load evaluation results from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.evaluation_history = [EvaluationResult(**item) for item in data]
            self.logger.info(
                f"Loaded {len(self.evaluation_history)} evaluation results"
            )
        except Exception as e:
            self.logger.error(f"Failed to load evaluation results: {e}")
