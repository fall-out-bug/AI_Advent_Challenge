# Shared Infrastructure Playbook

## Service Matrix
| Service | Host Endpoint | Docker Endpoint | Notes |
|---------|---------------|-----------------|-------|
| MongoDB | `mongodb://admin:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin` | `shared-mongo:27017` | Credentials from `~/work/infra/.env.infra`. |
| Prometheus | `http://127.0.0.1:9090` | `shared-prometheus:9090` | Readiness at `/-/ready`, metrics at `/metrics`. |
| LLM API (Qwen) | `http://127.0.0.1:8000` | `llm-api:8000` | OpenAI-compatible `/v1/chat/completions`. |
| Grafana | `http://127.0.0.1:3000` | `grafana:3000` | Login `admin`, password from `.env.infra`. |
| Loki (Logs) | `http://127.0.0.1:3100` | `loki:3100` | Backed by Promtail log shippers; retention 30 days. |

## Environment Bootstrap
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
export MONGODB_URL="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin"
export TEST_MONGODB_URL="$MONGODB_URL"
export LLM_URL=http://127.0.0.1:8000
export LLM_MODEL=qwen
export PROMETHEUS_URL=http://127.0.0.1:9090
export USE_MODULAR_REVIEWER=1
```

## CI / Automation Bootstrap
- GitHub Actions uses `python scripts/ci/bootstrap_shared_infra.py --mongo-port 37017 --mock-port 19080`.
- Script starts disposable MongoDB plus mock service (`/health`, `/metrics`), writing connection strings into `$GITHUB_ENV`.
- Cleanup via `python scripts/ci/cleanup_shared_infra.py` guarded with `if: always()`.
- Local parity:
  ```bash
  poetry run python scripts/ci/bootstrap_shared_infra.py --mongo-port 37017 --mock-port 19080
  # ... run focussed tests ...
  poetry run python scripts/ci/cleanup_shared_infra.py
  ```
- Mock service implementation: `scripts/ci/mock_shared_services.py`; extend for new probes.

## Day 12 Deployment Quick Start
1. **Bring up shared stack**
   ```bash
   make day-12-up
   ```
   - Starts Mongo, Prometheus, Grafana, LLM API, task workers.
   - Containers join `infra_infra_app-network`; ensure host access.
2. **Validate service health**
   ```bash
   curl -s http://127.0.0.1:8000/health
   curl -s http://127.0.0.1:9090/-/ready
   curl -I http://127.0.0.1:3000/login
   ```
3. **Run smoke checks**
   ```bash
   poetry run python scripts/quality/test_review_system.py --metrics
   poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py -q
   ```
4. **Access dashboards**
   - Grafana: `http://127.0.0.1:3000` (admin/password from `.env.infra`)
   - Prometheus: `http://127.0.0.1:9090`

## Validation Commands
- Health check: `poetry run python scripts/quality/test_review_system.py --metrics --report json`
- Unit tests: `poetry run pytest src/tests/unit -q`
- Integration (shared infra): `poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py -q`
- Backoffice CLI flows: `poetry run pytest tests/integration/presentation/cli/test_backoffice_cli.py -q`
- MCP performance guardrails: `poetry run pytest tests/legacy/src/presentation/mcp/test_performance.py -q`
- Full suite (expected failures documented in specs): `poetry run pytest -q`

## Observability
- Metrics exported via Prometheus client; structured logger adds contextual fields (`trace_id`).
- MCP HTTP server exposes `/metrics` or returns 404 when client unavailable.
- Register custom jobs in `prometheus/prometheus.yml` as modules consolidate (tracked EP03).
- Grafana dashboards `grafana/dashboards/slo-*.json` cover review pipeline, MCP server, Butler bot.
- Alertmanager configured via `prometheus/alertmanager.yml`; runbook in `docs/specs/epic_03/alerting_runbook.md`.
- Loki + Promtail provide centralised logs; query with Grafana Loki datasource (`stream="audit"` for privileged ops).
- CI emits Prometheus-compatible health snapshots through mock service; see GitHub Actions logs for bootstrap/cleanup steps.
- MCP latency thresholds enforced in CI:
  | Metric | Threshold (s) | Env var |
  |--------|---------------|---------|
  | Tool discovery | 1.50 | `MCP_DISCOVERY_LATENCY_SEC` |
  | Calculator tool | 1.20 | `MCP_CALCULATOR_LATENCY_P95_SEC` |
  | Token counter (small/medium/large) | 1.10 / 1.30 / 1.60 | `MCP_TOKEN_LATENCY_SMALL_SEC`, `MCP_TOKEN_LATENCY_MEDIUM_SEC`, `MCP_TOKEN_LATENCY_LARGE_SEC` |
  | Model listing | 1.20 | `MCP_MODEL_LISTING_LATENCY_SEC` |

## Known Issues
- Several legacy tests expect unauthenticated Mongo; update fixtures to rely on
  `TEST_MONGODB_URL` credentials instead of direct localhost access.

## Maintenance Windows & Procedures
### Schedule
- **Primary window**: Saturday 02:00–06:00 UTC (low traffic, coordinated with support).
- **Emergency maintenance**: coordinate via ops chat (`#ops-shared`), log incident ID.
- **Freeze periods**: none defined; announce exceptions in program stand-up.

### Roles & Responsibilities
| Role | Owner | Backup | Responsibilities |
|------|-------|--------|------------------|
| EP03 Tech Lead | to be assigned | delegated engineer | Approve maintenance scope, final escalation |
| On-call Engineer | operations rotation | - | Execute checklist, own communications |
| Ops Duty Officer | shared infra team | - | Manage shared services, approve infra changes |

### Maintenance Checklist Template
```
- [ ] Pre-maintenance: announce window, snapshot configs, verify rollback plan
- [ ] During: execute runbook, log deviations, monitor dashboards
- [ ] Post-maintenance: run health checks (Prometheus targets, Grafana SLOs, Loki logs)
- [ ] Communication: post summary, document lessons learned, update incident tracker
```

### Escalation Flow
- Follow escalation matrix in `docs/specs/epic_03/alerting_runbook.md`.
- Communication channels: `#ops-shared`, on-call phone bridge, program coordination thread.
- Rollback authority: EP03 Tech Lead or delegated on-call engineer.

