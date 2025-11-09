# Stage 02_01 · MCP Tool Catalogue Freeze

**Status:** Completed — deliverables approved 2025-11-09 (see worklog for details).

## Goal
Establish the definitive MCP toolset by confirming keep/rework/archive decisions,
documenting replacements, and updating registry metadata.

## Checklist
- [x] Validate Stage 00 tool inventory against current repository state.
- [x] Produce final tool matrix (status, owner, replacement notes, dependencies).
- [x] Update `tools_registry` wiring to remove or flag deprecated tools.
- [x] Draft migration notes for consumers of archived tools (homework review,
  PDF digest, reminders).
- [x] Communicate freeze outcome to EP04 for archival scheduling.
- [x] Capture kickoff sync notes (team roster, timelines, outstanding questions)
  and file them under `docs/specs/epic_02/stage_02_01_worklog.md`.

## Deliverables
- Published tool matrix (embedded in Stage doc and linked from epic summary).
- Updated MCP registry code/config with deprecated tools removed or marked
  experimental.
- Migration bulletin summarising changes and timelines.

## Metrics & Evidence
- Registry diff showing only supported tools exposed by default.
- Test results covering retained tools (digest, channels, NLP).
- Confirmation from EP02 tech lead that CLI command mapping inputs match tool
  contracts.

## Dependencies
- Access to MCP registry codebase and tests.
- Coordination with EP01 for reviewer-related tool behaviour.
- Agreement from stakeholders on deprecation timeline.

## Exit Criteria
- Tool matrix approved by tech lead and shared with coordination board.
- Deprecated tooling either removed or wrapped with deprecation warnings pending
  archival.
- CLI design (Stage 02_02) receives stable tool contract references.

## Open Questions
- **Preserve archived tools behind feature flag?** ✅ Да — `MCP_INCLUDE_DEPRECATED_TOOLS` включает deprecated/archived инструменты до завершения CLI миграции.
- **Публиковать ли публичный CHANGELOG?** ✅ Да — см. `docs/CHANGELOG_MCP.md` (добавлен в рамках closing steps).

