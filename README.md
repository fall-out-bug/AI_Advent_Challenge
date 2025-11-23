# AI Advent Challenge · Alfred Era

> Twenty-eight consecutive builds culminated in Alfred, a Telegram-first God Agent
> that plans, executes, and reports like a personal employee.

## Project Snapshot
- ✅ All 28 daily challenges complete ([`docs/challenge_days.md`](docs/challenge_days.md))
- ✅ Alfred orchestrator shipped (Epic 28)
- ✅ Butler bot (text + voice) routes every user request through Alfred
- ✅ Local-only infrastructure (MongoDB, Prometheus, Grafana, Qwen)

## Run Alfred in <60 Seconds
```bash
make install              # deps
make day-12-up            # Mongo, Prometheus, Grafana, Qwen
make run-bot              # Telegram Butler → Alfred
```
Need full context? See [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md).

## Where to Read
| Document | Why it matters |
|----------|----------------|
| [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md) | Executive summary + operating instructions |
| [`docs/specs/epic_28/epic_28.md`](docs/specs/epic_28/epic_28.md) | Alfred architecture, intent router, planner, skill graph |
| [`docs/specs/epic_28/consensus/`](docs/specs/epic_28/consensus/) | Live consensus artifacts, inboxes, decision log |
| [`docs/roles/consensus_architecture.json`](docs/roles/consensus_architecture.json) | Canonical role contracts + prompts |
| [`docs/operational/shared_infra.md`](docs/operational/shared_infra.md) | Shared infra bootstrap + observability |

Legacy guides, APIs, and research notes now live under
[`docs/reference/legacy/library/`](docs/reference/legacy/library/). Nothing was
removed—just archived so the active docs stay small.

## Repo Layout
```
AI_Challenge/
├── src/                # Clean Architecture code (domain/application/infrastructure/presentation)
├── docs/
│   ├── FINAL_REPORT.md
│   ├── challenge_days.md
│   ├── specs/epic_28/
│   ├── roles/
│   └── reference/legacy/library/
├── scripts/            # Infra + maintenance helpers
├── shared/             # Shared SDKs / clients
└── tasks/, archive/…   # Historical challenge assets
```

## Alfred Highlights
- Butler persona (Day 25) with long-term profile + memory fabric powering replies
- Voice-to-text (Day 24) feeds the same intent router
- Multi-pass reviewer, MCP tool graph, and autonomous test agent (Days 14–26)
- Observability-first (Day 23): Prometheus `god_agent_*` metrics, Grafana, Loki
- Consensus evolved: JSON inbox, compact prompts, veto matrix, English-only outputs

Full day-by-day notes (including early experiments) live in
[`docs/challenge_days.md`](docs/challenge_days.md).

## Need Anything Else?
- Orientation for AI assistants: [`AI_CONTEXT.md`](AI_CONTEXT.md), [`docs/INDEX.md`](docs/INDEX.md)
- Contribution / license: [`CONTRIBUTING.md`](CONTRIBUTING.md), [`LICENSE`](LICENSE)

> “Alfred, we’re home.” — final transmission
