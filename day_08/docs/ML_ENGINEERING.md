# ML Engineering Guide

## Overview

The Enhanced Token Analysis System includes a comprehensive ML Engineering framework designed to support the complete machine learning lifecycle. This guide covers model evaluation, performance monitoring, experiment tracking, and model registry management.

## Table of Contents

- [Model Evaluation](#model-evaluation)
- [Performance Monitoring](#performance-monitoring)
- [Experiment Tracking](#experiment-tracking)
- [Model Registry](#model-registry)
- [MLOps Integration](#mlops-integration)
- [Production Deployment](#production-deployment)
- [Best Practices](#best-practices)

## Model Evaluation

### Overview

The model evaluation framework provides comprehensive tools for assessing model performance, accuracy, and quality across different metrics and scenarios.

### ModelEvaluator

The `ModelEvaluator` class provides systematic evaluation capabilities:

```python
from ml.evaluation.model_evaluator import ModelEvaluator
from ml.evaluation.ground_truth_loader import GroundTruthLoader

# Initialize evaluator
ground_truth_loader = GroundTruthLoader()
evaluator = ModelEvaluator(ground_truth_loader)

# Evaluate token counting accuracy
test_data = [
    ("Hello world", 2),
    ("This is a longer text", 5),
    ("Machine learning is fascinating", 4)
]

evaluation_result = evaluator.evaluate_token_counting_accuracy(
    model_name="starcoder",
    test_data=test_data
)

print(f"MAE: {evaluation_result.mae}")
print(f"RMSE: {evaluation_result.rmse}")
print(f"R²: {evaluation_result.r_squared}")
```

### Evaluation Metrics

#### Token Counting Accuracy

- **MAE (Mean Absolute Error)**: Average absolute difference between predicted and actual token counts
- **RMSE (Root Mean Square Error)**: Square root of average squared differences
- **R² (Coefficient of Determination)**: Proportion of variance explained by the model
- **MAPE (Mean Absolute Percentage Error)**: Average percentage error

#### Compression Quality

- **Compression Ratio**: Ratio of compressed to original text length
- **Information Retention**: Percentage of key information preserved
- **Readability Score**: Assessment of compressed text readability
- **Semantic Similarity**: Cosine similarity between original and compressed embeddings

### Ground Truth Data

```python
class GroundTruthLoader:
    """Load and manage ground truth data for evaluation."""
    
    def load_token_counts(self, dataset_path: str) -> List[Tuple[str, int]]:
        """Load token count ground truth data."""
        
    def load_compression_data(self, dataset_path: str) -> List[CompressionSample]:
        """Load compression quality ground truth data."""
        
    def validate_data(self, data: List[Tuple[str, int]]) -> bool:
        """Validate ground truth data quality."""
```

### Evaluation Workflow

1. **Data Preparation**: Load and validate ground truth data
2. **Model Testing**: Run model on test dataset
3. **Metric Calculation**: Compute accuracy and quality metrics
4. **Report Generation**: Generate comprehensive evaluation report
5. **Quality Assessment**: Determine if model meets quality thresholds

## Performance Monitoring

### Overview

The performance monitoring system tracks model performance in production, detects drift, and provides alerting capabilities.

### PerformanceMonitor

```python
from ml.monitoring.performance_monitor import PerformanceMonitor
from ml.monitoring.metrics_storage import MetricsStorage

# Initialize monitor
storage = MetricsStorage()
monitor = PerformanceMonitor(storage)

# Track predictions
monitor.track_prediction(
    model_name="starcoder",
    prediction=token_count,
    latency=0.15,
    metadata={"text_length": len(text)}
)

# Detect drift
drift_report = monitor.detect_drift(
    model_name="starcoder",
    window_size=100,
    threshold=0.05
)

if drift_report.has_drift:
    print(f"Drift detected: {drift_report.drift_score}")
    print(f"Affected metrics: {drift_report.affected_metrics}")
```

### Drift Detection

#### Statistical Methods

- **KS Test**: Kolmogorov-Smirnov test for distribution changes
- **PSI (Population Stability Index)**: Measure of population distribution changes
- **Chi-Square Test**: Test for categorical distribution changes
- **Z-Score Analysis**: Detection of mean and variance shifts

#### Machine Learning Methods

- **Isolation Forest**: Anomaly detection for performance metrics
- **One-Class SVM**: Unsupervised drift detection
- **Autoencoder**: Reconstruction error-based drift detection

### Performance Metrics

#### Latency Metrics

- **P50**: 50th percentile response time
- **P95**: 95th percentile response time
- **P99**: 99th percentile response time
- **Average**: Mean response time

#### Throughput Metrics

- **Requests per Second**: Model throughput
- **Concurrent Users**: Number of simultaneous users
- **Queue Length**: Request queue size

#### Accuracy Metrics

- **Prediction Accuracy**: Percentage of correct predictions
- **Confidence Scores**: Model confidence distribution
- **Error Rates**: Classification and regression error rates

### Alerting System

```python
from ml.monitoring.alert_manager import AlertManager

alert_manager = AlertManager()

# Configure alerts
alert_manager.configure_alert(
    model_name="starcoder",
    metric="latency_p95",
    threshold=2.0,
    condition="greater_than"
)

# Send alerts
alert_manager.send_alert(
    model_name="starcoder",
    alert_type="performance_degradation",
    message="P95 latency exceeded threshold",
    severity="warning"
)
```

## Experiment Tracking

### Overview

The experiment tracking system provides comprehensive tools for managing ML experiments, comparing results, and ensuring reproducibility.

### ExperimentTracker

```python
from ml.experiments.experiment_tracker import ExperimentTracker
from ml.experiments.experiment_storage import ExperimentStorage

# Initialize tracker
storage = ExperimentStorage()
tracker = ExperimentTracker(storage)

# Start experiment
experiment_id = tracker.start_experiment(
    name="token_analysis_v2",
    hyperparameters={
        "model": "starcoder",
        "strategy": "hybrid",
        "max_tokens": 1000,
        "temperature": 0.7
    },
    description="Testing hybrid token counting strategy"
)

# Log metrics
tracker.log_metrics(
    experiment_id=experiment_id,
    metrics={
        "accuracy": 0.95,
        "latency": 0.15,
        "throughput": 100
    },
    step=1
)

# Log artifacts
tracker.log_artifacts(
    experiment_id=experiment_id,
    artifacts={
        "model": "path/to/model.pkl",
        "config": "path/to/config.yaml",
        "results": "path/to/results.json"
    }
)
```

### Experiment Lifecycle

#### 1. Experiment Planning

- Define objectives and success criteria
- Select hyperparameters to test
- Prepare datasets and validation splits
- Set up experiment infrastructure

#### 2. Experiment Execution

- Initialize experiment tracking
- Log hyperparameters and configuration
- Execute training and evaluation
- Log metrics and artifacts

#### 3. Experiment Analysis

- Compare experiment results
- Identify best performing configurations
- Analyze failure modes and edge cases
- Generate insights and recommendations

#### 4. Experiment Documentation

- Document findings and conclusions
- Share results with stakeholders
- Archive successful experiments
- Update model registry

### Hyperparameter Management

```python
# Define hyperparameter search space
hyperparameter_space = {
    "learning_rate": [0.001, 0.01, 0.1],
    "batch_size": [16, 32, 64],
    "hidden_layers": [2, 4, 6],
    "dropout": [0.1, 0.3, 0.5]
}

# Grid search
for lr in hyperparameter_space["learning_rate"]:
    for batch_size in hyperparameter_space["batch_size"]:
        experiment_id = tracker.start_experiment(
            name=f"grid_search_lr_{lr}_bs_{batch_size}",
            hyperparameters={
                "learning_rate": lr,
                "batch_size": batch_size
            }
        )
        # Run experiment...
```

### Experiment Comparison

```python
# Compare multiple experiments
experiment_ids = ["exp_001", "exp_002", "exp_003"]
comparison_report = tracker.compare_experiments(experiment_ids)

print("Best performing experiment:")
print(f"ID: {comparison_report.best_experiment_id}")
print(f"Accuracy: {comparison_report.best_accuracy}")
print(f"Latency: {comparison_report.best_latency}")

# Get best run for specific metric
best_run = tracker.get_best_run(
    experiment_id="exp_001",
    metric="accuracy",
    mode="max"
)
```

## Model Registry

### Overview

The model registry provides versioning, lifecycle management, and production deployment capabilities for ML models.

### ModelRegistry

```python
from ml.registry.model_registry import ModelRegistry
from ml.registry.model_storage import ModelStorage

# Initialize registry
storage = ModelStorage()
registry = ModelRegistry(storage)

# Register model
model_id = registry.register_model(
    model_name="starcoder",
    version="2.0",
    metadata={
        "accuracy": 0.95,
        "latency": 0.15,
        "training_data": "token_dataset_v2",
        "algorithm": "hybrid_token_counter"
    },
    model_path="/path/to/model.pkl"
)

# Promote to production
registry.promote_to_production(
    model_name="starcoder",
    version="2.0"
)

# Rollback if needed
registry.rollback_model(
    model_name="starcoder",
    target_version="1.9"
)
```

### Model Lifecycle

#### 1. Development

- Train and validate model
- Register model with metadata
- Tag as "development" status

#### 2. Staging

- Deploy to staging environment
- Run integration tests
- Validate performance metrics
- Tag as "staging" status

#### 3. Production

- Promote to production
- Monitor performance
- Tag as "production" status
- Set up rollback procedures

#### 4. Deprecation

- Mark for deprecation
- Notify stakeholders
- Plan migration to new version
- Archive deprecated models

### Model Versioning

```python
# Semantic versioning for models
model_versions = [
    "1.0.0",  # Initial release
    "1.1.0",  # Minor improvements
    "1.1.1",  # Bug fixes
    "2.0.0",  # Major changes
    "2.0.1"   # Critical fixes
]

# Version comparison
from ml.registry.version_manager import VersionManager

version_manager = VersionManager()
latest_version = version_manager.get_latest_version("starcoder")
compatible_versions = version_manager.get_compatible_versions("starcoder", "2.0.0")
```

### Model Metadata

```python
# Comprehensive model metadata
model_metadata = {
    "name": "starcoder",
    "version": "2.0.0",
    "description": "Enhanced token counting model",
    "algorithm": "hybrid_token_counter",
    "training_data": {
        "dataset": "token_dataset_v2",
        "size": 1000000,
        "split": "train/validation/test"
    },
    "performance": {
        "accuracy": 0.95,
        "latency_p95": 0.15,
        "throughput": 1000
    },
    "dependencies": {
        "python": ">=3.8",
        "torch": ">=1.9.0",
        "transformers": ">=4.20.0"
    },
    "deployment": {
        "environment": "production",
        "resources": {
            "cpu": "2 cores",
            "memory": "4GB",
            "gpu": "optional"
        }
    }
}
```

## MLOps Integration

### CI/CD Pipeline

```yaml
# .github/workflows/ml-pipeline.yml
name: ML Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          python -m pytest tests/
          python -m pytest tests/ml/
      
  evaluate:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Evaluate model
        run: |
          python -m ml.evaluation.evaluate_model
      
  deploy:
    needs: evaluate
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to staging
        run: |
          python -m ml.registry.deploy_model --environment staging
```

### Monitoring Integration

```python
# Integration with external monitoring systems
from ml.monitoring.integrations import PrometheusIntegration, GrafanaIntegration

# Prometheus metrics
prometheus = PrometheusIntegration()
prometheus.export_metrics(
    model_name="starcoder",
    metrics=["latency", "throughput", "accuracy"]
)

# Grafana dashboards
grafana = GrafanaIntegration()
grafana.create_dashboard(
    model_name="starcoder",
    panels=["latency", "throughput", "error_rate", "drift_score"]
)
```

### Data Pipeline Integration

```python
# Integration with data pipelines
from ml.pipelines.data_pipeline import DataPipeline

data_pipeline = DataPipeline()

# Data validation
validation_result = data_pipeline.validate_data(
    dataset_path="data/token_dataset_v2",
    schema_path="schemas/token_dataset.json"
)

# Data preprocessing
processed_data = data_pipeline.preprocess_data(
    raw_data=validation_result.data,
    preprocessing_config="configs/preprocessing.yaml"
)

# Feature engineering
features = data_pipeline.extract_features(
    data=processed_data,
    feature_config="configs/features.yaml"
)
```

## Production Deployment

### Container Deployment

```dockerfile
# Dockerfile for ML model deployment
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy model and code
COPY ml/ ./ml/
COPY models/ ./models/
COPY config/ ./config/

# Set environment variables
ENV MODEL_NAME=starcoder
ENV MODEL_VERSION=2.0.0
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Start model server
CMD ["python", "-m", "ml.serving.model_server"]
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: starcoder-model
spec:
  replicas: 3
  selector:
    matchLabels:
      app: starcoder-model
  template:
    metadata:
      labels:
        app: starcoder-model
    spec:
      containers:
      - name: starcoder-model
        image: starcoder-model:2.0.0
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_NAME
          value: "starcoder"
        - name: MODEL_VERSION
          value: "2.0.0"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: starcoder-model-service
spec:
  selector:
    app: starcoder-model
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### Health Checks

```python
# Model health check endpoint
from ml.serving.health_check import HealthChecker

health_checker = HealthChecker()

@health_checker.health_endpoint
def model_health():
    """Check model health and readiness."""
    return {
        "status": "healthy",
        "model_name": "starcoder",
        "version": "2.0.0",
        "latency": health_checker.check_latency(),
        "memory_usage": health_checker.check_memory(),
        "dependencies": health_checker.check_dependencies()
    }
```

## Best Practices

### Model Evaluation

1. **Use Multiple Metrics**: Don't rely on a single metric for evaluation
2. **Cross-Validation**: Use k-fold cross-validation for robust evaluation
3. **Holdout Test Set**: Keep a separate test set for final evaluation
4. **Statistical Significance**: Test for statistical significance of improvements
5. **Baseline Comparison**: Always compare against baseline models

### Performance Monitoring

1. **Set Appropriate Thresholds**: Use domain knowledge to set meaningful thresholds
2. **Monitor Multiple Metrics**: Track both accuracy and performance metrics
3. **Automated Alerting**: Set up automated alerts for critical issues
4. **Regular Review**: Regularly review monitoring dashboards and reports
5. **Documentation**: Document monitoring procedures and escalation paths

### Experiment Tracking

1. **Consistent Naming**: Use consistent naming conventions for experiments
2. **Comprehensive Logging**: Log all relevant metrics, hyperparameters, and artifacts
3. **Version Control**: Use version control for experiment code and data
4. **Reproducibility**: Ensure experiments can be reproduced exactly
5. **Documentation**: Document experiment objectives, methods, and results

### Model Registry

1. **Semantic Versioning**: Use semantic versioning for model versions
2. **Rich Metadata**: Include comprehensive metadata for each model
3. **Automated Testing**: Automate model testing before promotion
4. **Rollback Procedures**: Have clear rollback procedures for production models
5. **Access Control**: Implement proper access control for model registry

### Production Deployment

1. **Blue-Green Deployment**: Use blue-green deployment for zero-downtime updates
2. **Canary Releases**: Gradually roll out new models to a subset of users
3. **Monitoring**: Monitor model performance closely after deployment
4. **Rollback Plan**: Have a clear rollback plan for failed deployments
5. **Documentation**: Document deployment procedures and troubleshooting guides

## Troubleshooting

### Common Issues

#### Model Performance Degradation

```python
# Diagnose performance issues
from ml.troubleshooting.performance_diagnostics import PerformanceDiagnostics

diagnostics = PerformanceDiagnostics()

# Check for data drift
data_drift = diagnostics.check_data_drift(
    model_name="starcoder",
    current_data="data/current.csv",
    training_data="data/training.csv"
)

# Check for concept drift
concept_drift = diagnostics.check_concept_drift(
    model_name="starcoder",
    window_size=1000
)

# Generate diagnostic report
report = diagnostics.generate_report(
    model_name="starcoder",
    issues=[data_drift, concept_drift]
)
```

#### Experiment Failures

```python
# Debug experiment failures
from ml.troubleshooting.experiment_debugger import ExperimentDebugger

debugger = ExperimentDebugger()

# Analyze failed experiment
failure_analysis = debugger.analyze_failure(
    experiment_id="exp_001",
    error_log="logs/experiment_001.log"
)

# Check resource usage
resource_usage = debugger.check_resource_usage(
    experiment_id="exp_001"
)

# Generate debugging report
debug_report = debugger.generate_debug_report(
    experiment_id="exp_001",
    analysis=failure_analysis,
    resources=resource_usage
)
```

### Performance Optimization

```python
# Optimize model performance
from ml.optimization.model_optimizer import ModelOptimizer

optimizer = ModelOptimizer()

# Profile model performance
profile = optimizer.profile_model(
    model_name="starcoder",
    input_data="data/test_inputs.csv"
)

# Optimize inference
optimized_model = optimizer.optimize_inference(
    model_name="starcoder",
    optimization_level="aggressive"
)

# Benchmark performance
benchmark_results = optimizer.benchmark(
    original_model="starcoder:1.9.0",
    optimized_model="starcoder:2.0.0",
    test_data="data/benchmark.csv"
)
```

## Conclusion

The ML Engineering framework provides comprehensive tools for managing the complete machine learning lifecycle. By following the best practices outlined in this guide, you can ensure reliable, scalable, and maintainable ML systems in production.

For additional support and examples, refer to the API documentation and example scripts in the project repository.
