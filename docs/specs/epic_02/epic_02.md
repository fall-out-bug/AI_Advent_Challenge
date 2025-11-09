# Epic 02 · MCP & Bot Consolidation

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

## References
- `docs/specs/epic_00/stage_00_01.md` MCP tool inventory.
- `docs/API_MCP.md`, `docs/API_BOT_BACKOFFICE.md` – existing drafts to refresh.
- `docs/specs/operations.md` – shared infra commands required by CLI.

