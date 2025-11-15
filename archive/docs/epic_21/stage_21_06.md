# Stage 21_03 · Implementation & Tests

## Goal
Ship filtering/rerank into the agent/CLI with flags and basic tests.

## Checklist
- [ ] CLI additions:
  - `rag:compare --question "..." --filter --threshold 0.35 --reranker off|cross_encoder|llm`
  - `rag:batch --queries ... --filter --threshold ...`
- [ ] Metrics: `rag_rerank_duration_ms`, `rag_chunks_filtered_total`, `rag_rerank_win_total`.
- [ ] Tests: unit (filtering, scoring), integration against small index.
- [ ] Config via env and `retrieval_rerank_config.yaml`.

## Deliverables
- Updated agent/CLI; tests; metrics wiring.

## Exit Criteria
- CLI works locally; unit tests pass in CI; integration runs behind marker.
