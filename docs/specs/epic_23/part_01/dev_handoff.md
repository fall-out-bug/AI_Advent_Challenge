# Epic 23 · Developer Handoff

## 1. Scope & Inputs
- **Epic:** EP23 – Observability & Benchmark Enablement (Day 23 focus).
- **Primary plan:** `docs/specs/epic_23/tech_lead_plan.md` (TL-00…TL-07).
- **Acceptance tracking:** `docs/specs/epic_23/acceptance_matrix.md`.
- **Checklists & addenda:** `docs/specs/epic_23/checklists/ru_localization_spotcheck.md`, `docs/specs/epic_23/owner_only/rag_plus_plus_addendum.md`.
- **Challenge Day closures:** `docs/specs/epic_23/challenge_days_gap_closure_plan.md` (Days 1–22 deliverables, owners, evidence).
- **Legacy refactor mini-epics:** `docs/specs/epic_23/mini_epics/legacy_cluster_*.md` (clusters A–E plans + acceptance matrices).

All developers must read the Tech Lead plan before picking up work. This document highlights concrete execution steps, owners, required commands, and evidence expectations.

## 2. Stage Kick-Off Order
| Stage | Start Window | Owner(s) | Notes |
| --- | --- | --- | --- |
| TL-01 | Immediately | Dev A + Data Services | Requires Mongo access + RU spot-check checklist. |
| TL-02 | After TL-01 datasets validated | QA (primary) + Dev B | Depends on `channel_counts.json`. |
| TL-03 | After TL-02 exporters verified | Tech Lead + DevOps | Benchmark runs on Ryzen 5800 host. |
| TL-04 | Overlaps TL-02/TL-03 once schemas stable | Observability squad | Coordinate metrics registry merges. |
| TL-05 | Parallel to TL-04 | DevOps | Implement `make day-23-up/down`, restart memo. |
| TL-06 | After TL-04/TL-05 deliverables | Docs Guild + QA | Lint/YAML/tests + localisation. |
| TL-07 | After TL-04 metrics land | RAG Taskforce | Owner-only addendum + variance metrics. |

## 3. Task Breakdown & Evidence
### TL-01 – Benchmark Dataset Seeding
- **Commands:**  
  - `MONGODB_URL="mongodb://admin:secure_mongo_password_456@127.0.0.1:27017/butler?authSource=admin" PYTHONPATH=. python scripts/quality/analysis/seed_benchmark_data.py --channels "<comma-separated list>" --days 30 --minimum 30`  
  - `python scripts/quality/analysis/sample_ru_entries.py --channel <name> --count 5`
- **Evidence:**  
  - `data/benchmarks/snapshots/2025-11-15/channel_counts.json` (covers @onaboka, @alexgladkovblog, @ctorecords, @xor_journal, @tired_glebmikheev)  
  - Completed `data/benchmarks/snapshots/2025-11-15/ru_spotcheck.md` (Engineer ✅, Analyst signature pending)  
  - `data/benchmarks/snapshots/2025-11-15/dataset_audit.json` (output of `verify_benchmark_counts.py`, verifies ≥30 records + schema fields)  
  - Prometheus counter `benchmark_digest_records_total{channel="..."}` ≥30 (shared registry; screenshot attached in PR)
- **DoD:** Checklist signed by engineer + Analyst, Mongo counts validated twice (Engineer complete as of 2025-11-15; Analyst review outstanding).

### TL-02 – Exporter Verification
- **Commands:**  
  - `PYTHONPATH=. python scripts/quality/analysis/export_digests.py --hours 720 --limit 1000 --output data/benchmarks/exports/2025-11-15/digests.jsonl`  
  - `PYTHONPATH=. python scripts/quality/analysis/export_review_reports.py --hours 720 --limit 1000 --output data/benchmarks/exports/2025-11-15/review_reports.jsonl`  
  - `pytest tests/integration/benchmark/test_exporters.py`
- **Evidence:**  
  - `data/benchmarks/exports/2025-11-15/manifest.json` + SHA256  
  - `data/benchmarks/exports/2025-11-15/schema_validation.json` (150 records / файл, 0 schema misses)

### TL-03 – Benchmarks & Stage 05_03 Pilot
- **Commands:**  
  - `python scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru --dry-run`  
  - `python scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru`  
  - Stage 05_03 runbook steps (`docs/specs/epic_05/stage_05_03_runbook.md`)
