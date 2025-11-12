# Epic 02 · Worklog & Close-out

## Snapshot
- **Period:** 2025-11-08 → 2025-11-09
- **Scope:** MCP tool freeze, CLI backoffice delivery, Telegram/docs alignment
- **Status:** Completed (all stages closed)
- **Tech lead:** Assistant (user oversight)

## Stage Outcomes
| Stage | Highlights | Evidence |
|-------|------------|----------|
| 02_01 | Finalised MCP tool matrix, lifecycle metadata, feature flag for deprecated tools, documentation refresh. | `mcp_tool_matrix.md`, `tools_registry.py`, `docs/archive/release_notes/CHANGELOG_MCP.md`. |
| 02_02 | Delivered deterministic CLI (`channels list/add/remove`, `digest run/last`), dual-format output, Prometheus metrics, comprehensive tests. | `src/presentation/cli/backoffice/…`, CLI unit/integration tests, updated backoffice docs. |
| 02_03 | Removed reminder/task bot flows, aligned menus/factory, pruned tests, refreshed README & Telegram guides, drafted manual checklist. | `src/presentation/bot/…`, Stage manual checklist, updated README EN/RU. |

## Key Metrics
- **Testing:**
  - MCP impacted suites kept healthy (`pytest` selective runs; deprecated suites marked xfail/skip).
  - CLI backoffice: `poetry run pytest src/tests/presentation/cli/backoffice -q` → 16 passed.
  - Bot scope: `poetry run pytest tests/presentation/bot -q` → 11 passed.
- **Documentation:** 10+ artefacts updated/created (tool matrix, migration bulletin, CLI docs EN/RU, MCP changelog, README EN/RU, Telegram guides, Stage worklogs, manual checklist).
- **Monitoring:** MCP registered-tools gauge, CLI command counters/timers/errors.

## Decision Log Summary
- Deprecated/archived MCP tools hidden by default; temporary access via `MCP_INCLUDE_DEPRECATED_TOOLS`.
- CLI operates without interactive prompts; JSON export via `--json`, metrics enabled by default.
- Telegram bot retains only channel/digest functionality; reminder/task code removed without feature flags.
- Manual acceptance testing to use `stage_02_03_manual_checklist.md`; localisation review pending.

## Risks & Mitigations
- **Drift between CLI and MCP:** Unified adapters and shared tool client tests keep parity; backlog includes joint integration checks.
- **Localisation regressions:** RU copy review scheduled; manual checklist includes RU scenarios.
- **Legacy artefacts lingering in deployments:** EP04 coordination document tracks files for archival.

## Follow-ups & Backlog
- Extend CLI in EP03/EP04 (`channels refresh`, `digest export`, NLP QA).
- Execute EP04 archival of deleted reminder/task assets.
- Automate localisation diff testing once RU review is completed.

## References
- Stage worklogs: `stage_02_01_worklog.md`, `stage_02_02_worklog.md`, `stage_02_03_worklog.md`.
- Specifications: `stage_02_01.md`, `stage_02_02.md`, `stage_02_03.md`.
- Supporting docs: `mcp_tool_matrix.md`, `mcp_migration_bulletin.md`, `API_MCP*.md`, `API_BOT_BACKOFFICE*.md`.
