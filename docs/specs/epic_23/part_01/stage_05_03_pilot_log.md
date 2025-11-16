# Stage 05_03 Pilot Log · EP23 (2025-11-15)

## 1. Metadata
- **Pilot Owner:** dev_a (EP23 TL-03 execution)
- **Scenario:** `channel_digest_ru`
- **Dataset:** `data/benchmarks/benchmark_digest_ru_v1/2025-11-09_samples.jsonl`
- **Prompt version:** `benchmark-2025-11-v1`
- **Baseline model:** `qwen-7b` (dry-run uses stored ground truth)
- **Evaluation model:** `gpt-4o` served via local LLM API (`http://127.0.0.1:8000`)

## 2. Commands Executed
```bash
# Dry-run (ground truth judge)
DB_NAME=benchmark_run PYTHONPATH=. \
python scripts/quality/benchmark/run_benchmark.py \
  --scenario channel_digest_ru --dry-run

# Live evaluation (LLM-as-judge)
DB_NAME=benchmark_run LLM_URL=http://127.0.0.1:8000 PYTHONPATH=. \
python scripts/quality/benchmark/run_benchmark.py \
  --scenario channel_digest_ru
```

## 3. Results Summary
| Metric | Dry-run | Live run (LLM) | Threshold | Status |
| --- | --- | --- | --- | --- |
| Coverage | 0.89 | 0.95 | ≥0.88 pass, ≥0.80 warn | Dry-run: WARN, Live: PASS |
| Accuracy | 0.89 | 0.95 | ≥0.90 pass, ≥0.85 warn | Dry-run: WARN, Live: PASS |
| Coherence | 0.89 | 0.95 | ≥0.90 pass, ≥0.85 warn | Dry-run: WARN, Live: PASS |
| Informativeness | 0.905 | 0.85 | ≥0.88 pass, ≥0.82 warn | Dry-run: PASS, Live: WARN |
| Latency (avg) | 189.0s | 189.0s | ≤210s pass, ≤240s warn | PASS |
| Overall | WARN | WARN | fail-on-warn disabled | WARN |

Live run logged two transient `503 Service Unavailable` responses from the local LLM API; ResilientClient retried successfully, so the run completed with usable metrics.

## 4. Observations & Follow-ups
1. **Informativeness regression:** Live evaluation dipped to 0.85 (WARN). Needs further sampling or fine-tuning (Stage 05_03 target was ≥0.88).  
2. **LLM infrastructure:** Local LLM endpoint occasionally returns 503; monitor shared stack before promoting to CI.  
3. **Stage 05_03 scope:** Fine-tuning itself is still deferred until Epic 23 dataset expansion completes; this pilot only validates benchmark pipeline + governance logging.

## 5. Approvals
- **Tech Lead:** cursor_tech_lead_v1 — _ACK (benchmark pipeline verified, no model promotion)_  
- **Analyst:** cursor_analyst_v1 — _ACK (metrics recorded; requires improved informativeness before go-live)_  
- **Architect:** cursor_architect_v1 — _ACK (pipeline ready; FT postponed pending dataset review)_

> NOTE: Since fine-tuning was not executed in this iteration, overall Stage 05_03 remains in monitoring state. This log satisfies TL-03 DoD for EP23 by documenting the benchmark evidence and governance feedback.

