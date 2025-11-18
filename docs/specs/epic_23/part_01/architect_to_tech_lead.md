# Architect → Tech Lead Handoff · Epic 23 · Observability & Benchmark Enablement

## 1. Metadata
| Field | Value |
| --- | --- |
| Epic | EP23 |
| Architecture version | 1.1 (2025-11-15) |
| Architect | cursor_architect_v1 |
| Analyst requirements pack | `docs/specs/epic_23/backlog.md` rev. 2025-11-15 |
| Scope change notes | 5 RU channels × 30 days, DR removed, Mongo JSON storage retained, owner-only RAG++ |

## 2. Architecture Vision Summary
- Goal: unblock Stage 05 benchmark pipeline by seeding Mongo datasets, verifying exporters, and enforcing Day 23 observability (metrics/logging/tracing) across MCP, Butler sidecar, and CLI runtimes.
- Environment: single Ryzen 5800 / 128 GB RAM / RTX 3070 Ti host; CI must assume same capacities.
- Data: exactly five RU Telegram channels provided by the PO, 30-day window, ≥30 daily digests per channel, stored as JSON in `butler.digests` and `butler.review_reports`.
- Observability: `/metrics` endpoints must expose new counters/histograms for exporters, shared infrastructure bootstrap, and benchmark runs; structured logs routed to Loki; tracing hooks recorded for self-observation.
- RAG++: feature flag remains owner-only; document limitation in Tech Lead plan (no shared rollout automation in this epic).

## 3. Component Inventory
| Component | Layer | Responsibilities | Dependencies |
| --- | --- | --- | --- |
| `BenchmarkDatasetDomain` | Domain | Entities/value objects validating digest/report samples (RU locale, latency fields, feature flags). | None |
| `ObservabilityPolicy` | Domain | Ruleset for Day 23 telemetry coverage (metrics, logs, traces). | None |
| `SeedBenchmarkDataUseCase` | Application | Orchestrate ingestion of 5-channel × 30-day dataset into Mongo, enforce ≥30 digests/channel. | `IBenchmarkRepository`, `ObservabilityPolicy` |
| `VerifyExportersUseCase` | Application | Run exporter scripts, validate JSONL outputs, archive evidence. | CLI adapters, `IBenchmarkRepository` |
| `RunBenchmarkUseCase` | Application | Trigger `scripts/quality/benchmark/run_benchmark.py`, collect metrics, update PERFORMANCE_BENCHMARKS. | Prometheus adapter, CLI |
| `TelemetryOrchestrator` | Application | Register new Day 23 metrics/log hooks across runtimes. | Metrics adapters, logging adapters |
| `SharedInfraBootstrapUseCase` | Application | Call `scripts/ci/bootstrap_shared_infra.py` / `make day-12-up` parity, emit health metrics. | Shell adapter, Prometheus |
| `RAGTuningManager` | Application | Manage owner-only RAG++ knobs (seed, variance metrics) and write config updates. | Config store adapter |
| `MongoBenchmarkRepository` | Infrastructure | CRUD for `butler.digests` / `butler.review_reports`, validation helpers. | MongoDB |
| `PrometheusMetricsAdapter` | Infrastructure | Extend metrics modules (`src/infrastructure/metrics/*`, `src/presentation/cli/backoffice/metrics/`). | Prometheus client |
| `GrafanaLokiProvisioner` | Infrastructure | Codify dashboards/alerts, ensure IaC validated in CI. | Grafana/Loki |
| `CLI/MCP Instrumentation` | Presentation | Ensure CLI, MCP HTTP server, Butler metrics sidecar expose Day 23 metrics/logs/traces. | TelemetryOrchestrator |

