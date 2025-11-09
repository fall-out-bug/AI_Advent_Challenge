# Operations Guide

## 1. Shared Infrastructure Overview
| Service | Host Endpoint | Docker Endpoint | Notes |
|---------|---------------|-----------------|-------|
| MongoDB | `mongodb://admin:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin` | `shared-mongo:27017` | Credentials sourced from `~/work/infra/.env.infra`. |
| Prometheus | `http://127.0.0.1:9090` | `shared-prometheus:9090` | Readiness at `/-/ready`, metrics at `/metrics`. |
| LLM API (Qwen) | `http://127.0.0.1:8000` | `llm-api:8000` | OpenAI-compatible `/v1/chat/completions`. |
| Grafana | `http://127.0.0.1:3000` | `grafana:3000` | Login `admin`, password from `.env.infra`. |

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
   poetry run python scripts/test_review_system.py --metrics
   poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py -q
   ```

4. **Access dashboards**
   - Grafana: `http://127.0.0.1:3000` (admin / password from `.env.infra`)
   - Prometheus: `http://127.0.0.1:9090`

## 3. Validation Commands
- Health check: `poetry run python scripts/test_review_system.py --metrics --report json`
- Unit tests: `poetry run pytest src/tests/unit -q`
- Integration (shared infra): `poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py -q`
- Full suite (expected failures documented in specs): `poetry run pytest -q`

## 4. Observability
- Metrics exported via Prometheus client; structured logger attaches contextual
  fields (e.g., `trace_id`).
- For MCP HTTP server, `/metrics` endpoint returns Prometheus format or 404 when
  client unavailable.
- Plan to register custom jobs in `prometheus/prometheus.yml` once modules are
  consolidated (tracked in EP03).

## 5. Known Issues
- Several legacy tests expect unauthenticated Mongo; they require fixture
  updates to use `TEST_MONGODB_URL` (Stage 00_01 deliverable).
- Lint target `make lint` currently fails due to pre-existing long lines and
  unused variables; remediation tracked for future epic.
- PDF generation tests rely on `weasyprint`; ensure dependency versions match
  `pyproject`. Failures should be mocked or executed in environment with
  required native libs.

## 6. Runbooks (To Be Expanded)
- Start shared infra (`./scripts/start-infra.sh` in infra repo).
- Restart LLM API container (`docker compose -f llm/docker-compose.yml up -d`).
- Rotate credentials (update `.env.infra`, restart consumers, commit masked
  changes in ops docs).
