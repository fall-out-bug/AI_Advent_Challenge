# EP04 Coordination Notes · Input from Stage 02_01

## Purpose

Provide EP04 (Archive & Cleanup) with the artefact list and timelines resulting
from the Stage 02_01 MCP tool catalogue freeze. This document should be reviewed
before opening Stage 04_01 so that archival work and dependency removal can be
scheduled without blocking CLI or MCP flows.

## Items Targeted for Archival

| Component | Path(s) | Current Status | Dependencies to Check | Notes |
|-----------|---------|----------------|------------------------|-------|
| Reminder MCP tools | `src/presentation/mcp/tools/reminder_tools.py` | Archived | Mongo `tasks` collection, Telegram creds, workers | Remove once bot handlers cleaned up (Stage 02_03). |
| Reminder summary helpers | `src/presentation/mcp/tools/_summary_helpers.py` (task sections) | Archived | Shared summary imports | Move digest-specific helpers to CLI utilities. |
| Reminder tests | `tests/presentation/mcp/test_reminder_tools.py` (and variants) | Archived | Pyrogram fixtures | Mark for deletion or move to `archive/`. |
| Homework review legacy tool | `src/presentation/mcp/tools/homework_review_tool.py` | Deprecated | ModularReviewService, Mongo homework collection | Retire after EP01 ships replacement. |
| PDF digest toolchain | `src/presentation/mcp/tools/pdf_digest_tools.py` | Deprecated | WeasyPrint, Prom metrics, Mongo posts | Delete once CLI `digest:export` adopted (Stage 02_02). |
| PDF tests | `tests/presentation/mcp/test_pdf_digest_tools.py` | Deprecated | WeasyPrint fixtures | Convert to CLI integration test or remove. |
| Channel bulk MCP wrappers | `src/presentation/mcp/tools/channels/channel_management.py` (non-read ops) | Transition | Mongo `channels`, CLI Stage 02_02 | Keep read-only hooks; move bulk logic to CLI then archive remaining MCP entrypoints. |
| Posts management MCP wrappers | `src/presentation/mcp/tools/channels/posts_management.py` | Transition | Telegram workers, Mongo `posts` | Confirm CLI refresh covers all use cases before archiving. |
| CLI demo scripts (legacy) | `scripts/mcp_comprehensive_demo.py` | Archived | None | Replace references with new CLI docs. |

## Timeline Recommendations

1. **Immediately after Stage 02_02**  
   - Confirm CLI backoffice commands cover channel and digest flows.  
   - Deprecate documentation references to MCP bulk tools.

2. **During Stage 02_03**  
   - Remove reminder/task references from Telegram bot and localisation files.  
   - Verify no presentation layer imports `reminder_tools` or related helpers.  
   - Update docs to point to CLI-only flows.

3. **Stage 04_01 Kick-off**  
   - Remove archived MCP modules/tests listed above.  
   - Drop WeasyPrint and task-related dependencies from `pyproject.toml`.  
   - Migrate remaining helper functions to CLI modules where needed.  
   - Ensure `archive/` contains historical copies if stakeholders request them.

## Preconditions Before Archival

- CLI `digest:export` and channel management commands are released and documented.  
- Telegram bot no longer imports reminder/task handlers.  
- Modular reviewer replacement for homework tool is available (EP01 deliverable).  
- Observability dashboards updated to remove metrics emitted by deprecated tools.

## Cross-Team Touchpoints

- **EP02 Team**: Confirm CLI coverage and provide replacement command references.  
- **EP01 Team**: Supply final homework review MCP replacement contract.  
- **Ops/Infra**: Plan removal of WeasyPrint and related OS packages.  
- **Docs Team**: Update user-facing guides post-archive.

## Next Actions

1. Validate dependencies and confirm readiness at Stage 02_02/02_03 exits.  
2. Create archive tasks in EP04 backlog referencing this document.  
3. Schedule joint review with EP02/EP04 leads before EP04 execution starts.

