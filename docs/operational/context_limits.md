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

