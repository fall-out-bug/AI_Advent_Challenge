# Stage 03_02 Remediation Backlog

## P0 — Blockers (must land before Stage 03_02 exit)
1. **Ship Prometheus exporters for MCP, unified worker, and modular reviewer**
   - *Current state*: No `/metrics` endpoint except MCP placeholder; modular reviewer metrics unexposed.
   - *Definition of done*: `/metrics` returns MCP request counters, latency histogram, review pipeline duration, worker throughput metrics; Prometheus scrape succeeds locally.
   - *Dependencies*: `metrics_inventory.json`, SLO catalogue.
   - *Effort*: 5 dev-days.
2. **Replace invalid alert rules and enable Alertmanager routing**
   - *Current state*: Alerts reference non-existent metrics, Alertmanager disabled.
   - *Definition of done*: Alert expressions validated via `promtool`; Alertmanager endpoint configured with Slack/Telegram channel; runbook links embedded in annotations.
   - *Effort*: 3 dev-days.
3. **Establish GitHub Actions pipeline for observability verification**
   - *Current state*: No CI; manual scripts only.
   - *Definition of done*: Workflow runs lint/tests plus Prometheus rule lint, dashboard JSON validation, smoke tests for `/health` & `/metrics`.
   - *Effort*: 4 dev-days.

## P1 — High Priority (deliver within Stage 03_02)
1. **Unify logging stack and introduce structured context propagation**
   - Merge duplicate logger implementations, enforce `get_logger`, add request_id/user_id context, ensure secrets masked.
   - Deliver sample Kibana/Loki queries and logging RFC.
   - Effort: 4 dev-days.
2. **Select and wire log aggregation backend**
   - Decision between Loki vs. ELK; provision environment, update docker-compose, document retention and access.
   - Effort: 5 dev-days (shared with Ops).
3. **Publish SLO dashboards and error budget panels**
   - Add Grafana dashboard per SLO with burn-down visualisation; include auto-generated CSV export.
   - Effort: 3 dev-days.
4. **Implement baseline audit logging for privileged actions**
   - Record MCP tool invocations, admin CLI operations, authentication events with traceable IDs; define retention.
   - Effort: 3 dev-days (with Security).

## P2 — Nice-to-Have (schedule if time remains)
1. **Automated configuration drift detection**
   - Script comparing repo `prometheus.yml`/Grafana dashboards with deployed versions; alert on drift.
2. **Synthetic monitoring canaries**
   - Periodic job triggering MCP review, bot digest, and verifying outputs; feed metrics into Prometheus.
3. **Tracing rollout (OpenTelemetry PoC)**
   - Instrument MCP FastAPI and HTTPX clients, export to Jaeger/Tempo with 10% sampling.

## Tracking & Ownership
- Backlog entries mirrored as GitHub issues with EP03 label.
- Review progress in weekly EP03 sync; adjust priorities once instrumentation groundwork lands.

