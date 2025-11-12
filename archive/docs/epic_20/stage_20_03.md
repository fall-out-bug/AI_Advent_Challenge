# Stage 20_03 · Implementation & Tests

## Goal
Ship the agent/CLI supporting two modes (with RAG / without RAG), including
basic tests and metrics.

## Checklist
- [ ] Implement application use case `CompareRagAnswersUseCase`.
- [ ] CLI commands:
  - `rag:compare --question "..."` (single run)
  - `rag:batch --queries docs/specs/epic_20/queries.jsonl --out results.jsonl`
- [ ] Metrics: `rag_compare_duration_ms`, `retrieved_chunks_total`.
- [ ] Tests: unit for prompt assembly, retrieval; integration against small index.
- [ ] Config via env (`RAG_TOP_K`, `RAG_SCORE_THRESHOLD`, index namespace).

## Deliverables
- Agent wiring under `src/application/use_cases/` and CLI in `src/presentation/cli/`.
- Test suite green for module/unit; integration guarded behind fixtures.

## Exit Criteria
- CLI works locally (shared infra up).
- Tests pass in CI for unit scope; integration optional with markers.
