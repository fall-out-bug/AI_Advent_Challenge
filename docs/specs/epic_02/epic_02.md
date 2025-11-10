# Epic 02 · MCP & Bot Consolidation

## Status
- **State:** Completed (2025-11-09)
- **Summary:** MCP catalogue frozen, CLI backoffice shipped, Telegram bot/doc set aligned with new scope.
- **Owners:** Tech lead – Assistant (user oversight); Implementation – GPT-5 Codex agents.

## Purpose
Streamline the MCP toolset and Telegram bot flows by retiring legacy paths,
introducing deterministic CLI backoffice tooling, and aligning all interfaces
with the modular reviewer era.

## Objectives
- Freeze the supported MCP tool catalogue, documenting keep/rework/archive
  outcomes and removing deprecated assets.
- Deliver a CLI backoffice that covers owner-only operations (channel
  management, digest control, optional NLP checks) through application services.
- Prune Telegram bot scenarios to active digest/channel flows while keeping docs
  and localisation consistent.

## Dependencies
- EP01 outputs for reviewer service contracts and shared SDK components.
- Shared infrastructure availability (Mongo, LLM, Prometheus) for CLI and MCP
  verification.
- Coordination with EP04 to schedule archival of removed assets.

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 02_01 | Tool catalogue freeze | Definitive MCP tool matrix, deprecation plan, migration notes | Tool registry updated, deprecation timeline published |
| Stage 02_02 | CLI backoffice delivery | CLI command set implemented with tests and docs | CLI commands pass tests, operator guide approved |
| Stage 02_03 | Telegram & docs alignment | Bot flows trimmed, localisation updated, docs synced | Telegram app reflects new scope, docs merged, stakeholders sign off |

## Deliverables
- `docs/specs/epic_02/mcp_tool_matrix.md` – finalised tool catalogue with lifecycle notes.
- CLI backoffice (`src/presentation/cli/backoffice/…`) with tests/documentation.
- Telegram bot scope reduction (channels/digest only) and updated manuals.
- Public changelog entries (`docs/archive/release_notes/CHANGELOG_MCP.md`) capturing freeze and CLI rollout.
- Stage worklogs (`stage_02_01_worklog.md`, `stage_02_02_worklog.md`, `stage_02_03_worklog.md`) and manual checklist.

## Metrics & Evidence
| Area | Evidence |
|------|----------|
| MCP | `tools_registry` filters deprecated/archived by default; Prometheus metric tracks registered tools. |
| CLI | `poetry run pytest src/tests/presentation/cli/backoffice -q` – 16 passed; Prometheus counters for command usage. |
| Bot | `poetry run pytest tests/presentation/bot -q` – 11 passed after scope reduction. |
| Docs | EN/RU guides refreshed (MCP API, CLI backoffice, README, Telegram setup/cache). |

## Success Criteria
- MCP `tools_registry` exposes only supported tools with accurate metadata.
- CLI backoffice covers agreed commands and integrates with application services
  and shared infra.
- Telegram bot and documentation no longer reference archived reminder/task
  functionality.

## Stakeholders
- Tech Lead Agent: to be assigned (planning, reviews, coordination).
- Developer Agents: allocated per stage for MCP refactor, CLI implementation,
  bot adjustments.
- Ops/Support: consulted for CLI rollout and operator training.

## Risk & Mitigation Snapshot
- **Risk:** CLI and MCP APIs drift apart.
  **Mitigation:** Share adapter layer between CLI and MCP; stage tests hitting
  both surfaces.
- **Risk:** Localisation mismatches in Telegram flows.
  **Mitigation:** Institute localisation review checklist in Stage 02_03 and run
  RU copy tests.

## Follow-ups
- EP03 backlog: extend CLI with `channels refresh`, `digest export`, NLP QA.
- EP04: execute archival plan for deleted reminder/task assets.
- Schedule RU localisation sign-off using `stage_02_03_manual_checklist.md`.

## References
- `docs/specs/epic_00/stage_00_01.md` MCP tool inventory.
- `docs/reference/en/API_MCP.md`, `docs/reference/en/API_BOT_BACKOFFICE.md` – existing drafts to refresh.
- `docs/specs/operations.md` – shared infra commands required by CLI.
