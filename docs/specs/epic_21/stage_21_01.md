# Stage 21_01 · Requirements & Question Set Update

## Goal
Define filtering/rerank requirements, extend the EP20 query set for ablation, and set initial thresholds/metrics.

## Checklist
- [ ] Extend `docs/specs/epic_20/queries.jsonl` with filter‑sensitive questions.
- [ ] Define retrieval config (`retrieval_rerank_config.yaml`): `top_k`, `score_threshold`, `reranker=off|cross_encoder|llm_score`.
- [ ] Choose minimal metrics: coverage, accuracy, coherence, helpfulness (reuse EP05 judge prompts if needed).
- [ ] Document assumptions: chunk size/overlap, index namespace, languages.

## Deliverables
- Updated `queries.jsonl`.
- `retrieval_rerank_config.yaml` (checked into repo).
- Short note describing metrics and expected effects.

## Exit Criteria
- Config approved; queries saved.
- No blockers for Stage 21_02.
