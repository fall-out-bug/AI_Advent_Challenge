# Day 20 · RAG vs Non‑RAG Answering Agent

## Scope
- Implement “question → retrieve relevant chunks → augment prompt → query LLM”.
- Compare model answers with and without RAG context.
- Produce a concise report: when RAG helps vs when it doesn’t.

## Where to Look
- Epic: `docs/specs/epic_20/epic_20.md`
- Stages: `docs/specs/epic_20/` (`stage_20_01.md`..`stage_20_04.md`)
- Demo plan: `docs/specs/epic_20/stage_20_03.md` and `docs/specs/epic_20/README` (if present)

## High-Level Design
1. Accept a user question.
2. Retrieve top‑K relevant chunks from EP19 index.
3. Build two prompts: (A) zero‑shot (no context), (B) RAG‑augmented (with top‑K chunks).
4. Call LLM (via `LLM_URL`) for both prompts; capture outputs and latency.
5. Present side‑by‑side comparison and simple quality signals (e.g., length, self‑consistency).

## Outputs
- A CLI/agent with two modes (RAG on/off) and a comparison report.
- Example transcripts demonstrating cases where RAG helps vs where it doesn’t.
- Optional: summary table with “RAG vs Non‑RAG” performance per query.
