# EP23 Owner-Only Addendum · RAG++ Reproducibility

**Access:** This document contains strategy guidance only. No secrets, API keys, or proprietary prompts should be stored here. Sensitive configs live in the private owner repo (`ops/owner_only/secure_configs/`).
**Scope:** Supports TL-07 tasks (reproducibility knobs, variance metrics, canary rollout).

## 1. Tuning Cadence

- **Frequency:** Start with fortnightly RAG++ tuning, move to weekly once traffic and telemetry stabilise.
- **Entry Point:** Use `scripts/rag/day_21_demo.py` (owner-only corpora) to run comparison batches.
- **Sample Size:** Minimum 50 queries per run (mix of EN/RU, architecture/docs/homework categories).
- **Process:**
  1. Freeze config snapshot (see Evidence Log) and feature flag state.
  2. Run `python scripts/rag/day_21_demo.py --dry-run` against fixed query set.
  3. Capture metrics: `rag_rerank_score_variance`, `rag_variance_ratio{window="current"}`, `rag_fallback_reason_total`.
  4. Compare against previous run; only promote changes when variance and fallback rates stay within thresholds.
- **Ownership:** RAG++ owner (data/ML engineer) signs off each tuning run before rollout.

## 2. Randomness Controls

- **Config Mapping:** `config/retrieval_rerank_config.yaml` now includes owner-only knobs:

  ```yaml
  reranker:
    enabled: true
    strategy: "llm"
    seed: 123                # owner-only seed for reproducible runs
    variance_window: "current"
    adaptive_threshold: 0.5  # max acceptable variance for promotion
    llm:
      model: "mistral:7b-instruct"
      temperature: 0.3
      max_tokens: 256
      timeout_seconds: 3
  ```

- **Semantics:**
  - `seed`: Logged by `LLMRerankerAdapter` on each run; use external tooling to enforce deterministic sampling.
  - `temperature`: Controlled via config and `RAG_RERANK_TEMPERATURE` env override in owner-only environments.
  - `variance_window`: Label for `rag_variance_ratio` gauge (e.g. `current`, `rolling_5m`).
  - `adaptive_threshold`: Upper bound for acceptable variance; values above threshold block promotion.
- **Sanitisation Guidance:**
  - Use non-secret placeholders in repo configs (e.g. `seed: 123`, generic model names).
  - Store real owner-only configs under `ops/owner_only/secure_configs/` and keep them out of git.
  - Never commit concrete production prompts or tenant-specific corpora.

## 3. Variance Metrics & Dashboards

- **Metrics:**
  - `rag_rerank_score_variance` (histogram) — distribution of per-run variance.
  - `rag_variance_ratio{window="current"}` (gauge) — normalised variance value used for gates.
  - `rag_fallback_reason_total{reason="timeout|parse_error|exception"}` (counter) — fallback reasons.
- **Thresholds (owner-only recommendation):**
  - `rag_variance_ratio{window="current"}` ≤ `adaptive_threshold` (default 0.5) for promotion.
  - `rag_fallback_reason_total{reason!="timeout"}` low and stable (no spikes after tuning).
- **Dashboards:**
  - Extend `grafana/dashboards/stage05-benchmarks.json`:
    - Timeseries for `rag_variance_ratio{window="current"}`.
    - Stacked lines for `rag_fallback_reason_total` by `reason`.
  - Owner-only Grafana folder: `RAG++ / Variance & Fallbacks` (configured outside repo).

## 4. Canary Rollout Plan (Feature Flag `enable_rag_plus_plus`)

- **Preconditions:**
  - `feature_flags.enable_rag_plus_plus` disabled by default in public configs.
  - Variance and fallback metrics within thresholds on owner-only staging.
- **Rollout Steps (owner-only stack):**
  1. Enable `enable_rag_plus_plus` for 5–10% of traffic (internal users only).
  2. Monitor `rag_variance_ratio` and `rag_fallback_reason_total` for 24–48h.
  3. If stable, increase to 25% → 50% → 100% with checkpoints after each step.
  4. Keep non-RAG baseline route available for quick rollback.
- **Rollback Triggers:**
  - `rag_variance_ratio{window="current"}` persistently exceeds `adaptive_threshold`.
  - Sudden spike in `rag_fallback_reason_total{reason!="timeout"}`.
  - Qualitative degradation in answer quality reported by reviewers.
- **Checklist (owner-only):**
  - [ ] Feature flag rollout plan documented in internal runbook.
  - [ ] Alerts configured on variance & fallback thresholds.
  - [ ] Rollback procedure tested on staging.

## 5. Evidence Log

| Date | Config Hash (sanitised) | Seed | Adaptive Threshold | Variance (current) | Fallback Rate | Notes / Links |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-11-16 | `cfg-ep23-ragpp-v1` | 123 | 0.5 | 0.23 | 2% (`timeout` only) | Baseline Epic 23 tuning; screenshots stored in owner-only Grafana folder. |

## Sanitization Rules
- Replace concrete secrets with placeholders (e.g., `<OWNER_API_KEY>`).
- Store raw logs/metrics with personal data outside repo; only link to secure storage.
- Tag each update with version + author for traceability.

## Change Log
| Version | Date | Author | Summary |
| --- | --- | --- | --- |
| v0.1 | 2025-11-15 | cursor_tech_lead_v1 | Scaffold created; populate once TL-07 kicks off. |
