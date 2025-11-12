# Stage 21_03 · Observability Upgrade Plan

## Objectives
- Reflect refactored services (storage adapter, modular review pipeline) in monitoring stack.
- Ensure alerting thresholds align with new architecture and operational SLIs.
- Document runbooks and dashboard updates for quick adoption.

## Metrics Enhancements (see `architect/observability_labels.md` for label conventions)
- **Storage Adapter**
  - `review_storage_write_seconds` (histogram)
  - `review_storage_write_failures_total`
  - `review_storage_bytes_written_total`
- **Log Analysis Pipeline**
  - `review_pass4_duration_seconds`
  - `review_pass4_errors_total`
- **Queue Throughput**
  - `review_tasks_enqueued_total`
  - `review_tasks_completed_total`
  - `review_tasks_failed_total`

## Prometheus Configuration Steps
1. Update `prometheus/prometheus.yml` scrape jobs with new exporters or endpoints.
2. Add recording rules for p95 storage latency and error ratios.
3. Define alerts:
   - `StorageHighLatency`: p95 > 2s for 5 minutes.
   - `StorageWriteFailures`: error ratio > 5% over 10 minutes.
   - `Pass4FailureSpike`: pass4 errors > 3 per 10 minutes.
4. Validate configs locally via `promtool check config`.

## Grafana Dashboards
- Create new panels on review pipeline dashboard:
  - Storage write latency/throughput.
  - Pass 4 processing time and error distribution.
  - Queue depth (if available from repository metrics).
- Update SLO dashboard thresholds in line with operations guide.
- Provide annotations for deployment windows (Stage 21 milestones).

## Logging Updates
- Ensure structured logger includes `storage_path`, `checksum`, `task_id`, `trace_id`.
- Configure Loki queries for storage failures and pass 4 anomalies.
- Update alerting runbook with examples of Grafana + Loki correlation queries.

## Incident Response
- Extend `docs/specs/epic_03/alerting_runbook.md` with:
  - Storage failure troubleshooting (permissions, disk space, S3 credentials).
  - Pass 4 analysis recovery steps (retry, fallback to manual review).
- Add rollback instructions for new storage adapter (feature flag toggle).

## Validation Checklist
- [ ] `make day-12-up` stack emits new metrics.
- [ ] Prometheus alerts fire in staging when thresholds exceeded.
- [ ] Grafana dashboards reviewed and approved by operations owner.
- [ ] Logging fields verified via Loki queries.
- [ ] Runbooks updated and linked from README/Operations documentation.


