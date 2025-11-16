# Epic 23 · Architect Handoff Package

Purpose:
    Provide the complete file bundle Architect must ingest before producing the
    architecture vision for Day 23 (Observability & Benchmark Enablement).

## Core Epic References
- `docs/specs/epic_23/epic_23.md`
- `docs/specs/epic_23/backlog.md`
- `docs/specs/epic_23/architect_to_analyst.md`

## Analyst Role & Handoff Context
- `docs/roles/analyst/role_definition.md`
- `docs/roles/analyst/day_capabilities.md`
- `docs/roles/analyst/rag_queries.md`
- `docs/roles/analyst/examples/README.md`
  - `docs/roles/analyst/examples/day_3_conversation_stopping.md`
  - `docs/roles/analyst/examples/day_8_token_budgeting.md`
  - `docs/roles/analyst/examples/day_15_compression.md`
  - `docs/roles/analyst/examples/day_22_rag_citations.md`
- `docs/roles/analyst/examples/` (future Day 23 example to include observability metadata)
- `docs/operational/context_limits.md`
- `docs/operational/handoff_contracts.md`
- `docs/roles/CURSOR_INITIALIZATION.md`

## Observability & Shared Infrastructure
- `docs/operational/shared_infra.md`
- `archive/docs/epic_21/stage_21_03_observability_plan.md`
- `docs/operational/observability_labels.md`
- `grafana/dashboards/*.json`
- `prometheus/prometheus.yml`
- `prometheus/alertmanager.yml`
- `scripts/ci/bootstrap_shared_infra.py`
- `scripts/ci/cleanup_shared_infra.py`
- `scripts/ci/mock_shared_services.py`
- `scripts/infra/start_shared_infra.sh`
- `scripts/infra/start_models.sh`
- Target hardware reference: single Ryzen 5800 / 128 GB RAM / RTX 3070 Ti host (DR out of scope for this epic).

## Benchmark & Dataset Tooling
- `scripts/quality/analysis/export_digests.py`
- `scripts/quality/analysis/export_review_reports.py`
- `scripts/quality/benchmark/run_benchmark.py`
- `scripts/quality/test_review_system.py`
- Sample output links from exporters (schema reference instead of inline duplication).
- `docs/reference/en/PERFORMANCE_BENCHMARKS.md`
- `docs/specs/epic_05/stage_05_03_runbook.md`

## Metrics & Telemetry Implementations
- `src/infrastructure/metrics/butler_metrics.py`
- `src/infrastructure/metrics/rag_metrics.py`
- `src/presentation/bot/metrics_server.py`
- `src/presentation/mcp/http_server.py`
- `src/presentation/cli/backoffice/metrics/*`
- `src/infrastructure/monitoring/mcp_metrics.py`
- `src/infrastructure/monitoring/prometheus_metrics.py`

## RAG++ Dependencies
- `docs/specs/epic_20/epic_20.md`
- `docs/specs/epic_21/` (Stage 21_03 materials)
- `config/retrieval_rerank_config.yaml`
- `scripts/rag/day_20_demo.py`
- `scripts/rag/day_21_demo.py`
- `results_stage20.jsonl`
- `results_with_labels.jsonl`
- RAG++ feature flag remains owner-only (document limitation in handoff notes).

## Operational & Programme References
- `docs/specs/process/agent_workflow.md`
- `docs/specs/agents/MODELS.md`
- `docs/specs/progress.md`
- `docs/guides/en/DEPLOYMENT.md`
- `docs/guides/en/DOCKER_SETUP.md`
- `README.md`
- `README.ru`

Acceptance:
    Architect confirms receipt of all files above before drafting the Day 23
    architecture vision and references this list in the design log.
