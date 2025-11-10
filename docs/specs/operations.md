# Operations Guide

## 1. Shared Infrastructure Overview
| Service | Host Endpoint | Docker Endpoint | Notes |
|---------|---------------|-----------------|-------|
| MongoDB | `mongodb://admin:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin` | `shared-mongo:27017` | Credentials sourced from `~/work/infra/.env.infra`. |
| Prometheus | `http://127.0.0.1:9090` | `shared-prometheus:9090` | Readiness at `/-/ready`, metrics at `/metrics`. |
| LLM API (Qwen) | `http://127.0.0.1:8000` | `llm-api:8000` | OpenAI-compatible `/v1/chat/completions`. |
| Grafana | `http://127.0.0.1:3000` | `grafana:3000` | Login `admin`, password from `.env.infra`. |
| Loki (Logs) | `http://127.0.0.1:3100` | `loki:3100` | Backed by Promtail docker log shippers; retention 30 days. |

## 2. Environment Bootstrap
```bash
cd ~/work/infra
set -a
source .env.infra
set +a
# Optional: start monitoring / LLM stacks if not already running
```

For repository commands:
```bash
cd ~/studies/AI_Challenge
export $(grep -v '^#' ~/work/infra/.env.infra | xargs)
export MONGODB_URL="mongodb://$MONGO_USER:$MONGO_PASSWORD@127.0.0.1:27017/butler?authSource=admin"
export TEST_MONGODB_URL="$MONGODB_URL"
export LLM_URL=http://127.0.0.1:8000
export LLM_MODEL=qwen
export PROMETHEUS_URL=http://127.0.0.1:9090
export USE_MODULAR_REVIEWER=1
```

### 2.1 CI / Automation Bootstrap
- GitHub Actions jobs invoke `python scripts/ci/bootstrap_shared_infra.py --mongo-port 37017 --mock-port 19080`.
- The script starts a disposable MongoDB container plus a lightweight mock service that exposes `/health` and `/metrics` endpoints, then writes connection strings into `$GITHUB_ENV`.
- Cleanup runs via `python scripts/ci/cleanup_shared_infra.py` with `if: always()` guards.
- Local parity:
  ```bash
  poetry run python scripts/ci/bootstrap_shared_infra.py --mongo-port 37017 --mock-port 19080
  # ... run focussed tests ...
  poetry run python scripts/ci/cleanup_shared_infra.py
  ```
- Mock service implementation is in `scripts/ci/mock_shared_services.py`; extend it if new probes are required.

## 3. Day 12 Deployment Quick Start

1. **Bring up shared stack**
   ```bash
   make day-12-up
   ```
   - Starts core services (Mongo, Prometheus, Grafana, LLM API, task workers).
   - Containers join `infra_infra_app-network`; ensure host has access.

2. **Validate service health**
   ```bash
   # LLM
   curl -s http://127.0.0.1:8000/health
   # Prometheus
   curl -s http://127.0.0.1:9090/-/ready
   # Grafana
   curl -I http://127.0.0.1:3000/login
   ```

3. **Run smoke checks**
   ```bash
   poetry run python scripts/quality/test_review_system.py --metrics
   poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py -q
   ```

4. **Access dashboards**
   - Grafana: `http://127.0.0.1:3000` (admin / password from `.env.infra`)
   - Prometheus: `http://127.0.0.1:9090`

## 3. Validation Commands
- Health check: `poetry run python scripts/quality/test_review_system.py --metrics --report json`
- Unit tests: `poetry run pytest src/tests/unit -q`
- Integration (shared infra): `poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py -q`
- Backoffice CLI flows: `poetry run pytest tests/integration/presentation/cli/test_backoffice_cli.py -q`
- MCP performance guardrails: `poetry run pytest tests/legacy/src/presentation/mcp/test_performance.py -q`
- Full suite (expected failures documented in specs): `poetry run pytest -q`

## 4. Observability
- Metrics exported via Prometheus client; structured logger attaches contextual
  fields (e.g., `trace_id`).
- For MCP HTTP server, `/metrics` endpoint returns Prometheus format or 404 when
  client unavailable.
- Plan to register custom jobs in `prometheus/prometheus.yml` once modules are
  consolidated (tracked in EP03).
- SLO dashboards provisioned in Grafana (`grafana/dashboards/slo-*.json`) cover
  review pipeline, MCP server, and Butler bot components.
- Alertmanager is enabled with webhook routing via `prometheus/alertmanager.yml`
  and the runbook lives in `docs/specs/epic_03/alerting_runbook.md`.
- Loki + Promtail provide centralised log aggregation; use the Grafana Loki
  datasource for troubleshooting (`stream="audit"` for privileged operations).
- CI emits Prometheus-compatible health snapshots through the mock service; check GitHub Actions logs for `Bootstrap shared infrastructure`/`Cleanup shared infrastructure` steps.
- MCP latency thresholds enforced in CI (override via environment variables):
  | Metric | Threshold (s) | Environment variable |
  |--------|---------------|----------------------|
  | Tool discovery | 1.50 | `MCP_DISCOVERY_LATENCY_SEC` |
  | Calculator tool | 1.20 | `MCP_CALCULATOR_LATENCY_P95_SEC` |
  | Token counter (small / medium / large) | 1.10 / 1.30 / 1.60 | `MCP_TOKEN_LATENCY_SMALL_SEC`, `MCP_TOKEN_LATENCY_MEDIUM_SEC`, `MCP_TOKEN_LATENCY_LARGE_SEC` |
  | Model listing | 1.20 | `MCP_MODEL_LISTING_LATENCY_SEC` |

## 5. Known Issues
- Several legacy tests expect unauthenticated Mongo; they require fixture
  updates to use `

## 5. Maintenance Windows & Procedures

### 5.1 Schedule
- **Primary window**: Saturday 02:00–06:00 UTC (low traffic, coordinated with support)
- **Emergency maintenance**: coordinate via ops chat (`#ops-shared`) and log incident ID in runbook
- **Freeze periods**: none currently defined; announce exceptions in program stand-up

### 5.2 Roles & Responsibilities
| Role | Owner | Backup | Responsibilities |
|------|-------|--------|------------------|
| EP03 Tech Lead | to be assigned | delegated engineer | Approve maintenance scope, final escalation |
| On-call Engineer | operations rotation | - | Execute checklist, own communications |
| Ops Duty Officer | shared infra team | - | Manage shared services, approve infra changes |

### 5.3 Maintenance Checklist Template
```
- [ ] Pre-maintenance: announce window, snapshot configs, verify rollback plan
- [ ] During: execute runbook steps, log deviations, monitor dashboards
- [ ] Post-maintenance: run health checks (Prometheus targets, Grafana SLOs, Loki logs)
- [ ] Communication: post summary, document lessons learned, update incident tracker
```

### 5.4 Escalation Flow
- Follow escalation matrix in `docs/specs/epic_03/alerting_runbook.md`
- Communication channels: `#ops-shared`, on-call phone bridge, program coordination thread
- Rollback authority: EP03 tech lead or delegated on-call engineer
