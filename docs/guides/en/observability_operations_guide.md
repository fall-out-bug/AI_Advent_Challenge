# Observability Operations Guide

## TL;DR
- **Stack**: Prometheus (metrics), Grafana (dashboards), Alertmanager (paging), Loki (logs), Promtail (log shippers).
- **Key Dashboards**: `slo-review-pipeline`, `slo-mcp-server`, `slo-butler-bot` (Grafana).
- **Runbook**: `docs/specs/epic_03/alerting_runbook.md` — use for investigation/remediation.
- **Daily Checks**:
  1. Grafana SLO dashboards green.
  2. Prometheus targets all `UP`.
  3. Loki logs flowing (`{service="unified-task-worker"}` query).

## What We Monitor
- **MCP Server**: `mcp_requests_total`, `mcp_request_duration_seconds`, error rate alerts.
- **Unified Worker**: `unified_worker_tasks_total`, queue depth, task latency.
- **Butler Bot**: Message throughput, handler latency, health gauge.
- **Review Pipeline**: End-to-end latency histogram, success rate.
- **Audit Logs**: Privileged operations via Loki label `stream="audit"`.

## Why It Matters
- **SLOs**: Review pipeline P95 ≤ 300s, MCP latency ≤ 5s, Butler error rate ≤ 10%.
- **Alerts**: Prevent incident escalation through early detection (backlog, error spikes).
- **Logging**: Structured context (request_id, actor) speeds root cause analysis.
- **Compliance**: Audit trail recorded for privileged operations.

## How to Operate
1. **Access Tooling**
   - Prometheus: `http://127.0.0.1:9090`
   - Grafana: `http://127.0.0.1:3000`
   - Loki (Grafana Explore): choose `Loki` datasource
   - Alertmanager: `http://127.0.0.1:9093`
2. **Dashboards**
   - Review pipeline: monitor latency/error budget
   - MCP: track request volume, error rate
   - Butler: monitor user-facing health
3. **Logs (Loki)**
   ```logql
   {service="mcp-server"} |= "ERROR"
   {stream="audit"} | json | line_format "{.action} {.resource} {.outcome}"
   ```
4. **Alerts**
   - Fired alerts → Alertmanager → Notification gateway
   - Follow `alerting_runbook.md` investigation/remediation steps
5. **Validation**
   - `curl http://localhost:8004/metrics | head`
   - Prometheus `/targets` page all green
   - `pytest tests/integration/observability -q`

## Quick Reference Table
| Operation | Command/URL | Expected Result |
|-----------|-------------|-----------------|
| Check review backlog | Grafana `slo-review-pipeline` | Backlog < 50 tasks |
| Query audit logs | Loki `{stream="audit"}` | Recent privileged actions listed |
| Restart worker | `docker compose -f docker-compose.butler.yml restart unified-task-worker` | Worker metrics resume |
| Validate scrape targets | Prometheus `/targets` | All jobs `UP` |
| Test alert routing | `amtool alert add test Alertname=UnifiedWorkerDown` | Notification webhook fired |
