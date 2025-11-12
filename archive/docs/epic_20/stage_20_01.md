# Stage 20_01 · Requirements & Question Set

## Goal
Define the query set, retrieval parameters, and comparison rubric for RAG vs
non‑RAG evaluation.

## Checklist
- [ ] Prepare a small query set (10–20 questions) relevant to EP19 corpora
  (docs + lecture folders). Save to `docs/specs/epic_20/queries.jsonl`.
- [ ] Configure retrieval: top_k, score threshold, chunk size/overlap.
- [ ] Decide prompt templates for both modes (with and without retrieved chunks).
- [ ] Choose evaluation rubric: coverage, accuracy, coherence, helpfulness
  (reuse EP05 judge prompts where possible).
- [ ] Document assumptions and limits (context length, languages).

## Deliverables
- `queries.jsonl` with fields: `id`, `question`, `expectation` (optional notes).
- `retrieval_config.yaml` (top_k, score threshold, namespace).
- `prompt_templates.md` showing final templates for both modes.

## Exit Criteria
- Stakeholder (you) signs off on query set and retrieval config.
- Prompts agreed; ready to prototype in Stage 20_02.
