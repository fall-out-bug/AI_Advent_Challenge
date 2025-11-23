# AI Challenge Documentation Index

Alfred is live; the doc set is intentionally small.

## Final Deliverables
- [Final Report](FINAL_REPORT.md) – narrative wrap-up + run instructions.
- [Day 1–28 Summary](challenge_days.md) – one table to rule them all.
- [Epic 28 Spec](specs/epic_28/epic_28.md) – canonical design for Alfred.
- [Consensus Artifacts](specs/epic_28/consensus/) – requirements, architecture, plan, decision logs.
- [Roles & Prompts](roles/) – `consensus_architecture.json` + per-role `prompt.json`.
- [Shared Infra Playbook](operational/shared_infra.md) – Mongo/Prometheus/Qwen bootstrap.

## Supporting Specs
- Historic epics remain under `specs/epic_*` for context.
- Templates live in `specs/templates/` if you ever need to draft new artifacts.
- `specs/progress.md` and `specs/operations.md` are kept for lineage but frozen.

## Operations Snapshot
- Single entry point: Telegram Butler bot → Alfred orchestrator.
- Observability: Prometheus/Grafana/Loki per `operational/shared_infra.md`.
- Metrics namespace: `god_agent_*` (see Epic 28 for definitions).

## Legacy Library
All former guides, bilingual APIs, and research papers now live under
`docs/reference/legacy/library/`. Nothing was deleted—search there if you
need the old playbooks (maintainer guide, MCP tutorials, bilingual API docs, etc.).

## Need More?
- Browse `FINAL_REPORT.md` for context + quick links.
- Check `docs/reference/legacy/library/` for anything not listed above.
- Run the consensus flow via the per-epic structure and prompts in `docs/roles/`.
