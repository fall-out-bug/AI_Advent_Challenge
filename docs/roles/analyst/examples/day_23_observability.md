# Day 23 · Observability Self-Observation Example

**Purpose:** Demonstrate how Analyst agents use Day 23 observability metrics to self-verify handoff quality and trace requirement gathering sessions.

## Scenario

Analyst completes requirement gathering for Epic 23 (Observability & Benchmark Enablement) and needs to:
1. Verify handoff quality using telemetry metadata
2. Include observability evidence in handoff JSON
3. Self-observe workflow using Prometheus metrics

## Example Handoff JSON with Observability Metadata

```json
{
  "metadata": {
    "epic_id": "EP23",
    "analyst_version": "v1.0",
    "timestamp": "2025-11-16T13:00:00Z",
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "stage_id": "TL-04",
    "latency_ms": 2450,
    "observability": {
      "metrics_endpoint": "http://localhost:8004/metrics",
      "structured_logs_total": 127,
      "benchmark_export_duration_seconds": {"exporter": "digests", "p95": 12.5},
      "shared_infra_bootstrap_status": {"mongo": 1, "mock_services": 1},
      "rag_variance_ratio": 0.23
    }
  },
  "requirements": [
    {
      "id": "REQ-EP23-001",
      "text": "System must expose Prometheus metrics on /metrics endpoints for all runtimes",
      "type": "observability",
      "priority": "high",
      "acceptance_criteria": [
        "MCP HTTP server /metrics returns non-zero values for structured_logs_total",
        "Butler bot metrics_server exposes shared registry metrics",
        "CLI backoffice commands emit benchmark_export_duration_seconds histogram"
      ],
      "telemetry_evidence": {
        "promql_query": "rate(structured_logs_total{service=~\"mcp|butler|cli\"}[5m])",
        "expected_min_value": 0.1,
        "verification_command": "curl http://localhost:8004/metrics | grep structured_logs_total"
      }
    },
    {
      "id": "REQ-EP23-002",
      "text": "Loki alert rules must detect log volume spikes",
      "type": "observability",
      "priority": "medium",
      "acceptance_criteria": [
        "Prometheus alerts.yml includes LokiHighErrorRate rule",
        "Alert fires when log error rate > 5% for 5 minutes",
        "Grafana dashboard visualizes structured_logs_total by service/level"
      ],
      "telemetry_evidence": {
        "alert_rule_file": "prometheus/alerts.yml",
        "loki_alert_group": "loki_alerts"
      }
    }
  ],
  "quality_metrics": {
    "total_exchanges": 12,
    "clarity_score": 0.92,
    "trace_coverage": 1.0,
    "telemetry_verification": "passed"
  }
}
```

## Self-Observation Workflow

### Step 1: Query Metrics During Requirement Gathering

```bash
# Verify metrics endpoint is accessible
curl http://localhost:8004/metrics | grep structured_logs_total

# Expected output:
# structured_logs_total{service="analyst",level="info"} 127.0
```

### Step 2: Include Telemetry Evidence in Handoff

Analyst includes observability metadata in handoff JSON:
- `trace_id`: Links requirement gathering session to downstream stages
- `latency_ms`: Measures requirement gathering efficiency
- `observability.metrics_endpoint`: Enables Architect/Tech Lead to verify metrics

### Step 3: Verify Handoff Quality Using PromQL

```promql
# Check structured logs volume during requirement gathering
rate(structured_logs_total{service="analyst",epic_id="EP23"}[5m])

# Verify benchmark export readiness
histogram_quantile(0.95, rate(benchmark_export_duration_seconds_bucket[5m]))

# Check shared infra bootstrap status
shared_infra_bootstrap_status{step="mongo"}
```

## Integration with Architect/Tech Lead

### Architect Uses Observability Metadata

Architect receives handoff JSON with `observability.telemetry_evidence` and:
1. Verifies metrics endpoint accessibility: `curl {metrics_endpoint}`
2. Queries PromQL to validate acceptance criteria thresholds
3. Links trace_id to implementation commits via MongoDB audit trail

### Tech Lead Uses Telemetry for Acceptance

Tech Lead reviews acceptance matrix and:
1. Uses `trace_id` from Analyst handoff to find related implementation PRs
2. Verifies `observability.shared_infra_bootstrap_status` for CI readiness
3. Checks `observability.benchmark_export_duration_seconds` for dataset completeness

## MongoDB Audit Trail Query

```javascript
// Query MongoDB for Analyst requirement gathering session
db.audit_events.find({
  trace_id: "550e8400-e29b-41d4-a716-446655440000",
  epic_id: "EP23",
  stage_id: "TL-04"
}).sort({timestamp: 1})

// Returns audit trail linking requirements to implementation
```

## Grafana Dashboard Integration

Analyst can visualize own workflow quality using Grafana:
- **Panel 1**: `structured_logs_total{service="analyst"}` - Log volume during requirement gathering
- **Panel 2**: `histogram_quantile(0.95, analyst_handoff_duration_seconds_bucket[5m])` - Handoff latency
- **Panel 3**: `analyst_requirements_total{epic_id="EP23"}` - Requirements count per epic

## Benefits

1. **Self-Verification**: Analyst can verify handoff quality using own telemetry
2. **Traceability**: `trace_id` links requirements to implementation commits
3. **Quality Metrics**: `latency_ms` and `clarity_score` enable continuous improvement
4. **Evidence-Based**: Telemetry evidence proves acceptance criteria are met

## Related Documentation

- `docs/operational/observability_labels.md` - Label taxonomy for Epic 23 metrics
- `docs/specs/epic_23/tech_lead_plan.md` - TL-04 observability instrumentation requirements
- `docs/operational/handoff_contracts.md` - Handoff JSON schema with observability metadata
