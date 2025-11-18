# Epic 23 · Tech Lead Implementation Plan
_Observability & Benchmark Enablement · Day 23_

## 1. Metadata & Inputs
| Field | Value |
| --- | --- |
| Epic | EP23 |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-15 |
| Source Requirements | `docs/specs/epic_23/backlog.md` |
| Architecture Package | `docs/specs/epic_23/architect_to_tech_lead.md` v1.1 |
| Analyst Scope Notes | `docs/specs/epic_23/architect_to_analyst.md` |
| Operational Guardrails | `docs/operational/context_limits.md`, `docs/operational/handoff_contracts.md` |
| Related Tooling | Benchmark exporters, shared infra scripts, observability modules listed in `docs/specs/epic_23/architect_handoff.md` |

## 2. Planning Assumptions & Constraints
- Five RU Telegram channels, 30-day window, ≥30 daily digests per channel remain non-negotiable; synthetic backfill allowed only to satisfy acceptance evidence.
- MongoDB stays the system of record; no schema migrations this epic, but validation must reference exporter outputs rather than redefining schemas.
- Hardware baseline: single Ryzen 5800 / 128 GB RAM / RTX 3070 Ti host; all benchmarks and CI simulations must respect this capacity envelope.
- RAG++ feature flag is owner-only; plan documents reproducibility knobs without broad rollout automation.
- DR automation remains out of scope; we only prove same-host restart readiness via TL-05.
- All documentation updates delivered in English, RU localisation items tracked in Stage TL-06 outputs.

## 3. Stage Overview
| Stage ID | Objective | Owner(s) | Duration (days) | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL-00 | Finalize inputs, MADRs, acceptance matrix | Tech Lead | 1 | — | Signed checklist, updated questions log |
| TL-01 | Seed Mongo datasets (digests + review reports) | Data Services + Dev A | 4 | TL-00 | Dataset count report, Mongo validation logs |
| TL-02 | Verify exporters & JSONL artefacts | QA + Dev B | 2 | TL-01 | Export run logs, JSONL schema validation |
| TL-03 | Run benchmarks & Stage 05_03 pilot | Tech Lead + DevOps | 3 | TL-02 | Benchmark reports, performance doc updates |
| TL-04 | Day 23 observability instrumentation & docs | Observability squad | 4 | TL-01 | `/metrics` snapshots, updated role docs/examples |
| TL-05 | Shared infra automation & restart validation | DevOps | 4 | TL-00 | CI logs, restart validation memo |
| TL-06 | Documentation, localisation, hygiene tasks | Docs Guild + QA | 3 | TL-04, TL-05 | `pre-commit` report, README diffs |
| TL-07 | RAG++ reproducibility & variance metrics | RAG Taskforce | 3 | TL-04 | Config diffs, variance dashboards |

Parallelization notes:
- TL-04 can start once Mongo collections expose stable schemas (post TL-01) even while TL-02/03 finish.
- TL-03 must wait for TL-02 exporter validation to avoid consuming unverified datasets.
- TL-05 may run in parallel with TL-04, but restart validation evidence must exist before TL-06 sign-off.
- TL-07 depends on observability metrics to harvest variance data; schedule after TL-04 instrumentation lands.

## 4. Stage Details

### Stage TL-00 · Input Consolidation & MADR Finalization (Day 0–1)
**Scope:** Confirm completeness of architecture handoff, finalize MADR-EP23-001…004, align acceptance matrices with Analyst and Architect.
**Tasks:**
1. Host 30-minute triage with Analyst + Architect to resolve open questions (dataset counts, schema snippets, RAG++ limitations).
2. Produce `docs/specs/epic_23/plan_status.md` snippet capturing scope, blockers, and token budget per `docs/operational/context_limits.md`.
3. Store the shared acceptance matrix at `docs/specs/epic_23/acceptance_matrix.md`, set `version: v1.0` (bump per change), and align signatures.
4. Define ownership: Tech Lead maintains the matrix post sign-off, Analyst co-signs every revision triggered by backlog changes; document this in the header.
5. Update MADRs with final decisions on dataset strategy, telemetry aggregation, CI bootstrap, and RAG reproducibility.
6. Capture risk/opportunity deltas in risk register (Section 7) and assign owners.
**Definition of Done:**
- All MADRs approved and referenced in this plan.
- Acceptance matrix (`docs/specs/epic_23/acceptance_matrix.md`) signed by Analyst & Architect, mapping backlog items to stages, includes `owner: tech_lead` and version tag incremented if any rows change.
- No open blocking questions remain in `handoff_contracts` tracker.
**CI Gates:** `make lint` (plan linting), markdown link checker (`scripts/ci/check_docs.py`).