## 4. Requirement Coverage
| Requirement / Backlog Item | Components / Use Cases | Notes |
| --- | --- | --- |
| Seed digests (Task 1) | `SeedBenchmarkDataUseCase`, `MongoBenchmarkRepository` | Accepts PO validation rule ≥30 digests/channel. |
| Seed reviewer reports (Task 2) | Same repository + domain validation | Reuse exporter schema, no duplication needed. |
| Verify exporters (Task 3) | `VerifyExportersUseCase`, CLI adapters | Artifacts stored under `benchmark_dataset_dir`. |
| Run benchmarks & Stage 05 pilot (Tasks 4–5) | `RunBenchmarkUseCase`, `TelemetryOrchestrator` | Update `docs/reference/en/PERFORMANCE_BENCHMARKS.md`. |
| RU localization + hygiene (Tasks 6,11–15) | Presentation layer updates + docs tasks | Out of domain scope but tracked as cross-cutting. |
| Shared infra automation (Task 8) | `SharedInfraBootstrapUseCase`, metrics adapters | Must emit health metrics for CI gating. |
| Grafana IaC / Loki alerts (Task 9) | `GrafanaLokiProvisioner` | CI validation evidence required. |
| RAG++ extensions (Task 16) | `RAGTuningManager` | Owner-only, reference `config/retrieval_rerank_config.yaml`. |

## 5. Observability Plan (Day 23)
- **Metrics** (register in Prometheus registry shared by MCP/Butler/CLI):
  - `benchmark_digest_records_total{channel=...}` counter.
  - `benchmark_export_duration_seconds` histogram (per exporter).
  - `shared_infra_bootstrap_status` gauge (0=failure,1=success).
  - `rag_variance_ratio` gauge for owner-only feature flag.
  - `structured_logs_total{service,level}` counter for log compliance.
- **Logging**: JSON structured logs with fields `trace_id`, `epic_id`, `channel`, `stage`; route to Loki via existing promtail config; update `observability_labels.md`.
- **Tracing**: Light span telemetry for exporter runs and benchmark CLI; store trace metadata in Mongo for self-observation (Day 23 requirement).
- **Docs**: Update `docs/roles/analyst/day_capabilities.md` and `docs/roles/analyst/examples/*` to include new observability metadata fields in handoff JSON.

## 6. Infrastructure & Deployment Notes
- No DR automation in this epic; CI/local parity ensured by `scripts/ci/bootstrap_shared_infra.py` and `make day-12-up`.
- Keep Mongo as primary storage; no migration to Qdrant or other vector stores in EP23.
- Grafana dashboards and Loki alert rules must be committed under `grafana/dashboards/` and `prometheus/alertmanager.yml` with CI validation.
- Hardware baseline: single Ryzen 5800 host; performance tests should reflect this environment.

## 7. MADR Checklist
| MADR ID | Topic | Status | Notes |
| --- | --- | --- | --- |
| MADR-EP23-001 | Dataset strategy (synthetic vs recovered) | Draft | Reference Stage 05 runbook; final decision pending test data availability. |
| MADR-EP23-002 | Telemetry aggregation approach | Draft | Choose between single shared registry vs per-runtime fan-in; recommend shared registry. |
| MADR-EP23-003 | Shared infra bootstrap in CI | Draft | Compare GitHub Actions service containers vs Python bootstrap scripts (current direction: scripts). |
| MADR-EP23-004 | RAG++ reproducibility knobs | Draft | Document owner-only flag, seed handling, variance metrics. |

Tech Lead should expect at least these four MADRs finalized before implementation planning; add new ones if additional trade-offs appear.

## 8. Risks & Mitigations
| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Insufficient channel data (<30 digests) | Blocks acceptance | Medium | Add validation step in seeding use case; fall back to synthetic generation for gaps. |
| Exporter scripts diverge from Mongo schema | Incorrect datasets | Medium | Snapshot exporter README references and add schema validation tests. |
| CI bootstrap flakiness | Slows merges | Medium | Emit Prometheus health metrics, add retry logic and teardown guard. |
| Observability metric cardinality | Prometheus overload | Low | Enforce fixed label taxonomy via `ObservabilityPolicy`. |

## 9. Open Items for Tech Lead
1. Confirm timeline/effort allocation for hygiene tasks (YAML/JSON fixes, RU localization) since they span multiple teams.
2. Decide where MADRs will live (`docs/specs/epic_23/decisions/`) and coordinate reviewer assignments.
3. Provide feedback if additional instrumentation is required for CLI/backoffice beyond Day 23 baseline.

Once these points are settled, Tech Lead can break work into implementation stages per handoff contract.
