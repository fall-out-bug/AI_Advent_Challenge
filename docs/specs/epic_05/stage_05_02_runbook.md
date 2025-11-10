# Stage 05_02 Runbook · Benchmark & Dataset Automation

## Purpose

Provide operational guidance for running RU summarisation benchmarks, exporting
datasets, and verifying metric visibility across CI and observability tooling.

## Prerequisites

- Shared infra environment variables loaded (`.env.infra`). See
  `docs/specs/infra/shared_infra_reference.md` for endpoints and credentials.
- MongoDB with `digests`, `review_reports` collections populated.
- LLM endpoint reachable at `LLM_URL` (for live runs).
- Python 3.11 with project dependencies installed (`pip install -e .`).

## 1. Export Datasets

### Channel Digests (RU)

```bash
poetry run python scripts/analysis/export_digests.py \
  --mongo "$MONGODB_URL" \
  --hours 24 \
  --limit 50 \
  --output data/benchmarks/benchmark_digest_ru_v1/$(date +%Y%m%d)_samples.jsonl
```

- `source_text` is automatically derived from post payloads.
- Feature flags and latency metrics stored in `metadata` and `latency_seconds`.

### Reviewer Summaries (RU)

```bash
poetry run python scripts/analysis/export_review_reports.py \
  --mongo "$MONGODB_URL" \
  --hours 24 \
  --limit 50 \
  --output data/benchmarks/benchmark_review_ru_v1/$(date +%Y%m%d)_samples.jsonl
```

- Pass summaries, recommendations, and findings are concatenated into
  `source_text`.
- Latency values read from report metadata when available.

## 2. Run Benchmarks

### Dry Run (CI/Smoke)

```bash
poetry run python scripts/benchmark/run_benchmark.py \
  --scenario channel_digest_ru \
  --dataset data/benchmarks/benchmark_digest_ru_v1/2025-11-09_samples.jsonl \
  --dry-run --fail-on-warn
```

- Uses stored `baseline_scores` to avoid live LLM calls.
- CI workflow `.github/workflows/stage05_benchmark_smoke.yml` executes the same
  command on pull requests.

### Live Run

```bash
poetry run python scripts/benchmark/run_benchmark.py \
  --scenario channel_digest_ru \
  --dataset data/benchmarks/benchmark_digest_ru_v1/latest.jsonl \
  --fail-on-warn
```

- Requires valid `LLM_URL` and credentials.
- Results printed as JSON and emitted to Prometheus via
  `benchmark_run_*` metrics.

## 3. Metrics Verification

- Hit MCP `/metrics` endpoint (port 8004 by default) and confirm the presence of:
  - `benchmark_run_duration_seconds`
  - `benchmark_run_outcome`
  - `benchmark_metric_value`
  - `benchmark_metric_outcome`
- Check Prometheus scrape status for `mcp-server` job to validate exposure.
- Import `grafana/dashboards/stage05-benchmarks.json` into Grafana (or sync via
  provisioning) to visualise benchmark outcomes and latest status.

## 4. Artefact Management

- Store latest JSONL files in `data/benchmarks/<dataset_id>/latest.jsonl`.
- Archive dated snapshots for audit (`*_samples.jsonl`).
- Upload validated datasets to external storage (MinIO/S3) and retain anonymised
  manifests referencing location and checksum.

## 5. Troubleshooting

| Symptom | Action |
|---------|--------|
| `Export failed: ... connection refused` | Verify Mongo URI and credentials; ensure `mongod` reachable. |
| CLI exits with code 2 (fail) | Inspect JSON output; review metrics falling below thresholds. |
| No benchmark metrics on `/metrics` | Confirm CLI executed; ensure `prometheus_client` installed and runner imported. |
| Live run times out | Increase `benchmark_judge_timeout_seconds` in env or reduce concurrency (`--max-concurrency 1`). |

## 6. Next Steps

- Add Grafana panels visualising new metrics (coverage, accuracy, latency,
  outcome trend).
- Automate dataset uploads post-smoke run with checksum logging.
- Extend dry-run flow to reviewer summaries once dataset seeds exist.
