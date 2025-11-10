# Documentation Overview (EN)

This repository maintains specs, guides, and APIs in a bilingual format.
Use this index to navigate current canonical documents.

## 1. Specs (source of truth)

| Path | Description |
|------|-------------|
| `docs/specs/epic_00/` | Audit artefacts (Epic 0) |
| `docs/specs/epic_04/` | Legacy archive plan, migration log, closure artifacts |
| `docs/specs/epic_06/` | Repository hygiene epic (current) |
| `docs/specs/architecture.md` | Clean Architecture target state |
| `docs/specs/operations.md` | Infrastructure & runbooks |
| `docs/specs/specs.md` | System specification summary |
| `docs/specs/progress.md` | Epic/Stage tracker |

## 2. API & CLI References (bilingual pairs)

| EN | RU | Scope |
|----|----|-------|
| `docs/reference/en/API_REVIEWER.md` | `docs/reference/ru/API_REVIEWER.ru.md` | Modular reviewer service & MCP tool |
| `docs/reference/en/API_MCP.md` | `docs/reference/ru/API_MCP.ru.md` | Active MCP tools (channels/digest/NLP) |
| `docs/reference/en/API_BOT_BACKOFFICE.md` | `docs/reference/ru/API_BOT_BACKOFFICE.ru.md` | CLI commands for backoffice |
| `docs/reference/en/API_DOCUMENTATION.md` | — | Full REST/CLI overview (EN only) |

Upcoming pairs (planned):

- `guides/en/USER_GUIDE.md` / `guides/ru/AGENT_INTEGRATION.ru.md` (mixed coverage)
- `guides/en/DEVELOPMENT.md` / _(translation planned)_
- Additional guides as part of Stage 00_02 rollout.

## 3. Guides & Operations

| Path | Notes |
|------|-------|
| `docs/guides/en/USER_GUIDE.md` | Environment setup, benchmarks |
| `docs/guides/en/DEVELOPMENT.md` | Dev container & workflow |
| `docs/guides/en/TROUBLESHOOTING.md` | Common issues (Mongo, LLM, Prometheus) |
| `docs/guides/en/shared_infra_cutover.md` | External infra dependency overview |
| `docs/MAINTAINERS_GUIDE.md` | Maintainer responsibilities, CI gates, automation playbook |
| `docs/reference/en/PERFORMANCE_BENCHMARKS.md` | Latest reviewer latency |
| `docs/guides/en/MODULAR_REVIEWER_INTEGRATION_GUIDE.md` | Embedding package in other projects |
| `docs/guides/en/observability_operations_guide.md` | Day-to-day observability tasks |
| `scripts/ci/bootstrap_shared_infra.py` | CI/local bootstrap for disposable infra (paired with cleanup script) |
| `scripts/infra/start_shared_infra.sh` | Wrapper script (run from repo root) for shared infra bootstrap |

## 4. Legacy / Archive

- `docs/archive/` — historical day specs (`day11`, `day12`, etc.)
- `docs/reference/en/API_MCP_TOOLS.md`, `docs/reference/en/API.md` — superseded by bilingual API docs (retain until migration complete).

## 5. Translation Policy

- Specs remain in English; dominant user-facing content (bot messages, CLI output) localised to Russian.
- API/CLI docs maintained as EN/RU pairs; updates should keep both versions in sync.
- When adding new guides, create both language versions or mark translation backlog in Stage 00_02.
