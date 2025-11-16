# Epic 23 · Observability & Benchmark Enablement

## Context
- Day 23 introduces observability-centric requirements for all agents (logging, metrics, tracing, self-observation) on top of Day 1–22 capabilities described in `docs/roles/analyst/day_capabilities.md`.
- Benchmark automation from Epic 05 depends on populated datasets and on telemetry that can be validated in CI via Prometheus/Grafana/Loki (`docs/operational/shared_infra.md`).
- `docs/specs/epic_23/backlog.md` captures sixteen blocking tasks that collectively unblock Stage 05 live runs, DR drills, and RAG++ rollout.

## Goals
1. Seed benchmark datasets and execute Stage 05_03 pilot runs end-to-end with live metrics captured and published.
2. Define and enforce observability requirements (metrics, logging, traces) for every pipeline component, satisfying Day 23 expectations and handoff contracts.
3. Automate shared infrastructure bootstrap (Mongo, Prometheus, Grafana, Loki, LLM) for CI/local parity and document RU/EN operations playbooks.

## Success Metrics
- ✅ `scripts/quality/analysis/export_digests.py` and `export_review_reports.py` generate non-empty datasets referenced by `scripts/quality/benchmark/run_benchmark.py` without manual DB tweaks.
- ✅ `/metrics` endpoints (MCP HTTP server, Butler bot sidecar, CLI commands) expose the consolidated Prometheus registry with new Day 23 gauges/counters.
- ✅ Grafana dashboards and Loki alert rules codified as IaC and validated in CI via `make day-12-up` or equivalent automation.
- ✅ Disaster Recovery (DR) drill executed and documented with pass/fail criteria linked to Prometheus evidence.
- ✅ Mongo collections (`digests`, `review_reports`) contain ≥30 daily digests per RU channel across the latest 30 calendar days, proving exporter coverage without schema rewrites.

## Scope
### Must Have
- Benchmark data seeding, exporter verification, benchmark execution, and Stage 05_03 pilot handoff (Backlog items 1–5).
- Shared infra automation + CI bootstrap scripts + docs updates (items 8–10).
- Observability requirements for all runtimes, including new metrics/traces, structured logging, and `/metrics` exposure (Day 23 focus, items 9–10, 16).
- Documentation hygiene (RU localisation, CLI coverage, lint/YAML/JSON fixes, JSONL optimisation) to keep repositories compliant (items 6–15).

### Should Have
- RAG++ reproducibility knobs (seed, cross-run variance, adaptive thresholds) and rollout plan updates (item 16).
- Expanded tests for backoffice CLI integration and shared infra smoke coverage (items 5, 8, 11).

### Out of Scope
- New business features unrelated to observability or benchmarking.
- Non-critical refactors of legacy async tests beyond cataloguing/archiving (item 15 limits).
- Disaster recovery drills or multi-host failover for the shared infra stack (single Ryzen 5800 + 128 GB RAM + RTX 3070 Ti host only).

## Current State Assessment
- **Benchmark exporters** already normalise digests/review reports from Mongo, include feature flags, latency, and metadata, and surface failure modes through structured errors (`scripts/quality/analysis/export_digests.py`, `scripts/quality/analysis/export_review_reports.py`).
- **Benchmark runner** supports live vs dry-run execution, configurable metrics, and Prometheus recording hooks, enabling reuse once datasets exist (`scripts/quality/benchmark/run_benchmark.py`).
- **Metrics infrastructure** provides Prometheus collectors for Butler bot and RAG pipelines plus `/metrics` endpoints in MCP HTTP server and bot metrics sidecar, satisfying Day 11–12 observability baselines (`src/infrastructure/metrics/butler_metrics.py`, `src/infrastructure/metrics/rag_metrics.py`, `src/presentation/mcp/http_server.py`, `src/presentation/bot/metrics_server.py`).
- **Shared infra** scripts and docs exist (`scripts/ci/bootstrap_shared_infra.py`, `docs/operational/shared_infra.md`) but require automation within CI workflows and DR drill documentation.

## Workstreams & Requirements

### 1. Benchmark Data & Stage 05 Pilot
- **Requirements**
  - Populate `butler.digests` and `butler.review_reports` with synthetic or recovered samples covering RU channels, including summary, raw posts, feature flags, latency, and judge scores.
- Enforce minimum dataset requirement: ≥30 daily digests per provided channel spanning the last 30 calendar days.
  - Run exporters and benchmark CLI against populated data; archive JSONL artefacts under `benchmark_dataset_dir`.
  - Execute Stage 05_03 pilot per `docs/specs/epic_05/stage_05_03_runbook.md` and capture governance approvals.
- Acceptance tests defined in Analyst pack: exporter record counts, RU localization spot-check, benchmark latency on target host.
- **Acceptance**
  - Export commands succeed twice consecutively, producing ≥50 samples each with required metadata.
  - `scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru --dry-run` and live mode both succeed, writing Prometheus metrics.
  - `docs/reference/en/PERFORMANCE_BENCHMARKS.md` updated with fresh metrics, thresholds, and timestamped evidence.

