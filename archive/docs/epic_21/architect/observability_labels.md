# Observability Labels · Epic 21

**Purpose**: Mandatory Prometheus labels for new Epic 21 metrics.

**Status**: Ready for Stage 21_03 implementation

---

## Label Standards

### General Rules

1. **Mandatory labels** (all metrics):
   - `operation`: Type of operation
   - `status`: `success` | `error`

2. **Conditional labels**:
   - `error_type`: Required only when `status=error`
   - `backend`: For storage metrics (identifies storage type)
   - `component`: For decomposed use cases

3. **Cardinality limits**:
   - ❌ Never use `user_id`, `student_id`, `session_id` as labels (unbounded)
   - ✅ Use for structured logs (Loki), not metrics

4. **Naming convention**:
   - Prefix: `<component>_<metric_name>`
   - Suffix: `_total` (counters), `_seconds` (histograms/summaries), `_bytes` (gauges)

---

## Dialog Context Repository

### Metrics

```prometheus
# Operation counter
dialog_context_repository_operations_total{
    operation="get|save|delete|list",
    status="success|error",
    error_type=""  # Only if status=error
}

# Latency histogram
dialog_context_repository_latency_seconds{
    operation="get|save|delete|list"
}
```

### Label Values

| Label | Values | Required | Description |
|-------|--------|----------|-------------|
| `operation` | `get`, `save`, `delete`, `list` | ✅ Yes | Repository operation type |
| `status` | `success`, `error` | ✅ Yes | Operation outcome |
| `error_type` | `not_found`, `connection_error`, `timeout`, `validation_error` | ⚠️ If error | Error category |

### Exposition

- **Process**: Butler bot
- **Port**: 8001
- **Endpoint**: `/metrics`
- **Scrape interval**: 15s

### Example

```python
# src/infrastructure/repositories/mongo_dialog_context_repository.py

from prometheus_client import Counter, Histogram

operations_total = Counter(
    'dialog_context_repository_operations_total',
    'Dialog context repository operations',
    ['operation', 'status', 'error_type']
)

latency_seconds = Histogram(
    'dialog_context_repository_latency_seconds',
    'Dialog context repository operation latency',
    ['operation'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

class MongoDialogContextRepository:
    async def get_by_session(self, session_id: str):
        with latency_seconds.labels(operation='get').time():
            try:
                result = await self._collection.find_one(...)
                operations_total.labels(operation='get', status='success', error_type='').inc()
                return result
            except Exception as e:
                error_type = self._classify_error(e)
                operations_total.labels(operation='get', status='error', error_type=error_type).inc()
                raise
```

---

## Homework Review Service

### Metrics

```prometheus
# Request counter
homework_review_service_requests_total{
    operation="list_commits|request_review|get_status",
    status="success|error",
    error_type=""
}

# Latency histogram
homework_review_service_latency_seconds{
    operation="list_commits|request_review|get_status"
}
```

### Label Values

| Label | Values | Required | Description |
|-------|--------|----------|-------------|
| `operation` | `list_commits`, `request_review`, `get_status` | ✅ Yes | Service operation |
| `status` | `success`, `error` | ✅ Yes | Operation outcome |
| `error_type` | `api_timeout`, `api_error`, `rate_limit`, `not_found` | ⚠️ If error | Error category |

### Exposition

- **Process**: Background worker
- **Port**: 8002
- **Endpoint**: `/metrics`

---

## Storage Adapter

### Metrics

```prometheus
# Operation counter
review_archive_storage_operations_total{
    operation="save_new|save_previous|save_logs|open|purge",
    status="success|error",
    backend="local_fs|s3",
    error_type=""
}

# Bytes written gauge
review_archive_storage_bytes_written{
    backend="local_fs|s3"
}

# Checksum failure counter
review_archive_storage_checksum_failures_total{
    backend="local_fs|s3"
}

# Latency histogram
review_archive_storage_latency_seconds{
    operation="save_new|save_previous|save_logs|open",
    backend="local_fs|s3"
}
```

### Label Values

| Label | Values | Required | Description |
|-------|--------|----------|-------------|
| `operation` | `save_new`, `save_previous`, `save_logs`, `open`, `purge` | ✅ Yes | Storage operation |
| `status` | `success`, `error` | ✅ Yes | Operation outcome |
| `backend` | `local_fs`, `s3` | ✅ Yes | Storage backend type ← **as requested by Tech Lead** |
| `error_type` | `checksum_failed`, `disk_full`, `permission_error`, `av_scan_reject`, `size_limit` | ⚠️ If error | Error category |

### Exposition

- **Process**: API server
- **Port**: 8000
- **Endpoint**: `/metrics`

### Example

