# Stage 05_02 · Automation & Evaluation Tooling

## Goal
Build automation that scores summarisation outputs, curates datasets, and
surfacing results via dashboards for stakeholders.

## Checklist
- [x] Implement LLM-as-judge evaluation pipeline based on benchmark plan.
- [x] Automate dataset export, versioning, and storage (include metadata from
  Stage 05_01 schema).
- [ ] Integrate evaluation metrics into observability stack (dashboards,
  reports).
- [ ] Validate automation through pilot runs and sanity checks.
- [x] Document usage instructions and troubleshooting for automation scripts.

## Deliverables
- Automated evaluation pipeline (scripts, configs, CI jobs where applicable).
- Dataset export tooling with version control and catalog entries.
- Dashboard or reporting mechanism showing evaluation results over time.
- Stage summary capturing pilot outcomes and identified improvements.

## Metrics & Evidence
- Pilot run logs with evaluation scores and dataset snapshots.
- Dashboard screenshots or URLs.
- Audit trail of dataset versions produced during the stage.

## Dependencies
- Stage 05_01 plan, schema, and sample datasets.
- EP03 observability infrastructure for dashboard integration.
- Access to LLM API and storage services.

## Exit Criteria
- Automation runs end-to-end on sample data with results validated by reviewers.
- Dashboards/reports accessible to stakeholders with up-to-date metrics.
- Backlog items for further enhancements documented and prioritised.

## Open Questions
- Do we require human review of LLM-as-judge outputs before accepting results?
- How frequently should automation run (per release, nightly, on-demand)?

## Progress (2025-11-11)
- Added benchmarking application module with async runner, metric aggregation,
  and Prometheus recorder (see `src/application/benchmarking/`).
- Delivered infrastructure adapters (JSONL dataset provider, summarisation judge
  adapter, factory wiring) plus CLI entry point
  `scripts/benchmark/run_benchmark.py`.
- Authored dataset exporters `scripts/quality/analysis/export_digests.py` and
  `scripts/quality/analysis/export_review_reports.py` to populate RU benchmark datasets
  with `source_text`, feature flags, and latency metadata.
- Compiled operational guidance in
  `docs/specs/epic_05/stage_05_02_runbook.md` covering exports, benchmark runs,
  and metric verification.
- Added Grafana dashboard definition `grafana/dashboards/stage05-benchmarks.json`
  with panels for metric values and latest outcomes (import via provisioning).
- Executed dry-run benchmark (`channel_digest_ru`) via CLI/CI flow; coverage and
  accuracy currently in warning band (0.89) with latency average 189.05s.
- Added unit tests for benchmarking runner and JSONL dataset provider to guard
  aggregation logic (`tests/unit/application/benchmarking/test_runner.py`).
- Live benchmarks blocked: shared Mongo lacks digest/review samples. Seeding
  tasks moved to future Epic 23 backlog.

## Summary
- Аналитическая инфраструктура для Stage 05 готова: раннер, экспортеры,
  dry-run CI, документация и Grafana-дэшборд поставлены.
- Первичный прогон (dry-run) показал предупреждения по coverage/accuracy —
  требуется дополнительный контроль на живых данных.
- Полноценные live-прогоны заблокированы отсутствием дайджестов/отчётов в
  Mongo; импорт и повторный запуск вынесены в Epic 23.