### Stage TL-01 · Benchmark Dataset Seeding (Days 1–5)
**Scope:** Implement `SeedBenchmarkDataUseCase` plus Mongo repository extensions to ingest 5×30-day datasets with RU localisation metadata.
**Tasks:**
1. Define `BenchmarkDatasetDomain` validators (latency, feature flags, RU localisation markers).
2. Implement ingestion pipeline (reuse `scripts/quality/analysis` helpers) with synthetic backfill fallback.
3. Add automated count checks per channel (≥30 daily digests) with alerts to Prometheus (`benchmark_digest_records_total`).
4. Run Mongo aggregation per channel, export results to `benchmark_dataset_dir/snapshots/YYYY-MM-DD/channel_counts.json`, and reference files in acceptance artifacts.
5. Execute RU localisation spot-check per `docs/specs/epic_23/checklists/ru_localization_spotcheck.md` (5-entry sample, bilingual reviewer sign-off).
6. Store sample generation scripts and evidence under `benchmark_dataset_dir/snapshots/YYYY-MM-DD/`.
**Definition of Done:**
- Each channel ≥30 records, validated twice consecutively.
- Mongo collections include summary, raw posts, latency, feature flags fields; RU content spot-check logged via checklist in `docs/specs/epic_23/checklists/ru_localization_spotcheck.md`.
- Prometheus counter exposes counts per channel.
**CI Gates:** `pytest tests/unit/domain/test_benchmark_dataset.py`, `pytest tests/unit/application/test_seed_benchmark_data.py`, `mypy src/domain src/application`, `make lint`.

### Stage TL-02 · Exporter Verification & Artefact Archiving (Days 5–7)
**Scope:** Guarantee exporters produce JSONL compatible artefacts and align with Stage 05 schema references.
**Tasks:**
1. Create CLI wrappers to run `scripts/quality/analysis/export_digests.py` and `export_review_reports.py` with deterministic seeds.
2. Validate JSONL outputs against schema snapshots; fail build if structure drifts.
3. Automate upload of artefacts to `benchmark_dataset_dir/exports/` with checksum manifest.
4. Document run instructions in `docs/reference/en/PERFORMANCE_BENCHMARKS.md`.
**Definition of Done:**
- Two consecutive exporter runs succeed with ≥50 samples each.
- Schema validation report stored alongside artefacts.
- Checklist appended to `docs/specs/epic_23/epic_23.md#acceptance-checklist`.
**CI Gates:** `python scripts/quality/analysis/export_digests.py --output tmp/digests.jsonl`, `python scripts/quality/analysis/export_review_reports.py --output tmp/reports.jsonl`, `pytest tests/integration/benchmark/test_exporters.py`.

### Stage TL-03 · Benchmark Execution & Stage 05_03 Pilot (Days 7–10)
**Scope:** Execute dry-run and live benchmark scenarios, update documentation, and capture governance approval for Stage 05_03.
**Tasks:**
1. Run `scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru --dry-run` followed by live execution.
2. Collect Prometheus metrics, Grafana screenshots, and Loki log excerpts; store under `docs/reference/en/PERFORMANCE_BENCHMARKS.md`.
3. Execute Stage 05_03 pilot per runbook, including approvals and success/failure summaries.
4. Publish benchmark summary (inputs, latency, error bars) referencing hardware baseline.
**Definition of Done:**
- Benchmarks complete on the target Ryzen 5800 host without manual DB tweaks, with latency metrics recorded for transparency.
- Updated performance document with timestamp and evidence attachments.
- Stage 05_03 pilot log stored and linked from spec.
**CI Gates:** `python scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru --dry-run`, `python scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru`, `pytest tests/integration/benchmark/test_benchmark_runner.py`. Gate checks for completion + metric emission, not a specific SLA unless future requirements add one.

