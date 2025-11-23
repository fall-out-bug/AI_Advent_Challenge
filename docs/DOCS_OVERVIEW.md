# Documentation Overview

The project is complete. Alfred (Epic 28) is the only supported surface, and all
supporting docs are distilled below. Everything else has been archived under
`docs/reference/legacy/library/` for historical research.

## Canonical Docs (Active)

| Path | Purpose |
|------|---------|
| [`docs/FINAL_REPORT.md`](FINAL_REPORT.md) | Narrative wrap-up + operating model for Alfred. |
| [`docs/challenge_days.md`](challenge_days.md) | Concise summary of Days 1‑28. |
| [`docs/specs/epic_28/epic_28.md`](specs/epic_28/epic_28.md) | God Agent Alfred spec (intent router, planner, skill graph). |
| [`docs/specs/epic_28/consensus/`](specs/epic_28/consensus/) | Latest consensus artifacts, messages, decision logs. |
| [`docs/roles/consensus_architecture.json`](roles/consensus_architecture.json) | Unified consensus contract + prompts. |
| [`docs/roles/*/prompt.json`](roles/) | Machine-readable prompts for each agent. |
| [`docs/operational/shared_infra.md`](operational/shared_infra.md) | How to run shared infra + local stack. |
| [`docs/specs/templates/`](specs/templates/) | Minimal templates if new specs are ever required. |

## How to Operate Alfred

1. **Shared infra** – follow `operational/shared_infra.md` to start Mongo, Prometheus, Qwen.
2. **Consensus** – use the per-epic structure in `docs/specs/epic_28/consensus/` and the prompts in `docs/roles/`.
3. **Entry point** – Telegram Butler bot is the single user surface; voice notes feed the same orchestrator.
4. **Observability** – metrics prefixed with `god_agent_*` (see Epic 28 spec) land in Prometheus/Grafana.

## Legacy Material

All previous guides, bilingual API docs, day-specific playbooks, and research
notes now live under `docs/reference/legacy/library/`. Nothing was deleted—just
quietly shelved so the active docs stay small.
