# Stage 20_02 · Design & Prototype

## Goal
Design the retrieval + prompting workflow and deliver a working prototype that
shows side‑by‑side answers for a single query.

## Checklist
- [ ] Retrieval adapter: connect to EP19 index (Redis/FAISS + Mongo metadata).
- [ ] Prompting: assemble RAG prompt (question + top_k chunks + citations).
- [ ] Non‑RAG baseline: plain question to LLM with same system instructions.
- [ ] Comparison output: side‑by‑side JSON lines (`id`, `question`, `with_rag`,
  `without_rag`, `chunks_used`, `latency_ms`).
- [ ] Optional judge: call LLM‑as‑judge to label which answer is better.

## Deliverables
- Prototype script `scripts/rag/compare_once.py` for a single query.
- Design note `docs/specs/epic_20/design.md` with component diagram.

## Exit Criteria
- Prototype returns both answers and prints basic stats for a sample query.
