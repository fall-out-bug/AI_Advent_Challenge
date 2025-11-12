# Stage 21_02 · Design & Prototype

## Goal
Design the filtering/rerank pipeline and deliver a prototype that compares Baseline, RAG, and RAG++ for a single query.

## Checklist
- [ ] Filtering: drop chunks below `score_threshold`; keep top_k after filter.
- [ ] Reranker (optional): re‑score candidates via cross‑encoder/LLM scoring.
- [ ] Prompting: assemble RAG++ prompt with citations preserving traceability.
- [ ] Prototype script `scripts/rag/rerank_once.py` prints side‑by‑side outputs.

## Deliverables
- Design note with data flow and component responsibilities.
- Prototype demonstrating three modes on a sample query.

## Exit Criteria
- Prototype outputs answers and basic stats without errors.
