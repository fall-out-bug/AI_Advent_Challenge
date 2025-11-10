# Stage 05_01 Benchmark Plan

## Overview

Stage 05_01 establishes reproducible benchmarks for RU-language summarisation flows
covering daily channel digests and modular reviewer synthesis outputs. The plan
defines scenarios, metrics, acceptance thresholds, and evaluation cadences that
Stage 05_02 automation must implement. All evaluations rely on the existing shared
infrastructure (Mongo, Prometheus, LLM API) and conform to Clean Architecture
boundaries.

## Benchmark Scenarios

### Scenario A — Channel Digest (RU)

- **Scope:** Telegram channel digests generated via `generate_channel_digest_by_name`
  (presentation layer MCP + summary worker pipeline).
- **Source Collections:** `digests`, `mcp_logs` (latency/error context).
- **Feature Flags:** `use_new_summarization`, `enable_quality_evaluation`,
  `enable_async_long_summarization` (record effective values per sample).
- **Cadence:** Execute on every minor/major release with optional on-demand reruns
  when new prompt versions or LLM models are introduced.

| Metric | Definition | Target (Pass) | Warning Band | Fail Criteria | Measurement Notes |
|--------|------------|---------------|---------------|---------------|-------------------|
| Coverage | Fraction of salient source facts captured in summary. | ≥ 0.88 | 0.80–0.87 | < 0.80 | LLM judge score (`coverage`) averaged across samples. |
| Accuracy | Absence of hallucinations or factual errors. | ≥ 0.90 | 0.85–0.89 | < 0.85 | Cross-check with LLM judge reasoning; flag samples with redline errors. |
| Coherence | Logical flow and readability of the summary. | ≥ 0.90 | 0.85–0.89 | < 0.85 | Weighted by per-paragraph coherence. |
| Informativeness | Degree of actionable insight delivered. | ≥ 0.88 | 0.82–0.87 | < 0.82 | Derived from judge verdict plus rubric prompts. |
| Latency P95 | Time from MCP invocation to digest persisted. | ≤ 210s | 211–240s | > 240s | Instrumentation via `review_pipeline_latency_seconds` histogram. |

### Scenario B — Reviewer Summary (RU)

- **Scope:** Modular reviewer synthesis outputs for RU submissions (architecture +
  component + synthesis passes).
- **Source Collections:** `review_reports`, `mcp_logs`, Prometheus metrics exposed by
  modular reviewer once Stage 05_02 wiring completes.
- **Feature Flags:** `use_modular_reviewer`, `enable_log_analysis`, `enable_quality_evaluation`.
- **Cadence:** Same release-based schedule; trigger reruns when reviewer prompt packs
  or weighting logic change.

| Metric | Definition | Target (Pass) | Warning Band | Fail Criteria | Measurement Notes |
|--------|------------|---------------|---------------|---------------|-------------------|
| Coverage | Alignment of summary to issues found across passes. | ≥ 0.87 | 0.80–0.86 | < 0.80 | Judge prompt compares synthesis vs. pass artefacts. |
| Accuracy | Fidelity of reported findings to detected code issues. | ≥ 0.90 | 0.85–0.89 | < 0.85 | Cross-validate against automated assertions in unit tests. |
| Coherence | Narrative flow across passes and final verdict. | ≥ 0.88 | 0.82–0.87 | < 0.82 | Evaluate section transitions and instruction clarity. |
| Informativeness | Actionable guidance for students. | ≥ 0.88 | 0.82–0.87 | < 0.82 | Judge rubric emphasises remediation steps. |
| Latency P95 | Review completion time (MCP call → report stored). | ≤ 300s | 301–360s | > 360s | Uses combined MCP + worker histograms. |

## Evaluation Methodology

- **Judge Model:** `gpt-4o` via shared OpenAI-compatible endpoint (`LLM_URL`), prompt
  version `benchmark-2025-11-v1`.
- **Prompt Governance:** Store prompt templates under
  `docs/specs/epic_05/prompts/benchmark_2025_11_v1.md` (to be generated during Stage
  05_02) and reference version in datasets.
- **Scoring Pipeline:** For each sample, persist judge responses alongside metadata
  (`language`, `channel`, `llm_model`, feature flag snapshot) matching dataset schema.
- **Aggregation:** Compute per-scenario averages, warn on metrics entering warning
  band, and fail pipeline when any metric crosses the fail threshold.
- **Observability Tie-in:** Map latency metrics to `review_pipeline_latency_seconds`,
  `mcp_request_duration_seconds`, and planned Stage 05 instrumentation; publish
  gauges for current pass/fail state.

## Release Cadence & Reporting

- **Baseline Run:** Prior to next RU release candidate; publish results in
  `docs/reference/en/PERFORMANCE_BENCHMARKS.md` under “Stage 05 Benchmarks”.
- **Release Regression:** Required before each tagged release (minor/major). Record
  run IDs and dataset snapshots in worklog.
- **On-Demand Runs:** Allowed for experiments; label results as `experimental` and
  avoid committing raw confidential data.
- **Stakeholder Review:** Summaries shared with ML lead and operations owner for
  sign-off; issues logged if any metric enters failure band.

## Dependencies & Risks

- **Data Quality:** Pending issues tracked in `docs/specs/epic_04/known_issues.md`.
  Samples must exclude channels flagged as degraded.
- **Automation Backlog:** Stage 05_02 must implement LLM judge automation, dataset
  exporters, Prometheus publishing, and dashboard updates reflecting these metrics.
- **Human Evaluation:** Out of scope for Stage 05_01; schedule follow-up initiative
  once RU automation stabilises.
- **Retention:** Adhere to worklog decision — raw datasets stored in-repo only until
  Stage 05_02 completes; afterward shift to external storage with anonymised
  snapshots.

## Deliverables Summary

- `docs/specs/epic_05/stage_05_01_benchmark_plan.md` (this document).
- Initial dataset schema (`stage_05_01_dataset_schema.json`) and samples under
  `data/benchmarks/benchmark_digest_ru_v1/`.
- Updated `docs/reference/en/PERFORMANCE_BENCHMARKS.md` Stage 05 scoreboard scaffold.
- Stage 05_02 backlog outlining automation tasks aligned with scenarios above.
