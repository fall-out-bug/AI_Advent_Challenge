# Documentation Overview (EN)

This repository maintains specs, guides, and APIs in a bilingual format.
Use this index to navigate current canonical documents.

## 1. Specs (source of truth)

| Path | Description |
|------|-------------|
| `docs/specs/epic_00/` | Audit artefacts (Epic 0) |
| `docs/specs/epic_04/` | Legacy archive plan, migration log, closure artifacts |
| `docs/specs/architecture.md` | Clean Architecture target state |
| `docs/specs/operations.md` | Infrastructure & runbooks |
| `docs/specs/specs.md` | System specification summary |
| `docs/specs/progress.md` | Epic/Stage tracker |

## 2. API & CLI References (bilingual pairs)

| EN | RU | Scope |
|----|----|-------|
| `docs/API_REVIEWER.md` | `docs/API_REVIEWER.ru.md` | Modular reviewer service & MCP tool |
| `docs/API_MCP.md` | `docs/API_MCP.ru.md` | Active MCP tools (channels/digest/NLP) |
| `docs/API_BOT_BACKOFFICE.md` | `docs/API_BOT_BACKOFFICE.ru.md` | CLI commands for backoffice |

Upcoming pairs (planned):

- `USER_GUIDE.md` / `USER_GUIDE.ru.md` (existing)
- `DEVELOPMENT.md` / `DEVELOPMENT.ru.md` (future)
- Additional guides as part of Stage 00_02 rollout.

## 3. Guides & Operations

| Path | Notes |
|------|-------|
| `docs/USER_GUIDE.md` | Environment setup, benchmarks |
| `docs/DEVELOPMENT.md` | Dev container & workflow |
| `docs/TROUBLESHOOTING.md` | Common issues (Mongo, LLM, Prometheus) |
| `docs/shared_infra_cutover.md` | External infra dependency overview |
| `docs/PERFORMANCE_BENCHMARKS.md` | Latest reviewer latency |
| `docs/MODULAR_REVIEWER_INTEGRATION_GUIDE.md` | Embedding package in other projects |
| `scripts/start_shared_infra.sh` | Wrapper script (run from repo root) for shared infra bootstrap |

## 4. Legacy / Archive

- `docs/archive/` — historical day specs (`day11`, `day12`, etc.)
- `docs/API_MCP_TOOLS.md`, `docs/API.md` — superseded by bilingual API docs (retain until migration complete).

## 5. Translation Policy

- Specs remain in English; dominant user-facing content (bot messages, CLI output) localised to Russian.
- API/CLI docs maintained as EN/RU pairs; updates should keep both versions in sync.
- When adding new guides, create both language versions or mark translation backlog in Stage 00_02.
