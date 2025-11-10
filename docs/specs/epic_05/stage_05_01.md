# Stage 05_01 · Benchmark & Dataset Design

## Goal
Define evaluation methodology, dataset schemas, and sampling strategies for
summarisation outputs to support consistent benchmarking and fine-tuning prep.

## Checklist
- [x] Review existing summarisation flows (digest pipeline, reviewer synthesis)
  to identify data sources.
- [x] Define benchmark scenarios (e.g., channel digests, review summaries) and
  target metrics (coverage, accuracy, coherence, informativeness).
- [x] Design dataset schema including metadata (language, source, timestamps,
  evaluator judgments).
- [x] Establish sampling strategy (frequency, volume, language mix).
- [x] Produce evaluation backlog with required automation tasks for Stage 05_02.

## Deliverables
- Benchmark plan document with scenarios, metrics, and acceptance thresholds.
- Dataset schema specification and initial sample dataset.
- Backlog of automation tasks with priorities and owners.

## Summary

- Benchmark plan published (`stage_05_01_benchmark_plan.md`) covering RU channel
  digest and reviewer summary scenarios, including metric thresholds and release
  cadence.
- Dataset schema (`stage_05_01_dataset_schema.json`) and seeded samples
  (`data/benchmarks/benchmark_digest_ru_v1/2025-11-09_samples.jsonl`) provide RU
  baseline for Stage 05_02 automation.
- Stage 05 scoreboard scaffold added to `docs/reference/en/PERFORMANCE_BENCHMARKS.md` pending
  automated runs.
- Automation backlog (`stage_05_02_backlog.md`) prioritises evaluation runner, CI
  smoke tests, metric exports, and supporting scripts.
- Worklog (`stage_05_01_worklog.md`) captures decisions on RU focus, LLM judge usage,
  retention handling, and dataset statistics.

## Starter Kit
- See `docs/specs/epic_05/stage_05_01_starter_kit.md` for available artefacts,
  data extraction commands, and templates (dataset schema, scoreboard).

## Metrics & Evidence
- Sample dataset statistics (counts, language distribution).
- Draft benchmark scoreboard template (even if manual initially).
- Stakeholder approval notes (architecture, ML lead).

## Dependencies
- Reviewer artefacts and digest outputs available via shared storage.
- Coordination with EP01/EP03 for metrics/logging alignment.

## Exit Criteria
- Benchmark plan approved and published.
- Sample dataset validated and stored in agreed location.
- Automation tasks prioritised for Stage 05_02, no open blockers.

## Open Questions
- Do we include human-in-the-loop evaluations at this stage?
- What data retention policies apply to stored datasets?
