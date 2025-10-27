#!/usr/bin/env python3
"""
ML Engineering Examples

This script demonstrates the ML Engineering framework including model evaluation,
performance monitoring, experiment tracking, and model registry.
"""

import asyncio
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# ML Engineering imports
from ml.evaluation.model_evaluator import ModelEvaluator
from ml.experiments.experiment_tracker import ExperimentTracker
from ml.monitoring.performance_monitor import PerformanceMonitor
from ml.registry.model_registry import ModelRegistry


# Mock implementations for demonstration
class MockGroundTruthLoader:
    """Mock ground truth loader for examples."""

    def load_token_counts(self, dataset_path: str) -> List[tuple]:
        """Load mock token count data."""
        return [
            ("Hello world", 2),
            ("This is a test", 4),
            ("Machine learning is fascinating", 5),
            ("Python programming language", 4),
            ("Artificial intelligence and data science", 7),
        ]


class MockMetricsStorage:
    """Mock metrics storage for examples."""

    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = {}

    def store_metric(self, model_name: str, metric: Dict[str, Any]) -> None:
        """Store metric data."""
        if model_name not in self.metrics:
            self.metrics[model_name] = []
        self.metrics[model_name].append(metric)

    def get_metrics(self, model_name: str, limit: int = 100) -> List[Dict]:
        """Get stored metrics."""
        return self.metrics.get(model_name, [])[-limit:]


class MockExperimentStorage:
    """Mock experiment storage for examples."""

    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.runs: Dict[str, List[Dict]] = {}

    def save_experiment(self, experiment: Dict[str, Any]) -> None:
        """Save experiment data."""
        self.experiments[experiment["id"]] = experiment

    def save_run(self, experiment_id: str, run: Dict[str, Any]) -> None:
        """Save experiment run."""
        if experiment_id not in self.runs:
            self.runs[experiment_id] = []
        self.runs[experiment_id].append(run)

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """Get experiment data."""
        return self.experiments.get(experiment_id)

    def get_runs(self, experiment_id: str) -> List[Dict]:
        """Get experiment runs."""
        return self.runs.get(experiment_id, [])


class MockModelStorage:
    """Mock model storage for examples."""

    def __init__(self):
        self.models: Dict[str, Dict] = {}

    def save_model(self, model: Dict[str, Any]) -> None:
        """Save model data."""
        key = f"{model['name']}:{model['version']}"
        self.models[key] = model

    def get_model(self, name: str, version: str) -> Optional[Dict]:
        """Get model data."""
        key = f"{name}:{version}"
        return self.models.get(key)

    def list_models(self) -> List[Dict]:
        """List all models."""
        return list(self.models.values())


