<<<<<<< HEAD
# Context Limits & Token Budgets

## Purpose
Define token, memory, and context guardrails per role to keep multi-agent
sessions efficient. Aligns with responsibilities outlined in
`docs/specs/process/agent_workflow.md`.

## Role Budgets

| Role       | Prompt Budget (tokens) | History Window | Attachment Limit | Notes |
|------------|------------------------|----------------|------------------|-------|
| Analyst    | 6k                     | 3 prior epics  | 5 docs           | Focus on requirement diffs and acceptance traceability. |
| Architect  | 5k                     | 2 prior epics  | 4 docs           | Prioritize architecture deltas, MADRs, dependency audits. |
| Tech Lead  | 5k                     | Current epic   | 6 docs           | Emphasize plan tables, CI gates, risk register extracts. |
| Developer  | 4k                     | Active stage   | 4 docs           | Keep code/test snippets lean; link to repos for detail. |
| Reviewer   | 4k                     | Current review | 6 artefacts      | Include evidence (tests/logs) with concise summaries. |

## Memory Windows
- Maintain rolling summaries after each major update (requirements, architecture,
  plan, implementation, review).
- Store canonical summaries under `docs/epics/<epic>/worklogs/`.
- Archive aged context (older than 3 epics) to reduce prompt size.

## Usage Guidelines
- Compress verbose logs before attaching; prefer key metrics or excerpts.
- Link to repo paths instead of pasting full code blocks when possible.
- Use `rag_queries.md` playbooks to pull fresh context instead of bloating prompts.
- Record token usage in worklogs for future tuning.

## Update Log
- 2025-11-13: Initial baseline created for living documentation system.
- Pending: integrate automated token tracking via MCP telemetry.
=======
# Context & Token Management

## Per Role Budgets

| Role | Model | Context Window | Allocated Budget | Used By |
|------|-------|-----------------|------------------|---------|
| Analyst | Qwen (Day 13) | 12K | 10K for gathering, 2K for RAG | Days 3, 15, 22 |
| Architect | Qwen | 12K | 8K for vision, 3K for RAG, 1K for margin | Days 4-5, 12, 22 |
| Tech Lead | Qwen | 12K | 6K for plan, 4K for cross-check, 2K for RAG | Days 8, 15-17, 22 |
| Developer | Qwen | 12K | 10K for code, 1K for context, 1K margin | Days 2, 8, 13 |
| Reviewer | Qwen | 12K | 8K for analysis, 3K for citations, 1K margin | Days 20-22 |

## Compression Strategies

**When context > 80% used:**
1. Apply Day 15 map-reduce compression
2. Summarize into bullet points (max 10 lines)
3. Replace original with summary in context

**Example:**
Original (8K tokens):
[Long conversation with 20+ exchanges]

Compressed (500 tokens):

Analyst gathered 15 requirements

Key constraint: PostgreSQL mandatory

Unclear: authentication scope (needs clarification from user)

Clarity score: 0.65 (needs improvement)

## RAG Query Costs

- Small query: ~100 tokens
- Medium query (3-5 docs): ~500 tokens
- Large query (full epic history): ~1K tokens

**Limit RAG queries to 2-3 per role per epic.**
>>>>>>> origin/master