### Stage TL-04 · Day 23 Observability Instrumentation (Days 5–9)
**Scope:** Extend metrics/logging/tracing across runtimes, update observability docs, and add Analyst example showing telemetry metadata.
**Tasks:**
1. Expand metrics modules with counters/histograms listed in architecture packet (`benchmark_export_duration_seconds`, `shared_infra_bootstrap_status`, `structured_logs_total`, `rag_variance_ratio`).
2. Wire `/metrics` endpoints (MCP HTTP server, Butler sidecar, CLI) to shared registry; add health gauges.
3. Implement tracing hooks storing span metadata in Mongo for Analyst self-observation.
4. Update `docs/roles/analyst/day_capabilities.md` and `docs/roles/analyst/examples/` with observability expectations and sample JSON.
5. Create `docs/operational/observability_labels.md` (linked from the Architect handoff bundle + role initialization guide) to capture label taxonomy and keep it in sync with `archive/docs/epic_21/stage_21_03_observability_plan.md`.
**Definition of Done:**
- Curling `/metrics` on all runtimes shows new metrics with non-zero values.
- Loki alert rules and Grafana IaC updated; CI provisioning passes.
- Analyst docs include Day 23 capability + example referencing telemetry metadata.
**CI Gates:** `pytest tests/unit/infrastructure/metrics`, `pytest tests/integration/presentation/test_metrics_endpoints.py`, `mypy src/infrastructure src/presentation`, `bandit -r src`, `make lint`.

### Stage TL-05 · Shared Infra Automation & Restart Validation (Days 6–10)
**Scope:** Automate bootstrap scripts in CI, ensure parity with `make day-12-up`, and prove the single-host stack can restart cleanly (non-DR).
**Tasks:**
1. Integrate `scripts/ci/bootstrap_shared_infra.py` into CI workflow with teardown via `scripts/ci/cleanup_shared_infra.py`.
2. Provide `make day-23-up` wrapper aligning with `.env.infra` and document ownership (DevOps).
3. Run a restart validation (stop/start shared infra on same host, verify metrics/logs resume) and capture evidence in `docs/specs/epic_23/shared_infra_restart.md`, including executed commands (`make day-23-down`, `make day-23-up`, `docker compose ps`) and PromQL/Loki queries used for verification.
4. Emit `shared_infra_bootstrap_status` gauge + logs for CI gating.
**Definition of Done:**
- CI logs show automatic infra bring-up/tear-down with failure gating.
- Restart validation memo (`docs/specs/epic_23/shared_infra_restart.md`) includes objectives, executed command list, PromQL/Loki query snippets, pass/fail summary; no DR drill required this epic.
- Make targets documented in README + operations guide with responsible owner (DevOps).
**CI Gates:** `python scripts/ci/bootstrap_shared_infra.py --check`, `make day-23-up` (implemented during TL-05), `pytest tests/integration/shared_infra/test_bootstrap.py`, `pre-commit run terraform_validate` (if IaC touched).

### Stage TL-06 · Documentation, Localisation & Hygiene (Days 8–11)
**Scope:** Close RU localisation gaps, fix linters, validate YAML/JSON, compress large artefacts, and align README references.
**Tasks:**
1. Update RU docs for MCP/Telegram/CLI plus README.ru/README.md with observability and restart validation info.
2. Fix `shared/tests` lint/type issues; ensure `pre-commit run --all-files` passes cleanly.
3. Repair YAML/JSON files (`config/mcp_config.yaml`, `archive/docker-compose/docker-compose.yml`, `tests/e2e/telegram/fixtures/test_messages.json`).
4. Compress `results_stage20.jsonl` and `results_with_labels.jsonl` <500 KB w/ documented process.
5. Archive legacy async tests referencing `LegacyDialogContextAdapter` in Stage 21 backlog doc.
**Definition of Done:**
- Linters/tests green with no auto-format noise.
- RU/EN docs mention new observability metrics and restart validation.
- Large artefacts within limits with README pointer to compression notes.
**CI Gates:** `pre-commit run --all-files`, `make lint`, `pytest tests/shared`, `check-json`, `check-yaml`.

