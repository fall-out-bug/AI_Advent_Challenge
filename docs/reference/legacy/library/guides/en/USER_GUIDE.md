# User Guide

## Table of Contents

- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Shared Infrastructure Setup](#shared-infrastructure-setup)
- [Modular Multi-Pass Reviewer](#modular-multi-pass-reviewer)
- [Using the CLI](#using-the-cli)
- [Using the API](#using-the-api)
- [Models](#models)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Introduction

The AI Challenge platform is a Clean Architecture system for AI-assisted code
review, summarisation, and automation. It exposes a command-line interface
(CLI), REST API, and reusable reviewer package that can run against a shared
LLM/MongoDB infrastructure.

### Key Features

- **Modular Multi-Pass Reviewer**: Architecture, component, and synthesis passes
  with configurable checker presets
- **Shared Infrastructure Ready**: Works with the cross-project `infra_shared`
  network for MongoDB, Prometheus, Grafana, and Mistral
- **Multi-Agent Orchestration**: Coordinate code generation and review
  workflows
- **Token Management**: Automatic token budgeting and compression helpers
- **Observability**: Built-in health checks, structured logging, and metrics

## Quick Start

### 1. Install dependencies

```bash
make install

# Or with Poetry
echo "POETRY_VIRTUALENVS_CREATE=false" >> ~/.bashrc
poetry install --with dev
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and provide shared infrastructure URLs:

```bash
cp .env.example .env
cat >> .env <<'EOF'
MONGODB_URL=mongodb://admin:***@shared-mongo:27017/butler?authSource=admin
LLM_URL=http://llm-api:8000
LLM_MODEL=qwen
PROMETHEUS_URL=http://shared-prometheus:9090
USE_MODULAR_REVIEWER=1
EOF
```

### 3. Run migrations and services

MongoDB migrations are orchestrated from `/home/fall_out_bug/work/infra`. After
running the shared scripts and confirming the transfer, start the local stack
(without bundled databases):

```bash
make day-12-up
```

The compose file expects the external `infra_shared` network to exist.

### 4. Run health checks and smoke tests

```bash
poetry run python scripts/quality/test_review_system.py --smoke
poetry run pytest tests/integration/shared_infra -q
```

### 5. Run end-to-end review pipeline

```bash
USE_MODULAR_REVIEWER=1 \
TEST_MONGODB_URL="$MONGODB_URL" \
LLM_URL="$LLM_URL" \
LLM_MODEL="${LLM_MODEL:-qwen}" \
poetry run pytest tests/e2e/test_review_pipeline.py
```

All three scenarios should pass. If MongoDB or the LLM is unreachable the tests
skip with a helpful message.

## Shared Infrastructure Setup

The project consumes shared MongoDB, Prometheus, Grafana, and Mistral services.

1. Join containers to the external Docker networks:
   - `infra_shared_network` (application layer, Grafana/Prometheus/LLM)
   - `infra_infra_db-network` (MongoDB/Redis/Postgres)
2. Update `.env` and compose files to reference the shared hostnames.
3. Use `tests/integration/shared_infra/test_shared_infra_connectivity.py` to
   verify reachability.
4. Coordinate data transfer with the infra team (see `docs/shared_infra_cutover.md`).

## Modular Multi-Pass Reviewer

The modular reviewer lives in `packages/multipass-reviewer`. It can be consumed
internally or packaged for other projects.

### Enabling in AI Challenge

1. Set `USE_MODULAR_REVIEWER=1` in the environment or `.env`.
2. Ensure `ZipArchiveService` is wired in the review use case (default).
3. Optionally customise the review configuration via
   `ReviewConfigBuilder` in `src/application/services/modular_review_service.py`.

### Observability and Failover
- Pass and checker metrics are exported via `src/infrastructure/monitoring/checker_metrics.py`
- `ReviewLogger` now attaches a `trace_id` to every structured event for cross-service correlation
- Each pass returns status/error metadata; partial failures are reported but do not block report generation
- Tenacity-based retries wrap every LLM call with exponential backoff; failures are logged with the trace identifier

### Integration Tests
Run the dedicated suites when modifying the reviewer integration:
```bash
poetry run pytest tests/integration/test_modular_review_service.py -v
poetry run pytest tests/unit/application/services/test_modular_review_service.py -v
```

### Running a targeted review

```python
from multipass_reviewer.application.config import ReviewConfigBuilder
from src.application.services.modular_review_service import ModularReviewService

config = (
    ReviewConfigBuilder()
    .with_language("python")
    .with_static_analysis(["linter", "type_checker"])
    .with_framework("airflow")
    .enable_haiku()
    .build()
)

service = ModularReviewService(
    archive_service=zip_archive_service,
    diff_analyzer=diff_analyzer,
    llm_client=unified_client,
    review_config=config,
)

report = await service.review_submission(
    new_archive_path="/tmp/submissions/new.zip",
    previous_archive_path=None,
    assignment_id="HW_MODULAR",
    student_id="student-1",
)
print(report.to_markdown())
```

The modular path records Prometheus metrics for every pass and checker via
`src/infrastructure/monitoring/checker_metrics.py`.

### Packaging for reuse

```bash
cd packages/multipass-reviewer
poetry build
poetry publish --repository <private-repo>
```

A companion Docker image exposes a REST API; see `packages/multipass-reviewer/README.md`.

## Using the CLI

### Available Commands

The legacy interactive CLI has been retired. Use the backoffice CLI group instead.

```bash
# Discover available backoffice commands
poetry run python -m src.presentation.cli.backoffice.main --help

# Generate digest output for the last 24 hours
poetry run python -m src.presentation.cli.backoffice.main digest run --user-id 42 --hours 24

# Export digest to PDF
poetry run python -m src.presentation.cli.backoffice.main digest export --user-id 42 --format pdf --output reports/digest.pdf --overwrite
```

Outputs include structured tables or JSON suitable for post-processing. The backoffice CLI reuses the same shared infrastructure services (MongoDB, Prometheus, etc.).

## Using the API

Base URL defaults to `http://localhost:8000`; when deployed alongside the shared
stack use the ingress defined in `docker-compose.butler.yml`.

Key endpoints:

- `POST /api/agents/generate` – create code from a prompt
- `POST /api/agents/review` – run a review task (automatically dispatches to the
  modular reviewer when the feature flag is enabled)
- `GET /api/review-sessions/{session_id}` – fetch stored review results

Interactive docs: `http://localhost:8000/docs`.

## Models

The shared infra exposes the `llm-api` container on `http://llm-api:8000`, serving Qwen/Qwen1.5-4B-Chat via an OpenAI-compatible `/v1/chat/completions` endpoint. The unified client also supports aliases for Mistral, TinyLlama, and StarCoder; when working with the reviewer service set `LLM_MODEL=qwen` (or another alias) and `LLM_URL` to the exposed host. Legacy `/chat` remains for backward compatibility, but new tooling should prefer the OpenAI route.


## Performance Benchmarks

Use the inline benchmarking helper to measure review latency against local or shared models:
```bash
LLM_URL=http://127.0.0.1:8000 \
LLM_MODEL=qwen poetry run python - <<'PY'
# (see docs/reference/en/PERFORMANCE_BENCHMARKS.md for the full script)
PY
```

Latest measurements (Qwen/Qwen1.5-4B-Chat on infra_shared):
- Dummy LLM (no external call): avg **0.00068s** over 3 runs
- Real LLM via `/v1/chat/completions`: avg **4.08s** over 5 runs

Benchmarks are captured in `docs/reference/en/PERFORMANCE_BENCHMARKS.md`.

## Examples

- `examples/review` – scripts for running multi-pass reviews against sample
  archives
- `scripts/quality/test_review_system.py` – orchestrated smoke test that exercises the
  feature flag, Mongo connectivity, and metrics endpoints

## Troubleshooting

| Symptom | Possible Cause | Fix |
| --- | --- | --- |
| `MongoDB unavailable` skips in tests | Container not connected to `infra_infra_db-network` | Attach test runner container to the network or update `TEST_MONGODB_URL` |
| `Unknown model: summary` | Unified client not using alias adapter | Ensure you run the latest `ModularReviewService` with `USE_MODULAR_REVIEWER=1` |
| `Input validation failed: model_name` | Raw model name contains version suffix | Use aliases (`mistral`, `qwen`, etc.) or rely on automatic normalisation |
| `HTTP 422` on `/chat` | Server expects OpenAI payload | Configure `LLM_MODEL` alias and prefer `/v1/chat/completions` |
| Review pipeline hangs >90s | Shared LLM offline or slow | Check `http://llm-api:8000/health` and Prometheus metrics |
| Prometheus counters absent | Metrics endpoint not scraped | Confirm `PROMETHEUS_URL` in `.env` and that `infra_shared` Prometheus includes the job |
