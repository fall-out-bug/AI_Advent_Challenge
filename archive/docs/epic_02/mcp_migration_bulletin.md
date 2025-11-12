# MCP Tool Migration Bulletin · Stage 02_01

## Overview

Stage 02_01 freezes the supported MCP tool catalogue and prepares consumers for
upcoming removals. Deprecated and archived tools remain callable only when
`MCP_INCLUDE_DEPRECATED_TOOLS=1` is set on the MCP server and client. Operators
must migrate to the replacements outlined below before Stage 02_03 completes.

## Summary Matrix

| Tool / Surface | Current Status | Replacement / Action | Target Stage |
|----------------|----------------|----------------------|--------------|
| `review_homework_archive` | Deprecated | New modular reviewer MCP tool (EP01 follow-up) | Post EP01 |
| PDF digest toolset (`get_posts_from_db`, `summarize_posts`, `format_digest_markdown`, `combine_markdown_sections`, `convert_markdown_to_pdf`) | Deprecated | CLI `digest:export` command set | Stage 02_02 |
| Reminder tools (`add_task`, `list_tasks`, `update_task`, `delete_task`, `get_summary`) | Archived | Retire integrations; remove from clients | Stage 02_03 / EP04 |
| Channel management (`add_channel`, `list_channels`, `delete_channel`) | Transition | Use CLI `channels:*` commands | Stage 02_02 |
| Posts management (`get_posts`, `collect_posts`, `save_posts_to_db`) | Transition | Use CLI ingestion pipeline | Stage 02_02 |
| NLP digest intent (`parse_digest_intent`) | Supported | Keep consuming; ensure RU localisation tests | Ongoing |
| NLP task intent (`parse_task_intent`) | Archived | Remove references; archive tests | Stage 02_03 / EP04 |

## CLI Command Mapping (Stage 02_02 Preview)

| Legacy MCP Flow | CLI Replacement | Notes |
|-----------------|-----------------|-------|
| `add_channel` | `cli channels add --username <name> [--tags ...]` | Performs validation via channel metadata service. |
| `list_channels` | `cli channels list [--include-tags]` | Same Mongo projection; adds JSON output option. |
| `delete_channel` | `cli channels remove --channel-id <id>` | Supports lookup by username before delete. |
| `get_posts` / `collect_posts` | `cli channels refresh --username <name> [--hours 72]` | Enqueues worker job or runs synchronously. |
| `save_posts_to_db` | `cli channels refresh` pipeline | Persistence handled within CLI workflow. |
| PDF digest toolchain | `cli digest run --channel <name> --hours 24` and `cli digest export ...` | Markdown + PDF emitted via shared templates. |
| Reminder lifecycle tools | No replacement | Feature removed; surface intentionally unavailable. |

## Timeline & Communications

1. **Stage 02_01 (now)**  
   - Publish tool matrix and migration bulletin.  
   - MCP server hides deprecated/archived tools unless opt-in flag set.  
   - Deprecation warnings emitted on use.

2. **Stage 02_02 (2025-11-17 target)**  
   - Deliver CLI backoffice covering channel management and digest export.  
   - Update docs to promote CLI usage as default.  
   - Begin notifying downstream consumers (Telegram bot, scripts).

3. **Stage 02_03 (2025-11-24 target)**  
   - Remove reminder hooks from Telegram flows and docs.  
   - Ensure channel bulk operations reference CLI only.  
   - Finalise list of files for EP04 archival sweep.

4. **EP04 (2025-11-24 onwards)**  
   - Move archived modules/tests into `archive/`.  
   - Remove PDF WeasyPrint dependencies from active dependencies.  
   - Confirm no remaining imports reference deprecated tools.

## Required Actions for Consumers

- **MCP Clients / Agents**  
  - Update discovery logic to respect `status` metadata returned by the registry.  
  - Remove hard-coded references to reminder and PDF digest tools.  
  - Prepare to handle `transition` status by routing via CLI once released.

- **Telegram Bot**  
  - Drop reminder commands and ensure digest flows call supported MCP tools only.  
  - Add UX hints directing operators to CLI for bulk actions.

- **Operators / Support**  
  - Set `MCP_INCLUDE_DEPRECATED_TOOLS=0` in production once CLI rollout verified.  
  - Update runbooks with CLI command recipes.

- **Documentation Maintainers**  
  - Sync `API_MCP.md` (EN/RU) with new statuses and CLI references.  
  - Link this bulletin from epic summary and operations guide.

## Risks & Mitigations

- **Delayed CLI rollout**  
  - Keep deprecated tools behind opt-in flag; communicate extension timeline if needed.

- **Client drift**  
  - Provide SDK helper to filter by `status`; add tests ensuring archived tools raise errors.

- **Documentation gaps**  
  - Track EN/RU parity via docs checklist; include CLI examples in both languages.

## Contacts

- Tech Lead (Stage 02): _Current user_
- CLI Backoffice Owner: Assign in Stage 02_02 kickoff
- EP04 Archival Lead: To be nominated; receive coordination doc from Stage 02_01