### Stage TL-07 · RAG++ Reproducibility & Quality Gates (Days 10–13)
**Scope:** Document and implement owner-only RAG++ tuning cadence, randomness controls, variance metrics, and rollout plan updates.
**Tasks:**
1. Extend `config/retrieval_rerank_config.yaml` with `seed`, `variance_window`, `adaptive_threshold` fields.
2. Instrument Prometheus metrics (`rag_variance_ratio`, `rag_fallback_reason_total`) and expose dashboards.
3. Create `docs/specs/epic_23/owner_only/rag_plus_plus_addendum.md` (sanitized for repo, sensitive configs stored outside) detailing tuning strategy, randomness controls, and canary plan; cross-reference Stage 21 materials.
4. Add CI smoke test verifying metrics presence and acceptable variance.
**Definition of Done:**
- Config + docs updated with cadence, knobs, and rollback triggers explicitly scoped to owner-only environments.
- Prometheus metrics live with Grafana visualization and alert thresholds.
- Feature flag rollout checklist appended to plan and limited to owner-only deployments.
**CI Gates:** `pytest tests/unit/rag/test_rag_plus_plus.py`, `pytest tests/integration/rag/test_variance_metrics.py`, `python scripts/rag/day_21_demo.py --dry-run`, `make coverage`.

## 5. CI/CD Gate Matrix
| Gate | Command | Applies To | Threshold | Blocking |
| --- | --- | --- | --- | --- |
| Lint | `make lint` | TL-00…TL-07 | 0 errors | Yes |
| Typecheck | `mypy src/ --strict` | TL-01, TL-04, TL-07 | 100% modules typed | Yes |
| Unit Tests | `pytest tests/unit` | TL-01, TL-04, TL-07 | 100% pass | Yes |
| Integration Tests | `pytest tests/integration` | TL-02, TL-03, TL-04, TL-05 | 100% pass | Yes |
| Coverage | `pytest --cov=src --cov-report=xml` | TL-01, TL-04, TL-07 | ≥80% global | Yes |
| Security | `bandit -r src` | TL-04 | No high/medium | Yes |
| Bootstrap Smoke | `python scripts/ci/bootstrap_shared_infra.py --check` | TL-05 | Exit 0, status gauge=1 | Yes |
| Benchmark Run | `python scripts/quality/benchmark/run_benchmark.py --scenario channel_digest_ru` | TL-03 | Completes on Ryzen 5800 host, emits latency metrics | Yes |
| Restart Validation | `make day-23-up && make day-23-down` (new targets by TL-05) | TL-05 | Exit 0, telemetry resumes | Yes |
| RAG Variance Check | `pytest tests/integration/rag/test_variance_metrics.py` | TL-07 | variance ≤ configured threshold | Yes |

## 6. Traceability Map
| Requirement / Backlog Item | Stage | Acceptance Evidence |
| --- | --- | --- |
| Tasks 1–2 (seed digests/review reports) | TL-01 | Mongo counts report, Prometheus counters, RU spot-check log |
| Task 3 (verify exporters) | TL-02 | JSONL manifest, schema validation output |
| Tasks 4–5 (benchmark & Stage 05 pilot) | TL-03 | Benchmark logs, Stage 05_03 pilot report |
| Task 6 (RU documentation) | TL-06 | README.ru diff, localisation checklist |
| Task 7 (purge legacy assets) | TL-06 | Deployment manifest + checklist |
| Task 8 (shared infra automation) | TL-05 | CI logs, make target output |
| Task 9 (Grafana IaC & Loki alerts) | TL-04 + TL-05 | IaC diffs, CI validation run |
| Task 10 (restart validation of shared infra) | TL-05 | `docs/specs/epic_23/shared_infra_restart.md` evidence |
| Task 11 (backoffice CLI integration tests) | TL-06 | New tests + coverage report |
| Task 12 (shared/tests linters) | TL-06 | pre-commit log |
| Task 13 (YAML/JSON fixes) | TL-06 | check-json/check-yaml logs |
| Task 14 (JSONL compression) | TL-06 | Compression README entry, file sizes |
| Task 15 (legacy async tests catalog) | TL-06 | Stage 21 backlog entry |
| Task 16 (RAG++ extensions) | TL-07 | Config diff, variance metrics dashboard |

