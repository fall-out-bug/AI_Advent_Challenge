# Epic 21 · Console Chat Demo — Developer Tasks

Status: READY FOR IMPLEMENTATION
Owners: Dev A (CLI/scripts), Dev B (Make/metrics), QA (acceptance)

---

## Task Breakdown (DoD + Evidence)

1) Create demo queries
- Path: `docs/specs/epic_21/demo_queries.jsonl`
- Content: 10 questions from `DEMO_TASK.md` (ids 1..10)
- DoD: File exists; JSONL valid; ids and questions match spec
- Evidence: PR diff + quick `jq` validation

2) Make targets
- Path: `Makefile`
- Targets: `day_21_demo`, `day_21_batch`, `day_21_metrics`
- DoD: Targets run locally without manual steps
- Evidence: Console logs pasted in PR; CI command job optional

3) Interactive demo runner (chat style)
- Path: `src/presentation/cli/backoffice/commands/demo_ep21.py` (or similar)
- Behavior: Iterate 10 questions; run modes: Baseline, RAG, RAG++ (0.30, llm), RAG++ aggressive (0.60, off)
- Output: Per-question section; filtered count; reordered yes/no; top-score delta
- DoD: Runs with `make day_21_demo`; prints all required fields
- Evidence: Sample console output attached in PR

4) Batch runner
- Path: reuse `rag batch` via Make target; output to `var/results_ep21.jsonl`
- Flags: `--filter --threshold 0.30 --reranker llm`
- DoD: File created with N=10 results; prints brief summary
- Evidence: File exists; line count = 10; summary on stdout

5) Metrics snapshot tool
- Path: small script or Make recipe to fetch `/metrics`
- Output: print only key `rag_*` lines:
  - `rag_rerank_duration_seconds{strategy}`
  - `rag_chunks_filtered_total{category}`
  - `rag_rerank_score_delta`
  - `rag_reranker_fallback_total{reason}`
  - `rag_rerank_score_variance`
- DoD: `make day_21_metrics` prints lines above
- Evidence: Console output in PR

6) Fallback demonstration
- Method: Temporarily set `RAG_RERANK_TIMEOUT=1` (or lower) for one question
- Expectation: Reranker times out once; fallback reasoning visible; counter increments
- DoD: Shown during `day_21_demo`; counter `...fallback_total{reason="timeout"}` increments
- Evidence: Console shows fallback note; metrics snapshot shows increment

7) Rollback drill (feature flag)
- Method: Toggle `feature_flags.enable_rag_plus_plus` true → run one question; then false → run same question
- Expectation: Behavior changes without code changes (RAG++ vs RAG)
- DoD: Integrated in demo flow or separate `make day_21_rollback_drill`
- Evidence: Console diff; metrics reset check (optional)

8) Config precedence demonstration
- Case: Provide CLI override (`--threshold 0.60`) while YAML=0.30 and env unset
- Expectation: Effective threshold = 0.60 (visible change in chunks/length)
- DoD: Demonstrated once in demo run; printed notice of override
- Evidence: Console output shows effect and printed note

9) Demo guide
- Path: `docs/specs/epic_21/DEMO.md`
- Content: scenario, commands, sample output, how to trigger fallback and rollback, where artifacts saved
- DoD: Complete mini guide; reviewed by TL
- Evidence: Doc in PR; links to artifacts

10) Output format & logging
- Output: Per question — Q, Baseline, RAG, chunks (path + score), RAG++ extras (reordered, top-score delta)
- Logging: Structured logs, query truncated to 50 chars
- DoD: Verified in interactive demo; no PII in logs
- Evidence: Sample output + code snippet of logging config

---

## Commands (expected wiring)

```bash
# Interactive demo
make day_21_demo

# Batch run
make day_21_batch

# Metrics snapshot
make day_21_metrics
```

---

## Acceptance Checklist (QA)

- [ ] 10 questions processed in interactive demo with required format
- [ ] Baseline ≠ RAG ≠ RAG++ for at least one question
- [ ] Threshold=0.60 mode visibly reduces context length
- [ ] Fallback demonstrated; timeout counter incremented
- [ ] `/metrics` available; key `rag_*` lines printed
- [ ] Rollback drill toggles behavior via feature flag only
- [ ] Config precedence demo shows CLI override effect
- [ ] Batch results saved to `var/results_ep21.jsonl` with brief summary

---

## Notes

- Defaults per spec: threshold=0.30, reranker off, feature flag off; temperature=0.5
- No canary rollout; single feature flag toggle only
