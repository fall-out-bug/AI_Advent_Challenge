# Stage 05_01 Starter Kit · Benchmarks & Datasets

Use this kit as the single reference for kick-starting Stage 05_01. It gathers
existing artefacts, commands, and templates so the agent can jump straight into
designing benchmarks and datasets.

---

## 1. Existing Artefacts to Reuse

| Area | Artefact | Notes |
|------|----------|-------|
| Performance baselines | `docs/reference/en/PERFORMANCE_BENCHMARKS.md` | Extend with new benchmark results (add Stage 05 sections). |
| Observability metrics | `docs/specs/epic_03/metrics_inventory.json` | Contains current Prometheus metric names (latency, error counts). |
| SLO guidance | `docs/specs/epic_03/slo_recommendations.md` | Reuse SLO targets for reviewer latency/accuracy. |
| Flag context | `docs/specs/epic_01/stage_01_01_feature_flag_inventory.md` | Track toggles that affect dataset sampling. |
| MCP scope | `docs/specs/epic_02/mcp_tool_matrix.md` | Defines active tools and payloads for digest/review flows. |
| Known issues | `docs/specs/epic_04/known_issues.md` | Check open items impacting data quality (e.g., xfails). |
| Automation backlog | `docs/specs/epic_06/stage_06_01_backlog.md` | Cross-link tasks that Stage 05_02 must deliver. |

---

## 2. Environment & Data Source Cheat Sheet

```bash
# Load shared infra credentials
export $(grep -v '^#' ~/work/infra/.env.infra | xargs)
export MONGODB_URL="mongodb://$MONGO_USER:$MONGO_PASSWORD@127.0.0.1:27017/butler?authSource=admin"
export LLM_URL=http://127.0.0.1:8000
export PROMETHEUS_URL=http://127.0.0.1:9090

# Recommended Mongo collections for sampling
# - digests: summaries for Telegram channels
# - review_reports: modular reviewer outputs
# - mcp_logs: tool invocations (for latency/error metrics)
```

Sample aggregation to fetch recent digests (24h window):

```bash
poetry run python scripts/quality/analysis/export_digests.py \
  --mongo "$MONGODB_URL" \
  --hours 24 \
  --output data/benchmarks/digest_samples_$(date +%Y%m%d).jsonl
```

Для отчётов ревью используйте `scripts/quality/analysis/export_review_reports.py` с
аналогичными параметрами (`--hours`, `--limit`, `--output`).

Add similar exporters as needed (e.g., reviewer reports, LLM judge responses).

---

## 3. Dataset Schema Template

```json
{
  "dataset_id": "benchmark_digest_ru_v1",
  "description": "Daily Telegram digest summaries for RU channels",
  "created_at": "2025-11-11T10:00:00Z",
  "source": {
    "collection": "digests",
    "query_window_hours": 24,
    "language": "ru"
  },
  "samples": [
    {
      "sample_id": "digest-2025-11-10-0001",
      "channel": "@example_channel",
      "language": "ru",
      "timestamp": "2025-11-10T19:05:00Z",
      "summary_markdown": "...",
      "metadata": {
        "posts_count": 18,
        "time_range_hours": 24,
        "llm_model": "qwen"
      },
      "ground_truth": {
        "human_rating": {
          "coverage": 0.9,
          "accuracy": 0.85,
          "coherence": 0.88,
          "informativeness": 0.92,
          "notes": "Needs more emphasis on product launch details."
        },
        "llm_judge": {
          "model": "gpt-4o",
          "prompt_version": "benchmark-2025-11-v1",
          "scores": {
            "coverage": 0.91,
            "accuracy": 0.83,
            "coherence": 0.90,
            "informativeness": 0.94
          },
          "verdict": "MEETS_EXPECTATIONS"
        }
      }
    }
  ]
}
```

Save initial samples under `data/benchmarks/<dataset_id>/` (JSONL or Parquet).

---

## 4. Benchmark Scoreboard Template

Embed in `docs/reference/en/PERFORMANCE_BENCHMARKS.md` (new section “Stage 05 Benchmarks”):

```
| Scenario | Dataset | Model | Coverage | Accuracy | Coherence | Informativeness | Latency P95 | Notes |
|----------|---------|-------|----------|----------|-----------|-----------------|-------------|-------|
| Channel Digest (RU) | benchmark_digest_ru_v1 | qwen-7b | 0.90 | 0.85 | 0.88 | 0.92 | 3.4s | LLM judge v1 |
| Review Summary (EN) | benchmark_review_en_alpha | qwen-7b | ... | ... | ... | ... | ... | Early sample |
```

---

## 5. Suggested Task Breakdown (Stage 05_01)

1. **Artefact review (0.5d)**
   Catalogue existing metrics, confirm data availability, log findings in `stage_05_01_worklog.md`.
2. **Benchmark design (1d)**
   Draft scenarios + metrics; present in `stage_05_01_benchmark_plan.md`.
3. **Dataset schema & sampling (1d)**
   Populate schema template, export first samples, store under `data/`.
4. **Backlog creation (0.5d)**
   Translate automation needs into Stage 05_02 backlog (`stage_05_02_backlog.md`).

---

## 6. Reporting & Documentation Targets

- `docs/specs/epic_05/stage_05_01_worklog.md` — daily notes, commands run, issues.
- `docs/specs/epic_05/stage_05_01_benchmark_plan.md` — final plan (create file on completion).
- `docs/specs/epic_05/stage_05_01_dataset_schema.json` — machine-readable schema (optional).
- Update `docs/reference/en/PERFORMANCE_BENCHMARKS.md` & `README`/`README.ru` once initial benchmarks validated.

---

## 7. Questions to Confirm Early

- Which language/locale mix has highest priority (RU-only vs RU+EN)?
- Are human raters available, or rely on LLM-as-judge only for Stage 05_01?
- Data retention constraints (how long to keep raw samples in repo).
- Required cadence for benchmark refresh (per release vs nightly).

Capture answers in `stage_05_01_worklog.md` to unblock Stage 05_02 automation.