```python
# src/infrastructure/storage/local_filesystem_storage.py

operations_total = Counter(
    'review_archive_storage_operations_total',
    'Storage operations',
    ['operation', 'status', 'backend', 'error_type']
)

bytes_written = Gauge(
    'review_archive_storage_bytes_written',
    'Total bytes written to storage',
    ['backend']
)

class LocalFileSystemStorage:
    async def save_new(self, student_id, assignment_id, filename, data):
        with latency_seconds.labels(operation='save_new', backend='local_fs').time():
            try:
                # ... save logic ...
                bytes_written.labels(backend='local_fs').inc(len(data))
                operations_total.labels(
                    operation='save_new',
                    status='success',
                    backend='local_fs',
                    error_type=''
                ).inc()
                return artifact
            except StorageSizeError as e:
                operations_total.labels(
                    operation='save_new',
                    status='error',
                    backend='local_fs',
                    error_type='size_limit'
                ).inc()
                raise
```

---

## Use Case Decomposition

### Metrics

```prometheus
# Use case error counter
review_submission_use_case_errors_total{
    component="rate_limiter|log_pipeline|publisher|orchestrator",
    error_type=""
}

# Rate limit hits
review_submission_rate_limit_hits_total

# Log analysis duration
review_submission_log_analysis_duration_seconds

# Overall use case duration
review_submission_duration_seconds{
    status="success|error"
}
```

### Label Values

| Label | Values | Required | Description |
|-------|--------|----------|-------------|
| `component` | `rate_limiter`, `log_pipeline`, `publisher`, `orchestrator` | ✅ Yes | Use case component |
| `error_type` | `rate_limit_exceeded`, `parse_error`, `publish_failed`, `timeout` | ⚠️ If error | Error category |
| `status` | `success`, `error` | ✅ Yes | Overall outcome |

### Exposition

- **Process**: Background worker
- **Port**: 8002
- **Endpoint**: `/metrics`

---

## Prometheus Scrape Config

```yaml
# prometheus/prometheus.yml (Epic 21 additions)

scrape_configs:
  # Butler bot (dialog context repository)
  - job_name: 'butler_bot'
    static_configs:
      - targets: ['butler-bot:8001']
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: /metrics
  
  # API server (storage adapter)
  - job_name: 'butler_api'
    static_configs:
      - targets: ['butler-api:8000']
    scrape_interval: 15s
    metrics_path: /metrics
  
  # Background worker (homework service, use case)
  - job_name: 'butler_worker'
    static_configs:
      - targets: ['butler-worker:8002']
    scrape_interval: 15s
    metrics_path: /metrics
```

---

## Grafana Dashboard Panels

### Panel 1: Dialog Context Repository Health

```promql
# Operation rate
rate(dialog_context_repository_operations_total[5m])

# Error rate
rate(dialog_context_repository_operations_total{status="error"}[5m])

# Latency (p95)
histogram_quantile(0.95, rate(dialog_context_repository_latency_seconds_bucket[5m]))
```

### Panel 2: Storage Adapter Health

```promql
# Operations by backend
sum by (backend) (rate(review_archive_storage_operations_total[5m]))

# Checksum failures
rate(review_archive_storage_checksum_failures_total[5m])

# Bytes written by backend
review_archive_storage_bytes_written

# Latency by backend
histogram_quantile(0.95, rate(review_archive_storage_latency_seconds_bucket{backend="local_fs"}[5m]))
```

---

## Alert Rules

### Alert 1: High Error Rate

```yaml
# prometheus/alerts/epic21_alerts.yml

groups:
  - name: epic21
    interval: 30s
    rules:
      - alert: DialogContextRepositoryHighErrorRate
        expr: |
          rate(dialog_context_repository_operations_total{status="error"}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
          epic: '21'
        annotations:
          summary: "Dialog context repository error rate >5%"
          description: "Error rate: {{ $value | humanizePercentage }}"
```

### Alert 2: Storage Checksum Failures

```yaml
- alert: StorageChecksumFailures
  expr: |
    rate(review_archive_storage_checksum_failures_total[5m]) > 0
  for: 1m
  labels:
    severity: critical
    epic: '21'
  annotations:
    summary: "Storage checksum failures detected"
    description: "Possible data corruption or malicious uploads"
```

---

## Structured Logging (Loki)

For high-cardinality data (user_id, student_id, etc.), use structured logs:

```python
# Use logger, not metrics
logger.info(
    "Dialog context saved",
    extra={
        "operation": "save",
        "session_id": session_id,  # ← OK in logs, not metrics
        "user_id": user_id,
        "trace_id": trace_id,
    }
)
```

**Query in Grafana Loki**:
```logql
{job="butler_bot"} |= "Dialog context saved" | json | user_id="alice"
```

---

## Acceptance Criteria

- [ ] All metrics use mandatory labels (`operation`, `status`)
- [ ] `backend` label present in storage metrics
- [ ] No high-cardinality labels (user_id, session_id) in metrics
- [ ] Prometheus scrape configs updated
- [ ] Grafana dashboards created
- [ ] Alert rules defined
- [ ] Team trained on label usage

---

**Document Owner**: EP21 DevOps + Architect  
**Status**: Ready for Stage 21_03  
**Last Updated**: 2025-11-11