def demonstrate_model_evaluation():
    """Demonstrate model evaluation framework."""
    print("=== Model Evaluation Demo ===")

    # Initialize evaluator
    ground_truth_loader = MockGroundTruthLoader()
    evaluator = ModelEvaluator(ground_truth_loader)

    print("\n1. Token Counting Accuracy Evaluation:")

    # Load test data
    test_data = ground_truth_loader.load_token_counts("mock_dataset.csv")
    print(f"Loaded {len(test_data)} test samples")

    # Mock predictions (simulate model predictions)
    predictions = [
        random.randint(max(1, actual - 1), actual + 1) for _, actual in test_data
    ]
    ground_truth = [actual for _, actual in test_data]

    print(f"Ground truth: {ground_truth}")
    print(f"Predictions:  {predictions}")

    # Calculate metrics
    metrics = evaluator.calculate_metrics(predictions, ground_truth)
    print(f"\nEvaluation Metrics:")
    print(f"  MAE: {metrics.get('mae', 0):.2f}")
    print(f"  RMSE: {metrics.get('rmse', 0):.2f}")
    print(f"  R²: {metrics.get('r_squared', 0):.2f}")

    # Evaluate compression quality
    print("\n2. Compression Quality Evaluation:")
    original_texts = [
        "This is a long text that needs compression",
        "Another long text for compression analysis",
        "Yet another text for quality evaluation",
    ]
    compressed_texts = [
        "Long text compressed",
        "Another text compressed",
        "Text compressed",
    ]
    compression_ratios = [0.6, 0.7, 0.8]

    quality_report = evaluator.evaluate_compression_quality(
        original_texts, compressed_texts, compression_ratios
    )
    print(f"Compression Quality Report:")
    print(f"  Average ratio: {quality_report.average_ratio:.2f}")
    print(f"  Quality score: {quality_report.quality_score:.2f}")
    print(f"  Readability score: {quality_report.readability_score:.2f}")


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring."""
    print("\n=== Performance Monitoring Demo ===")

    # Initialize monitor
    storage = MockMetricsStorage()
    monitor = PerformanceMonitor(storage)

    print("\n1. Prediction Tracking:")

    # Simulate prediction tracking
    model_name = "starcoder"
    for i in range(10):
        prediction = random.randint(5, 20)
        latency = random.uniform(0.1, 0.5)

        monitor.track_prediction(
            model_name=model_name,
            prediction=prediction,
            latency=latency,
            metadata={"batch_id": i, "text_length": random.randint(10, 100)},
        )

        print(f"  Tracked prediction {i+1}: {prediction} tokens, {latency:.3f}s")

    # Detect drift
    print("\n2. Drift Detection:")
    drift_report = monitor.detect_drift(
        model_name=model_name, window_size=5, threshold=0.1
    )

    print(f"Drift Analysis:")
    print(f"  Has drift: {drift_report.has_drift}")
    print(f"  Drift score: {drift_report.drift_score:.3f}")
    print(f"  Affected metrics: {drift_report.affected_metrics}")
    print(f"  Confidence: {drift_report.confidence:.2f}")

    # Performance report
    print("\n3. Performance Report:")
    performance_report = monitor.get_performance_report(
        model_name=model_name,
        time_range=(datetime.now() - timedelta(hours=1), datetime.now()),
    )

    print(f"Performance Metrics:")
    print(f"  Total predictions: {performance_report.total_predictions}")
    print(f"  Average latency: {performance_report.average_latency:.3f}s")
    print(f"  P95 latency: {performance_report.p95_latency:.3f}s")
    print(f"  Throughput: {performance_report.throughput:.1f} req/s")


def demonstrate_experiment_tracking():
    """Demonstrate experiment tracking."""
    print("\n=== Experiment Tracking Demo ===")

    # Initialize tracker
    storage = MockExperimentStorage()
    tracker = ExperimentTracker(storage)

    print("\n1. Starting Experiment:")

    # Start experiment
    experiment_id = tracker.start_experiment(
        name="token_analysis_optimization",
        hyperparameters={
            "model": "starcoder",
            "strategy": "hybrid",
            "max_tokens": 1000,
            "temperature": 0.7,
            "learning_rate": 0.001,
        },
        description="Optimizing token analysis for better accuracy",
    )

    print(f"Started experiment: {experiment_id}")

    # Log metrics over time
    print("\n2. Logging Metrics:")
    for epoch in range(5):
        metrics = {
            "accuracy": 0.8 + epoch * 0.03 + random.uniform(-0.02, 0.02),
            "latency": 0.2 - epoch * 0.01 + random.uniform(-0.01, 0.01),
            "throughput": 100 + epoch * 10 + random.uniform(-5, 5),
            "loss": 0.5 - epoch * 0.05 + random.uniform(-0.02, 0.02),
        }

        tracker.log_metrics(experiment_id=experiment_id, metrics=metrics, step=epoch)

        print(
            f"  Epoch {epoch}: accuracy={metrics['accuracy']:.3f}, "
            f"latency={metrics['latency']:.3f}s"
        )

    # Log artifacts
    print("\n3. Logging Artifacts:")
    artifacts = {
        "model": f"/models/token_analyzer_{experiment_id}.pkl",
        "config": f"/configs/experiment_{experiment_id}.yaml",
        "results": f"/results/experiment_{experiment_id}.json",
    }

    tracker.log_artifacts(experiment_id, artifacts)
    print(f"Logged artifacts: {list(artifacts.keys())}")

    # Compare experiments
    print("\n4. Experiment Comparison:")
    # Create another experiment for comparison
    experiment_id_2 = tracker.start_experiment(
        name="token_analysis_baseline",
        hyperparameters={
            "model": "starcoder",
            "strategy": "simple",
            "max_tokens": 1000,
        },
    )

    # Log some metrics for comparison
    for epoch in range(3):
        metrics = {"accuracy": 0.75 + epoch * 0.02, "latency": 0.25, "throughput": 80}
        tracker.log_metrics(experiment_id_2, metrics, step=epoch)

    comparison_report = tracker.compare_experiments([experiment_id, experiment_id_2])
    print(f"Comparison Results:")
    print(f"  Best experiment: {comparison_report.best_experiment_id}")
    print(f"  Best accuracy: {comparison_report.best_accuracy:.3f}")
    print(f"  Improvement: {comparison_report.improvement:.1f}%")


def demonstrate_model_registry():
    """Demonstrate model registry."""
    print("\n=== Model Registry Demo ===")

    # Initialize registry
    storage = MockModelStorage()
    registry = ModelRegistry(storage)

    print("\n1. Model Registration:")

    # Register multiple model versions
    models = [
        {
            "name": "starcoder",
            "version": "1.0.0",
            "metadata": {
                "accuracy": 0.85,
                "latency": 0.2,
                "training_data": "dataset_v1",
                "algorithm": "simple_token_counter",
            },
        },
        {
            "name": "starcoder",
            "version": "1.1.0",
            "metadata": {
                "accuracy": 0.88,
                "latency": 0.18,
                "training_data": "dataset_v1",
                "algorithm": "improved_token_counter",
            },
        },
        {
            "name": "starcoder",
            "version": "2.0.0",
            "metadata": {
                "accuracy": 0.92,
                "latency": 0.15,
                "training_data": "dataset_v2",
                "algorithm": "hybrid_token_counter",
            },
        },
    ]

    for model in models:
        model_id = registry.register_model(
            model_name=model["name"],
            version=model["version"],
            metadata=model["metadata"],
            model_path=f"/models/{model['name']}_{model['version']}.pkl",
        )
        print(f"  Registered {model['name']} v{model['version']}: {model_id}")

    # Promote to production
    print("\n2. Production Promotion:")
    registry.promote_to_production("starcoder", "2.0.0")
    print("  Promoted starcoder v2.0.0 to production")

    # Get model info
    print("\n3. Model Information:")
    model_info = registry.get_model_info("starcoder", "2.0.0")
    print(f"Model: {model_info.name}")
    print(f"Version: {model_info.version}")
    print(f"Status: {model_info.status}")
    print(f"Accuracy: {model_info.metadata['accuracy']}")
    print(f"Latency: {model_info.metadata['latency']}s")

    # List all models
    print("\n4. Model Listing:")
    all_models = registry.list_models()
    print(f"Total models: {len(all_models)}")
    for model in all_models:
        print(f"  {model['name']} v{model['version']} - {model['status']}")

    # Rollback demonstration
    print("\n5. Model Rollback:")
    registry.rollback_model("starcoder", "1.1.0")
    print("  Rolled back starcoder to v1.1.0")

    # Verify rollback
    current_model = registry.get_model_info("starcoder")
    print(f"Current production model: {current_model.name} v{current_model.version}")


def demonstrate_mlops_integration():
    """Demonstrate MLOps integration concepts."""
    print("\n=== MLOps Integration Demo ===")

    print("MLOps Integration Components:")
    print("1. CI/CD Pipeline:")
    print("   - Automated testing on code changes")
    print("   - Model evaluation in staging")
    print("   - Automated deployment to production")

    print("\n2. Monitoring Integration:")
    print("   - Prometheus metrics export")
    print("   - Grafana dashboards")
    print("   - Alert manager integration")

    print("\n3. Data Pipeline Integration:")
    print("   - Data validation and preprocessing")
    print("   - Feature engineering")
    print("   - Data quality monitoring")

    print("\n4. Model Serving:")
    print("   - Container deployment")
    print("   - Health checks")
    print("   - Load balancing")

    print("\n5. A/B Testing:")
    print("   - Traffic splitting")
    print("   - Performance comparison")
    print("   - Gradual rollout")


async def main():
    """Main demonstration function."""
    print("ML Engineering Framework Examples")
    print("=" * 50)

    # Demonstrate model evaluation
    demonstrate_model_evaluation()

    # Demonstrate performance monitoring
    demonstrate_performance_monitoring()

    # Demonstrate experiment tracking
    demonstrate_experiment_tracking()

    # Demonstrate model registry
    demonstrate_model_registry()

    # Demonstrate MLOps integration
    demonstrate_mlops_integration()

    print("\n" + "=" * 50)
    print("ML Engineering Demo Complete!")
    print("\nKey Benefits Demonstrated:")
    print("✓ Comprehensive model evaluation with multiple metrics")
    print("✓ Performance monitoring with drift detection")
    print("✓ Experiment tracking for reproducibility")
    print("✓ Model registry with versioning and lifecycle management")
    print("✓ MLOps integration for production deployment")
    print("✓ Production-ready monitoring and alerting")


if __name__ == "__main__":
    asyncio.run(main())
