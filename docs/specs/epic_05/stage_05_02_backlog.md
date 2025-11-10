# Stage 05_02 Automation Backlog (Draft)

## Overview

Automation must operationalise RU summarisation benchmarks by wiring LLM-as-judge
pipelines, dataset exporters, and observability hooks. Tasks below are prioritised
to deliver an end-to-end evaluation run before the next release freeze.

## Backlog

### P0 — Release Blockers

1. **Implement benchmark evaluation runner**
   - Build Python module under `src/application/benchmarking/` orchestrating sample
     loading, LLM judge calls, and result aggregation.
   - Support JSONL datasets in `data/benchmarks/benchmark_digest_ru_v1/` and future
     reviewer datasets.
   - Emit metrics (`benchmark_run_duration_seconds`, `benchmark_metric_value`) via
     Prometheus client.
   - Owner: ML engineering.
   - Status (2025-11-11): Initial module, factory, CLI runner landed; awaiting
     integration with automation workflows. Unit tests added covering aggregation
     and empty dataset scenarios.

2. **Add CI workflow for benchmark smoke run**
   - Create `.github/workflows/stage05_benchmark_smoke.yml`.
   - Execute evaluation runner on a trimmed dataset (<5 samples) to prevent
     regression before release.
   - Fail build if any metric crosses failure thresholds.
   - Status (2025-11-11): Workflow added using dry-run judge over sample dataset;
     extend to live runs once automation is stable.

3. **Expose modular reviewer metrics**
   - Integrate reviewer histograms/counters with MCP FastAPI `/metrics`.
   - Ensure `review_pipeline_latency_seconds` and judge-related counters are
     exported.
   - Owner: Reviewer platform.
   - Status (2025-11-11): Benchmark metrics available on MCP `/metrics` via
     Prometheus recorder; Grafana dashboard stub added, reviewer latency exports
     still pending wiring.

### P1 — High Priority

4. **Dataset exporter scripts**
   - Extend `scripts/quality/analysis/export_digests.py` to persist feature flag snapshots
     and Prometheus latency samples.
   - Add companion `export_review_reports.py` for reviewer datasets.
   - Store outputs under `data/benchmarks/<dataset_id>/`.
   - Status (2025-11-11): Scripts created with feature flag capture and latency
     fields; verify against production collections during next sync.

5. **Benchmark prompt registry**
   - Add prompt storage in `docs/specs/epic_05/prompts/`.
   - Version prompts and expose via configuration to evaluation runner.

6. **Grafana dashboard updates**
   - New panels for RU benchmarks showing metric trends, warning/failure bands, and
     release run history.
   - Link scoreboard to `docs/reference/en/PERFORMANCE_BENCHMARKS.md`.

### P2 — Follow-Up

7. **Automation documentation**
   - Author `docs/specs/epic_05/stage_05_02_runbook.md` with execution steps,
     troubleshooting, and incident response.

8. **On-demand benchmarking CLI**
   - Provide CLI entry point (`scripts/benchmark/run_benchmark.py`) supporting
     scenario selection and experimental runs.

9. **External storage sync**
   - Automate dataset upload to MinIO/S3 after successful release benchmark.
   - Strip PII and publish anonymised manifest back into repo.

## Dependencies

- Stage 05_01 dataset schema and sample inventory.
- Observability metrics inventory (`docs/specs/epic_03/metrics_inventory.json`) for
  naming alignment.
- Feature flag definitions to filter datasets (EP01 inventory).
- Access to shared LLM API and Mongo DB (export scripts).

## Risks & Mitigations

- **LLM costs / latency**: restrict CI smoke runs to minimal sample sizes and cache
  judge outputs.
- **Data drift**: incorporate feature flag snapshotting and channel blacklist to
  avoid polluted samples.
- **Metric gaps**: coordinate with EP03 to ensure Prometheus endpoints available
  before automation finalisation.