## 7. Risk Register
| ID | Description | Impact | Likelihood | Owner | Mitigation |
| --- | --- | --- | --- | --- | --- |
| R1 | Channel data gaps (<30 digests) | High | Medium | Data Services | Synthetic generation script, validation alerts (TL-01). |
| R2 | Exporter schema drift vs Mongo | High | Medium | QA | Schema validation tests + freeze exporter version tags (TL-02). |
| R3 | Benchmark exceeds hardware limits | Medium | Low | Tech Lead | Dry-run first, adjust batch sizes, capture metrics (TL-03). |
| R4 | Observability metrics cause Prometheus cardinality spike | Medium | Low | Observability Lead | Enforce label taxonomy via `ObservabilityPolicy` + new doc (TL-04). |
| R5 | CI bootstrap flaky | High | Medium | DevOps | Health gauge + retries + teardown guard (TL-05). |
| R6 | Restart validation fails due to lingering state | Medium | Low | DevOps | Automate teardown, add sanity checks before restart evidence (TL-05). |
| R7 | Linter hygiene regressions | Low | Medium | Docs Guild | Enforce `pre-commit` gate and shared/tests ownership (TL-06). |
| R8 | RAG++ variance unacceptable in owner env | High | Medium | RAG Taskforce | Introduce adaptive thresholds + rollback plan (TL-07). |

## 8. Telemetry & Evidence Plan
- **Metrics Registration:** Centralize via shared Prometheus registry; each stage adds metrics described in TL-04 to avoid duplication.
- **Logging:** Structured JSON logs enriched with `trace_id`, `epic_id`, `stage_id`, forwarding to Loki; Stage TL-05 validates ingestion during restart validation (not DR).
- **Tracing:** Lightweight spans recorded for exporter runs, benchmark pipeline, and RAG++ evaluations; persisted in Mongo for Analyst self-observation.

| Stage | Evidence Location |
| --- | --- |
| TL-00 | `docs/specs/epic_23/plan_status.md`, `docs/specs/epic_23/acceptance_matrix.md` |
| TL-01 | `benchmark_dataset_dir/snapshots/<date>/channel_counts.json`, Prometheus counter screenshots |
| TL-02 | `benchmark_dataset_dir/exports/<date>/manifest.json`, JSONL schema validation report |
| TL-03 | `docs/reference/en/PERFORMANCE_BENCHMARKS.md`, Stage 05_03 pilot log |
| TL-04 | `docs/operational/observability_labels.md`, updated Analyst docs, `/metrics` snapshots, architect handoff reference |
| TL-05 | CI logs, `docs/specs/epic_23/shared_infra_restart.md`, README updates |
| TL-06 | `pre-commit` reports, README.ru diff, compression notes |
| TL-07 | `docs/specs/epic_23/owner_only/rag_plus_plus_addendum.md`, Grafana `rag_variance.json` |

## 9. Handoff Checklist for Developers
1. Confirm stage ownership and availability; no developer handles more than two concurrent stages.
2. Synchronize environment: run `python scripts/ci/bootstrap_shared_infra.py --check` locally before touching TL-01/02.
3. Adopt TDD: for every new use case/domain object, write pytest skeleton + fixtures prior to implementation.
4. Keep functions ≤15 lines, ensure docstrings follow project format (Purpose/Args/Returns/Raises/Example).
5. Reference this plan in PR descriptions; link CI evidence (lint, tests, coverage, benchmark outputs).
6. Update risk register when new risks emerge or mitigation states change.
7. Provide `/metrics` snapshots and Loki query links within PR templates for observability-related work.

## 10. Next Steps
- [ ] Review this plan with Analyst + Architect for approval (DoD requirement).
- [ ] Kick off TL-01 + TL-05 in parallel once TL-00 sign-off recorded.
- [ ] Schedule shared-host restart validation window and benchmark run on shared calendar.
- [ ] Prepare developer onboarding brief referencing this document and `docs/specs/process/agent_workflow.md`.

Once approvals land, this plan becomes the authoritative Tech Lead handoff for Developers executing Epic 23.
