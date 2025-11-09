# MCP Tool Matrix · Stage 02_01

## Summary

This matrix captures the authoritative MCP tool catalogue following the Stage 02_01
freeze. It consolidates Stage 00_01 inventory data and Stage 00_02 decisions to
explicitly mark which tools remain supported, which enter refactor, and which are
deprecated or archived. The matrix also highlights replacement paths, affected
dependencies, and required follow-up work for later stages.

## Tool Status Matrix

| Tool | Module / Entry Point | Status | Owner | Dependencies | Notes |
|------|----------------------|--------|-------|--------------|-------|
| NLP intent utilities | `src/presentation/mcp/tools/nlp_tools.py` | Keep | EP02 team | Mongo (intents), LLM API | Tests stay mandatory; ensure RU localisation coverage. |
| Digest generation | `src/presentation/mcp/tools/digest_tools.py` | Keep / Rework | EP02 team | Mongo (posts/digests), LLM API, Prometheus | Retain MCP surface; align summaries with Stage 02_02 CLI outputs. |
| Channel metadata lookup | `src/presentation/mcp/tools/channels/channel_metadata.py` | Keep | EP02 team | Mongo (channels), Telegram API (read-only) | Serves MCP & upcoming CLI; ensure caching aligns with ops guide. |
| Channel resolution helpers | `src/presentation/mcp/tools/channels/channel_resolution.py` | Keep / Rework | EP02 team | Mongo, Telegram API | Clean up reminder-specific branches; document fallback logic. |
| Channel digest helpers | `src/presentation/mcp/tools/channels/channel_digest.py` | Keep / Rework | EP02 team | Mongo, LLM API | Shared templates with CLI digest runner; enforce structured logging. |
| Channel bulk management | `src/presentation/mcp/tools/channels/channel_management.py` | Move to Backoffice | EP02 + CLI owner | Mongo, Telegram API | Superseded by Stage 02_02 CLI commands; keep MCP hooks minimal. |
| Channel post operations | `src/presentation/mcp/tools/channels/posts_management.py` | Move to Backoffice | EP02 + CLI owner | Mongo, Workers | Replace with CLI orchestration; mark MCP usage experimental only. |
| Homework review | `src/presentation/mcp/tools/homework_review_tool.py` | Deprecate (sunset) | EP01 reviewer lead | Modular Review Service, LLM API | Replacement arrives after reviewer refactor; MCP tool remains with warnings. |
| PDF digest | `src/presentation/mcp/tools/pdf_digest_tools.py` | Deprecate (sunset) | EP02 team | Mongo, WeasyPrint stack | Functionality shifts to CLI export in Stage 02_02; remove from default registry. |
| Reminder & tasks | `src/presentation/mcp/tools/reminder_tools.py` | Archive | EP04 archival lead | Mongo, Scheduler workers, Telegram API | No replacement; Telegram flows already removed. |
| Summary helpers | `src/presentation/mcp/tools/_summary_helpers.py` | Move to Backoffice | EP02 + CLI owner | N/A | Consolidate shared formatting utilities under CLI package. |

## Replacement & Migration Notes

- **Homework review tool**: Consumers must prepare for the modular reviewer powered
  replacement shipping after EP01 refactors land. Provide temporary access only for
  parity testing; enforce deprecation warnings.
- **PDF digest tool**: Operators should switch to Stage 02_02 CLI command
  `digest:export` once available. The MCP tool remains callable behind an explicit
  feature flag until Stage 02_03 completes.
- **Reminder tools**: Archived outright. Telegram reminder flows are shut down,
  and no MCP replacement is planned. Consumers must delete integrations.
- **Channel bulk operations**: Bulk add/remove/refresh moves into the CLI
  backoffice. MCP hooks remain solely for lightweight use cases (read-only or
  single-channel operations) until CLI adoption finishes.
- **Summary helpers**: Shared formatting utilities migrate into the CLI module to
  avoid cross-layer leakage from presentation tooling.

## Timeline & Follow-Up

| Milestone | Target | Description | Owner |
|-----------|--------|-------------|-------|
| Stage 02_01 completion | 2025-11-10 | Publish matrix, update registry default exports, warn on deprecated tools. | Tech lead |
| Stage 02_02 CLI rollout | 2025-11-17 | Deliver CLI commands replacing channel bulk ops and PDF digest export. | CLI owner |
| EP04 archival sweep | 2025-11-24 | Move archived MCP modules/tests into `archive/` and prune docs. | EP04 lead |
| Reviewer replacement | TBD (post EP01) | Ship modular reviewer-based homework tool; retire deprecated MCP entrypoint. | Reviewer lead |

## Dependencies

- Shared infrastructure (Mongo, Prometheus, LLM API) must remain available to keep
  supported tools functional.
- Feature flags controlling deprecated tool exposure must be documented in
  `docs/API_MCP.md` and `docs/operations/`.
- EP02 and EP04 coordination is required to avoid dangling references when
  archival work begins.

## Evidence Checklist

- [ ] MCP server registers only supported tools by default.
- [ ] Deprecated tools emit structured warnings when invoked.
- [ ] API documentation reflects status and timelines in both EN/RU variants.
- [ ] Migration bulletin published and linked from epic summary.
- [ ] Tests cover retained tools (digest, channels, NLP) and skip archived ones.


