# Alerting Runbook

This runbook documents the alerts defined in `prometheus/alerts.yml`, the
investigation workflow, and recommended remediation steps. All timestamps are
UTC unless stated otherwise.

## Unified Task Worker Alerts

### UnifiedWorkerDown
- **Trigger**: `up{job="unified-task-worker"} == 0` for 2 minutes.
- **Investigation**:
  1. `docker compose -f docker-compose.butler.yml ps unified-task-worker`
  2. Check metrics endpoint: `curl -sf http://unified-task-worker:9092/`
  3. Inspect worker logs: `docker compose -f docker-compose.butler.yml logs unified-task-worker`
- **Remediation**:
  - Restart container: `docker compose -f docker-compose.butler.yml restart unified-task-worker`
  - If restart fails, validate environment variables (`TELEGRAM_BOT_TOKEN`, `MCP_SERVER_URL`).
  - Escalate to Ops if container enters crash loop after two restarts.

### UnifiedWorkerHighErrorRate
- **Trigger**: Error tasks >10% of total tasks across 10 minutes.
- **Investigation**:
  1. Query failed tasks: `promql` → `rate(unified_worker_tasks_total{status="error"}[5m])`
  2. Review `unified-task-worker` logs for stack traces.
  3. Check queue depth (`unified_worker_queue_depth`) to identify backlog.
- **Remediation**:
  - If failures tied to MCP, validate MCP `/health`.
  - For Telegram failures, confirm bot permissions and rate limits.
  - Open incident if failure rate remains >10% for 30 minutes.

### UnifiedWorkerBacklog
- **Trigger**: Review queue depth >50 tasks for 15 minutes.
- **Investigation**:
  1. Confirm backlog via Mongo: `db.long_tasks.countDocuments({status: "queued", task_type: "CODE_REVIEW"})`
  2. Inspect worker logs for rate limiting or external dependency delays.
  3. Verify MCP and LLM endpoints latency.
- **Remediation**:
  - Scale vertical: increase worker CPU/memory (update compose resources).
  - Scale horizontal: run additional worker instance (`docker compose ... up -d unified-task-worker-scale-2`).
  - Notify EP03 lead if backlog persists >1h.

### UnifiedWorkerHighLatency
- **Trigger**: P95 task duration >300s for 10 minutes.
- **Investigation**:
  1. Identify slow task type using Prometheus label filters.
  2. Review logs for slow external calls (MCP, LLM, Mongo).
  3. Check recent deployments to reviewer, MCP, or worker config.
- **Remediation**:
  - Increase `REVIEW_LLM_TIMEOUT` or queue batch size if necessary.
  - Investigate external API latency; coordinate with EP01/EP02 teams.
  - Record incident if SLA breach >30 minutes.

## MCP Server Alerts

### MCPServerDown
- **Trigger**: `up{job="mcp-server"} == 0` for 2 minutes.
- **Investigation**:
  1. `docker compose -f docker-compose.butler.yml ps mcp-server`
  2. Check `/health`: `curl -sf http://mcp-server:8004/health`
  3. Inspect logs: `docker compose ... logs mcp-server`
- **Remediation**:
  - Restart service: `docker compose ... restart mcp-server`
  - Validate Mongo/LLM connectivity (see `/config`).
  - Escalate if repeated restarts fail within 15 minutes.

### MCPServerHighErrorRate
- **Trigger**: Error requests >10% of total over 5 minutes.
- **Investigation**:
  1. Query failing tools: `rate(mcp_requests_total{status="error"}[5m])`.
  2. Use `/tools` endpoint to verify registration.
  3. Review MCP logs for stack traces.
- **Remediation**:
  - Disable problematic tool via feature flag in MCP settings.
  - Coordinate with tool owners for fixes.
  - Inform ops chat if error rate >25% for 10 minutes.

### MCPServerHighLatency
- **Trigger**: P95 latency >5 seconds for 5 minutes.
- **Investigation**:
  1. Identify slow tools via PromQL `mcp_request_duration_seconds_bucket` filter.
  2. Check downstream services (Mongo, LLM, external APIs).
  3. Inspect worker backlog for cascading effects.
- **Remediation**:
  - Apply rate limiting or queueing for slow tools.
  - Scale MCP resources (CPU/memory) or adjust gunicorn workers.
  - Escalate if latency remains >5s for 30 minutes.

## Butler Bot Alerts

### ButlerBotDown & ButlerBotUnhealthy
- **Investigation**:
  1. Validate container: `docker compose -f docker-compose.butler.yml ps butler-bot`
  2. Check metrics endpoint: `curl -sf http://butler-bot:9091/metrics`
  3. Review logs for token expiration or network issues.
- **Remediation**:
  - Restart bot service.
  - Confirm Telegram bot token validity; rotate if expired.
  - Escalate if unresolved within 20 minutes.

### ButlerHighErrorRate / ButlerLLMUnavailable
- **Investigation**:
  1. PromQL: `rate(butler_errors_total[5m])` with `error_type` filters.
  2. Cross-check MCP and LLM availability.
  3. Review recent deployments to bot handlers.
- **Remediation**:
  - Disable failing flows via feature flags.
  - Provide status update to support channel with incident ID.

### ButlerHighLatency
- **Investigation**:
  1. Analyze handler latency via PromQL filter on `butler_message_duration_seconds_bucket`.
  2. Inspect Mongo queries and LLM calls for slow responses.
- **Remediation**:
  - Optimize handler code paths; clear caches if stale.
  - Adjust worker concurrency or apply throttling.

### ButlerMongoDBConnectionFailed
- **Investigation**:
  1. Check MongoDB connectivity from bot container (`mongo --nodb mongodb://...`).
  2. Validate credentials/environment variables.
- **Remediation**:
  - Restart bot after verifying credentials.
  - Escalate to DB operations if Mongo instance unhealthy.

### ButlerNoMessages
- **Investigation**:
  1. Confirm quiet hours schedule.
  2. Check worker backlog and MCP status for upstream issues.
- **Remediation**:
  - If unplanned, send test message to bot and monitor.
  - Alert support team if no traffic within business hours.

## Escalation Matrix

| Severity | Response Time | Primary | Secondary | Notes |
|----------|---------------|---------|-----------|-------|
| Critical | 15 minutes    | EP03 On-call | Ops Duty Officer | Initiate incident bridge, update incident channel every 15 minutes. |
| Warning  | 30 minutes    | EP03 Engineering | Ops Duty Officer | Escalate to critical if unresolved in 60 minutes. |
| Info     | 4 hours       | EP03 Engineering | - | Document in daily ops report; no paging unless escalated. |

## Notification Endpoints

Alerts are delivered via Alertmanager webhooks to the notification gateway
(`http://notification-gateway:9000/hooks/*`). The gateway fans out to Slack
channels and PagerDuty rotations. Update the gateway configuration when team
contacts change.
