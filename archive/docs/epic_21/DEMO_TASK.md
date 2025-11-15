# Epic 21 · Console Chat Demo — Implementation Task

## Purpose
- Demonstrate Baseline vs RAG vs RAG++ (Filter + LLM Rerank) in an interactive console “chat” style, with metrics, fallback, and rollback drills.

## Scope
- Console demo with typewriter-like output (persona optional).
- 10 questions, run per question across multiple configurations.
- Batch run, metrics snapshot, rollback drill.

## Must
- Provide Make targets:
  - `make day_21_demo` — interactive run for 10 questions across modes.
  - `make day_21_batch` — batch run for the same 10 questions, saves results.
  - `make day_21_metrics` — prints rag_* metrics snapshot from `/metrics`.
- Modes per question (run sequentially for the same question):
  - Baseline (no RAG): no context.
  - RAG (no filter, no rerank).
  - RAG++ (filter threshold=0.30, reranker=llm).
  - RAG++ aggressive (filter threshold=0.60, reranker=off).
- Show fallback: force LLM reranker timeout once → increment `rag_reranker_fallback_total{reason="timeout"}` and surface fallback reasoning.
- Show rollback drill: enable feature flag, run one question with RAG++, disable flag, repeat same question; behavior must change without code changes.
- Respect config precedence: CLI > YAML > ENV > Defaults; demonstrate at least one override case.
- Structured logs without PII (query truncated to 50 chars remains in place).

## Should
- Personas (as in Day 20): normal / sarcastic — affects only answer generation temperature (not reranker behavior).
- Short demo guide: `docs/specs/epic_21/DEMO.md` (scenario, commands, expected artifacts).

## Out of Scope
- Canary rollout and cross-encoder strategy.
- Web/GUI.

## Inputs / Artifacts
- Config: `config/retrieval_rerank_config.yaml` (defaults: threshold=0.30, reranker off, feature flag off).
- Demo questions (10) → create `docs/specs/epic_21/demo_queries.jsonl` with entries (id, question):
  1) Что такое Clean Architecture и какие ограничения по импортам?
  2) Как оформлять Docstring и типизацию согласно правилам репозитория?
  3) Что такое MapReduce и как устроены map/shuffle/reduce?
  4) Когда RAG не улучшит ответ и почему (failure modes)?
  5) Какие директории индексируются в проекте и как хранится метадата чанков?
  6) Как устроен Feature Flag для RAG++ и как выполнить rollback?
  7) Какие метрики экспортируются для RAG++ и что они означают?
  8) Как работает фильтрация по порогу similarity и её риски?
  9) Как устроен LLM reranker и fallback при timeout/parse_error?
  10) Какой приоритет конфигурации (CLI > YAML > ENV > Defaults) и пример?
- Batch results: `var/results_ep21.jsonl` (+ brief summary to stdout).

## Demo Flow (Command Requirements)
- Interactive (chat emulation):
  - `make day_21_demo`
  - Iterate 10 questions; for each, run 3–4 modes listed in Must.
  - For RAG++ explicitly print: filtered count, reordered state, top-score delta.
- Batch:
  - `make day_21_batch`
  - Run 10 questions with `--filter --threshold 0.30 --reranker llm`, save to `var/results_ep21.jsonl`.
- Metrics:
  - `make day_21_metrics` → fetch `/metrics` and print key rag_* lines:
    - `rag_rerank_duration_seconds{strategy}`
    - `rag_chunks_filtered_total{category}`
    - `rag_rerank_score_delta`
    - `rag_reranker_fallback_total{reason}`
    - `rag_rerank_score_variance`
- Rollback:
  - Toggle `feature_flags.enable_rag_plus_plus` true → run one question (RAG++), then false → repeat; verify effect.
- Fallback:
  - Temporarily minimize reranker timeout (CLI/ENV) → run one question → show fallback note and metric increment.

## Output Requirements
- Per question print:
  - Q: <text>
  - Без RAG: <answer>
  - С RAG: <answer>
  - Chunks:
    - `path:line? (score=0.xx)` … 3–5 lines
  - If RAG++: `Reordered: yes|no, top-score delta: +0.xx`
- Session summary:
  - Total chunks filtered
  - Avg rerank duration (approx from histogram sample)
  - Fallback count by reason

## Acceptance Criteria
- All 10 questions processed in interactive demo with the required output format.
- For at least one question: Baseline ≠ RAG ≠ RAG++ (by chunks/order/citations).
- Filtering visibility: threshold=0.60 reduces context length noticeably.
- Fallback demonstrated; `rag_reranker_fallback_total{reason="timeout"}` incremented.
- Metrics are available at `/metrics`; console shows key rag_* lines.
- Rollback drill toggles behavior solely via feature flag.
- Config precedence demo: a CLI override changes behavior vs YAML.
- Batch run saves `var/results_ep21.jsonl` and prints a brief summary.

## Definition of Done
- Make targets available:
  - `make day_21_demo`
  - `make day_21_batch`
  - `make day_21_metrics`
  - (optional) `make day_21_rollback_drill` if not integrated in `day_21_demo`
- File `docs/specs/epic_21/demo_queries.jsonl` contains 10 questions above.
- File `docs/specs/epic_21/DEMO.md` explains scenario, commands, sample output, how to trigger fallback and rollback.
