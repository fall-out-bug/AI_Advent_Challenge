# Stage 03_01 Observability Gap Report

## Executive Summary
- Prometheus targets cover only MCP, Butler bot, and two worker placeholders; modular reviewer, unified worker, and API surfaces lack `/metrics` endpoints, leaving critical flows unobserved.
- Alert rules reference non-existent Prometheus series (`mcp_requests_total`, `http_requests_total`, `llm_error_rate_total`) and Alertmanager is disabled, so no actionable alerting exists today.
- Structured logging is partially adopted: Butler flows enrich context, but MCP, workers, and modular reviewer emit free-form strings with no correlation IDs or aggregation pipeline.
- CI/CD automation does not execute observability checks; there are no GitHub Actions, no smoke probes post-deploy, and no validation that metrics or dashboards stay healthy.
- Documentation outlines environment setup but misses runbooks, escalation paths, and compliance guidance; no SLO/SLI catalogue exists.

## Current Observability Footprint
- **Prometheus**: `prometheus/prometheus.yml` defines five static scrape jobs (MCP server, Butler bot, summary worker, post fetcher, mistral-chat, self). Only MCP server and Butler bot expose real `/metrics`; worker endpoints are aspirational.
- **Metrics Instrumentation**:
  - Butler bot publishes counters/histograms in `src/infrastructure/metrics/butler_metrics.py`.
  - Day 12 worker metrics (`post_fetcher_*`, `pdf_generation_*`, `bot_digest_*`) live in `src/infrastructure/monitoring/prometheus_metrics.py`.
  - Modular reviewer package defines counters/histograms under `packages/multipass-reviewer/.../monitoring/metrics.py`, but results stay in-process and are not exported through an HTTP endpoint.
- **Grafana**: three dashboards (app health, ML service metrics, post/PDF) expect HTTP and MCP metrics that do not exist.
- **Logging**: `src/infrastructure/logging/get_logger` wraps stdlib logging; Butler bot augments logs with contextual `extra`. A parallel `StructuredLogger` exists in `src/infrastructure/monitoring/logger.py` and is used by ad-hoc scripts only.
- **Alerting**: `prometheus/alerts.yml` contains 24 rules grouped by component, yet Alertmanager integration is commented out and most expressions reference missing metrics.
- **Operational Automation**: Make targets (`make test`, `make day-12-metrics`, QA smoke scripts) run manually; no CI workflows enforce them.
- **Documentation**: `docs/MONITORING.md` and `docs/specs/operations.md` describe stack bootstrap. Runbooks, SLOs, and compliance/audit requirements are absent.

## Gap Analysis

### Metrics & Dashboards
- No scrape targets or exporters for `unified-task-worker`, modular reviewer API, CLI backoffice, or shared SDK clients, so review throughput and queue latency are unknown.
- `prometheus/prometheus.yml` lists summary worker and post fetcher endpoints, but neither container exposes `/metrics`; instrumentation for `summary_worker` is missing entirely.
- Grafana panels rely on `http_requests_total` and `http_request_duration_seconds`, none of which are produced anywhere in the codebase.
- Modular reviewer histograms are not registered with a Prometheus registry that the MCP server exposes; end-to-end review latency tracking is missing.
- No business metrics (e.g., reviews completed, digests delivered, backlog depth) exist to support product SLOs.

### Logging
- MCP HTTP server, workers, and infrastructure clients log free-form strings without structured payloads or request IDs, making correlation impossible.
- Duplicate logger implementations (`src/infrastructure/logging` vs. `src/infrastructure/monitoring/logger.py`) fragment configuration and handler setup.
- No log aggregation stack (ELK/Loki/Cloud provider); Docker stdout is the only sink, so retention, querying, and incident triage rely on container logs.
- Sensitive flows (Mongo credential failures, LLM exceptions) are logged with raw error strings; there is no masking strategy for secrets or PII.

### Alerting & SLOs
- 11 alert expressions reference non-existent metrics (`mcp_requests_total`, `mcp_request_duration_seconds_bucket`, `llm_error_rate_total`, `butler_messages_total` labels not emitted as expected), so alerts would never trigger.
- Alertmanager targets are commented out, and there is no routing/notification configuration; alerts cannot reach humans.
- No SLO/SLI definitions are documented; Grafana dashboards do not highlight error budgets or SLO attainment.
- Error budget math, burn-rate policies, and alert priority classification are missing, increasing risk of alert fatigue when instrumentation arrives.

