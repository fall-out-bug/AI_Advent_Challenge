"""
ML Engineering module for Day 8 AI Challenge.

This module provides comprehensive ML engineering capabilities including:
- Model evaluation and performance tracking
- Performance monitoring with drift detection
- Experiment tracking and management
- Model registry with versioning and promotion
"""

from .evaluation.model_evaluator import (
    EvaluationMetrics,
    EvaluationResult,
    GroundTruthData,
    ModelEvaluator,
)
from .experiments.experiment_tracker import (
    ExperimentComparison,
    ExperimentConfig,
    ExperimentMetrics,
    ExperimentRun,
    ExperimentTracker,
)
from .monitoring.performance_monitor import (
    Alert,
    DriftDetectionResult,
    PerformanceMetrics,
    PerformanceMonitor,
)
from .registry.model_registry import (
    ModelMetadata,
    ModelRegistry,
    ModelStage,
    ModelStatus,
    ModelVersion,
    PromotionRequest,
)

__all__ = [
    # Evaluation
    "ModelEvaluator",
    "EvaluationMetrics",
    "EvaluationResult",
    "GroundTruthData",
    # Monitoring
    "PerformanceMonitor",
    "PerformanceMetrics",
    "DriftDetectionResult",
    "Alert",
    # Experiments
    "ExperimentTracker",
    "ExperimentConfig",
    "ExperimentMetrics",
    "ExperimentRun",
    "ExperimentComparison",
    # Registry
    "ModelRegistry",
    "ModelMetadata",
    "ModelVersion",
    "PromotionRequest",
    "ModelStage",
    "ModelStatus",
]