- **Evidence:**  
  - Log excerpts + latency metrics appended to `docs/reference/en/PERFORMANCE_BENCHMARKS.md`  
  - `docs/specs/epic_23/stage_05_03_pilot_log.md` (governance approvals, observations)

### TL-04 – Observability Instrumentation
- **Key files:** `src/infrastructure/metrics/*`, `src/presentation/*/metrics*`, `docs/roles/analyst/day_capabilities.md`.
- **Commands:**  
  - `pytest tests/unit/infrastructure/metrics`  
  - `pytest tests/integration/presentation/test_metrics_endpoints.py`
- **Evidence:**  
  - `/metrics` snapshots for MCP, Butler, CLI (attach to PR)  
  - Updated docs with Day 23 observability capability  
  - `docs/operational/observability_labels.md` entry describing new labels + registry sharing  
  - Metrics instrumentation: `structured_logs_total`, `benchmark_export_duration_seconds`, `shared_infra_bootstrap_status`, `rag_variance_ratio`

### TL-05 – Shared Infra Automation & Restart Validation
- **Commands:**  
  - `python scripts/ci/bootstrap_shared_infra.py --check`  
  - `make day-23-up` / `make day-23-down` (new targets)  
  - `docker compose ps`, PromQL `sum(rate(http_requests_total{job="mcp"}[5m]))`
- **Evidence:**  
  - `docs/specs/epic_23/shared_infra_restart.md` with executed commands + PromQL/Loki queries + screenshots  
  - CI logs showing bootstrap + teardown success

### TL-06 – Documentation & Hygiene
- **Commands:**  
  - `pre-commit run --all-files`  
  - `pytest tests/shared`  
  - `python scripts/tools/compress_jsonl.py results_stage20.jsonl`
- **Evidence:**  
  - README.ru/README.md diffs referencing Day 23 telemetry  
  - Lint/test logs attached to PRs

### TL-07 – RAG++ Reproducibility
- **Commands:**  
  - `python scripts/rag/day_21_demo.py --dry-run --seed <value>`  
  - `pytest tests/integration/rag/test_variance_metrics.py`
- **Evidence:**  
  - Updated `config/retrieval_rerank_config.yaml` (sanitized)  
  - `docs/specs/epic_23/owner_only/rag_plus_plus_addendum.md` entry summarizing cadence + metrics  
  - Grafana dashboard `rag_variance.json` screenshot

## 4. CI / Quality Gates (Quick Reference)
| Gate | Command | Responsibility |
| --- | --- | --- |
| Lint | `make lint` | All |
| Typecheck | `mypy src/ --strict` | TL-01, TL-04, TL-07 |
| Unit Tests | `pytest tests/unit` | TL-01, TL-04, TL-07 |
| Integration Tests | `pytest tests/integration` | TL-02–TL-05 |
| Coverage | `pytest --cov=src --cov-report=xml` | TL-01, TL-04, TL-07 |
| Security | `bandit -r src` | TL-04 |
| Bootstrap Smoke | `python scripts/ci/bootstrap_shared_infra.py --check` | TL-05 |
| Restart Validation | `make day-23-up && make day-23-down` | TL-05 |
| Benchmark Run | `python scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru` | TL-03 |
| RAG Variance | `pytest tests/integration/rag/test_variance_metrics.py` | TL-07 |

## 5. Communications & Reporting
- Все апдейты публикуем в текущем чате: статус стадий, ссылки на артефакты, найденные блокеры.
- По завершению стадии:  
  1. Пишем в чат короткий отчёт + ссылки.  
  2. Обновляем соответствующую строку `acceptance_matrix.md` (статус + подпись).  
  3. Прикладываем выдержку в PR/commit описания.

## 6. Ready Checklist
- [ ] Техлид и разработчики ознакомились с `tech_lead_plan.md`.  
- [ ] Доступ к Mongo/Prometheus/Grafana подтверждён (см. `.env.infra`).  
- [ ] Ryzen 5800 хост забронирован на время TL-03/TL-05.  
- [x] DevOps начали подготовку `make day-23-up/down` (completed 2025-11-16).  
- [ ] Все команды понимают требования по докам/доказательствам (см. раздел 3).

После выполнения каждого пункта сообщайте в чат; будем оперативно корректировать план при появлении новых рисков.