### Tracing & Context Propagation
- No OpenTelemetry or equivalent tracing libraries are installed or initialised; only the modular reviewer logger carries a local `trace_id`.
- Cross-service calls (Bot → MCP → LLM → Mongo) cannot be correlated; `X-Request-ID` or similar headers are not propagated.
- Without spans or correlation IDs, diagnosing latency spikes or partial failures requires log scraping and manual reconstruction.

### Operational Automation
- Repository lacks `.github/workflows/` or any CI definition; observability regressions are not caught automatically.
- Makefile and `scripts/quality/run_all_checks.sh` provide lint/test/security checks, but none validate Prometheus scrape targets, dashboard JSON, or alert syntax.
- No synthetic monitors or smoke tests run post-deploy (e.g., HTTP ping, MCP tool invocation, digest flow).
- No automation verifies configuration drift between repo manifests and deployed Prometheus/Grafana assets.

### Documentation & Compliance
- `docs/specs/operations.md` references future runbooks but omits actionable steps, escalation chains, or on-call expectations.
- No compliance requirements (GDPR, audit logging) are documented beyond a prompt in `stage_03_01.md`; audit logging strategy is undefined.
- SLO/SLA expectations per component are not captured anywhere; teams lack guidance for acceptable latency or availability.
- There is no risk register entry capturing observability blind spots; prior epics do not track observability debt.

## Recommended Next Steps (Stage 03_02 Input)
1. **Instrumentation**
   - Add Prometheus exporters for MCP server, unified worker, and modular reviewer, ensuring metrics in `metrics_inventory.json` marked `missing`/`partial` become available.
   - Register modular reviewer histograms with the MCP FastAPI app and expose them on `/metrics`.
2. **Alerting & Dashboards**
   - Replace placeholder alert expressions with metrics that exist; wire Alertmanager and notification channels.
   - Create dashboards for review pipeline and MCP tool performance with SLO indicators.
3. **Logging & Tracing**
   - Collapse duplicate logger implementations, enforce `get_logger`, and add structured context (request_id, user_id) across layers.
   - Introduce OpenTelemetry instrumentation for FastAPI (MCP), HTTPX (LLM), and worker tasks; export traces to a lightweight backend (Jaeger/Loki tempo).
4. **Operations Automation**
   - Add CI workflows executing lint/tests plus observability checks (PromQL rule validation, dashboard JSON lint).
   - Add smoke tests that hit `/health` and `/metrics`, fail builds when endpoints regress.
5. **Documentation & Governance**
   - Publish SLO catalogue and runbooks, including escalation and alert response steps.
   - Define audit logging requirements (who accessed what, retention), aligning with security policy.

## Decisions & Open Questions
- **Tracing scope**: proceed with option **b)** — defer full OpenTelemetry rollout to Stage 03_02 while budgeting design time during Stage 03_01_→03_02 handoff.
- **Compliance requirements**: adopt option **b)** — implement baseline audit logging for privileged actions (MCP tool invocations, admin commands) during Stage 03_02, with a follow-up assessment for deeper compliance.
- **Log aggregation**: align with option **d)** — select aggregation stack in Stage 03_02 after comparing Loki vs. ELK; current findings highlight requirements but stop short of committing to a vendor.

## Evidence Collected
- Metrics definitions and gaps: `docs/specs/epic_03/metrics_inventory.json`
- Prometheus and alerts configuration: `prometheus/prometheus.yml`, `prometheus/alerts.yml`
- Logging implementations: `src/infrastructure/logging/__init__.py`, `src/infrastructure/monitoring/logger.py`, `src/presentation/mcp/http_server.py`
- Dashboard expectations: `grafana/dashboards/app-health.json`, `grafana/dashboards/ml-service-metrics.json`, `grafana/dashboards/post-pdf-metrics.json`
- Operational docs: `docs/MONITORING.md`, `docs/specs/operations.md`, `docs/TROUBLESHOOTING.md`

