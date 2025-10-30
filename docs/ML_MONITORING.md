# ML Monitoring Documentation

## Overview

This document describes ML-specific monitoring, metrics, and model versioning for LLM services.

## ML Metrics

### Inference Metrics

**Location**: `src/infrastructure/ml/metrics.py`

**Metrics**:
- `llm_inference_latency_seconds` - Histogram of inference latency (P50, P95, P99)
- `llm_token_generation_rate_total` - Counter of tokens generated per model
- `llm_request_token_count` - Histogram of input/output tokens per request
- `llm_error_rate_total` - Counter of errors by type and model

### Quality Metrics

- `llm_response_quality_score` - Gauge of response quality (0-1)
- `llm_summarization_length` - Histogram of summarization output length
- `llm_intent_parsing_accuracy_total` - Counter of accuracy measurements

### Model Metadata

- `llm_model_version` - Gauge tracking deployed model version
- `llm_model_deployed_at_seconds` - Gauge tracking deployment timestamp

## Model Versioning

### Model Registry

**Location**: `src/infrastructure/ml/model_registry.py`

**Usage**:

```python
from src.infrastructure.ml.model_registry import get_model_registry

registry = get_model_registry()
registry.register_model(
    model_name="mistral",
    version="v1.0.0",
    model_hash="abc123...",
    metadata={"deployment_date": "2024-01-01"}
)

# Get model info
info = registry.get_model_info("mistral")
version = registry.get_model_version("mistral")
```

### Model Version Endpoint

**Future**: Add `/api/v1/models/version` endpoint to expose model versions via API.

## Prometheus Alerts for ML

### High Latency Alert

**Alert**: `HighLLMLatency`
**Condition**: P95 latency > 5s for 5 minutes
**Action**: Check model performance and infrastructure

### High Error Rate Alert

**Alert**: `HighLLMErrorRate`
**Condition**: Error rate > 10% for 2 minutes
**Action**: Check logs for error details and model availability

### Model Down Alert

**Alert**: `LLMModelDown`
**Condition**: Model service unavailable > 2 minutes
**Action**: Check service health and logs

### Model Drift Alert

**Alert**: `LLMModelDrift`
**Condition**: Latency increase > 2s compared to baseline
**Action**: Recommends retrain/investigation pipeline

## Grafana Dashboard: ML Service Metrics

**Location**: `grafana/dashboards/ml-service-metrics.json`

**Key Panels**:
1. Model latency (P50, P95, P99)
2. Request volume (predictions/min)
3. Token generation rate
4. Error rates by type
5. Model version tracking
6. Drift detection

## Drift Detection

### Current Implementation

- **Latency drift**: Compares current P95 latency to 6-hour baseline
- **Alert threshold**: > 2s increase triggers alert

### Future Enhancements

1. **Response length distribution**: Track changes in output length
2. **Quality score drift**: Monitor quality metric changes
3. **Statistical tests**: Implement KS-test or similar for distribution changes
4. **Automated retraining**: Trigger retrain pipeline on drift detection

## MLflow Integration (Future)

### Planned Features

1. **Model Versioning**: Track model versions in MLflow
2. **Experiment Tracking**: Log prompt variations, temperature effects
3. **Artifact Storage**: Store prompts, sample outputs
4. **Model Comparison**: A/B testing and model comparison

## Monitoring Best Practices

1. **Track all inference calls**: Log every LLM request
2. **Monitor latency distributions**: Use histograms, not averages
3. **Track token usage**: Monitor costs and rate limits
4. **Version models**: Always track deployed model version
5. **Alert on drift**: Set up alerts for performance degradation
6. **Baseline metrics**: Establish baseline metrics for comparison

## References

- [ML Monitoring Best Practices](https://ml-ops.org/content/ml-monitoring)
- [Model Drift Detection](https://www.evidentlyai.com/blog/ml-monitoring)