### 2. Observability & Day 23 Telemetry
- **Requirements**
  - Define Day 23 capability in `docs/roles/analyst/day_capabilities.md`, detailing observability requirements (logging, metrics, tracing, self-observation notes).
  - Expand Prometheus metrics (structured logging counts, trace/span timings, DR drill progress) within `src/infrastructure/metrics/` and ensure `/metrics` endpoints aggregate registries.
  - Ensure CLI/backoffice commands emit metrics via `src/presentation/cli/backoffice/metrics/prometheus.py` and log structured audit events.
  - Add tracing/decision logging hooks for Analyst self-observation (Day 23) with storage via Mongo (leveraging Day 16 external memory).
- **Acceptance**
  - `/metrics` endpoints for MCP HTTP server, Butler bot, and CLI return new gauges/counters documented in `observability_labels.md`.
  - Loki alert extensions and Grafana IaC validated in CI; dashboards source-controlled (JSON + provisioning).
  - Updated examples in `docs/roles/analyst/examples/` showing observability metadata in handoff JSON.

### 3. Shared Infra Automation & DR
- **Requirements**
  - Automate `scripts/ci/bootstrap_shared_infra.py` invocation inside CI workflows, ensuring `.env.infra` parity and automatic cleanup.
  - Implement `make day-12-up` parity scripts for Day 23 stack (Mongo, Prometheus, Grafana, Loki, LLM, mock services).
  - Plan, execute, and document DR drill for observability stack, storing outcomes in `docs/specs/epic_23/dr_drill.md`.
- **Acceptance**
  - CI logs show automatic infra bring-up and tear-down; failures block merge.
  - DR drill report includes objectives, execution log, metrics screenshots/links, and pass/fail decision.

### 4. Documentation, Localisation & Hygiene
- **Requirements**
  - Update RU localisation for MCP/Telegram/CLI docs (items 6, 11).
  - Fix linters for `shared/tests`, make YAML/JSON valid (`config/mcp_config.yaml`, `archive/docker-compose/docker-compose.yml`, `tests/e2e/telegram/fixtures/test_messages.json`), and compress oversized JSONL artefacts (<500 KB).
  - Extend README/operations docs with Day 23 observability expectations and runbooks.
- **Acceptance**
  - `pre-commit run --all-files` passes without formatting bursts.
  - README.ru/EN mention new observability metrics and DR drill results.

### 5. RAG++ Extensions & Quality Gates
- **Requirements**
  - Document prompt tuning cadence, randomness control (`seed`), cross-run variance metrics, and adaptive thresholds for `rag_plus_plus` flag (Backlog item 16).
  - Add Prometheus metrics for reranker variance and fallback reasons, and ensure CI captures these via smoke tests.
  - Plan canary rollout (percentage-based) with acceptance criteria and rollback triggers.
- **Acceptance**
  - `docs/specs/epic_21/` (or new Day 21 addendum) updated with tuning strategy and metrics plan.
  - CI/regression tests assert reranker variance metrics present and within range.

## Acceptance Checklist
- [ ] Benchmark exporters succeed with populated DB; datasets stored and catalogued.
- [ ] Stage 05 benchmark + pilot executed with metrics recorded and documented.
- [ ] Observability documentation (capabilities + examples + labels) updated for Day 23.
- [ ] All runtimes expose `/metrics` with new gauges/counters; Grafana/Loki IaC validated.
- [ ] Shared infra automation added to CI; DR drill executed and recorded.
- [ ] Documentation/ localisation/ lint hygiene tasks completed; JSONL artefacts optimised.
- [ ] RAG++ tuning, reproducibility, and variance monitoring documented and enforced.

## Dependencies
- Access to `.env.infra` secrets for Mongo, Prometheus, Grafana, Loki, LLM.
- Availability of synthetic or production-like data dumps.
- Coordination with Architect/Tech Lead for observability labels and CI gate updates.

## Risks & Mitigations
- **Incomplete data dumps** → Define synthetic dataset generator fallback; document generation steps.
- **CI flakiness due to infra bootstrap** → Provide retry/backoff logic and health checks in bootstrap scripts.
- **Observability noise** → Establish sampling strategies and label conventions to prevent cardinality explosions.
- **DR drill scheduling conflicts** → Reserve maintenance window and align stakeholders per `docs/operational/shared_infra.md`.

## Deliverables
- `docs/specs/epic_23/epic_23.md` (this spec) + supporting runbooks (DR drill, observability labels update).
- Updated role docs (`docs/roles/analyst/day_capabilities.md`, `docs/roles/analyst/examples/`).
- Updated operational docs (`docs/reference/en/PERFORMANCE_BENCHMARKS.md`, `README.ru`, shared infra playbooks, Grafana/Loki IaC).
- Updated CI workflows/scripts for shared infra automation and observability validation.
