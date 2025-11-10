# EP04 Archive · Tests

Add legacy test suites tied to archived functionality. Document why they were removed from CI and reference the replacement coverage or rationale for retirement.

## Archived on 2025-11-09 (Wave 1)

- `src/tests/presentation/mcp/test_reminder_tools.py` — reminder MCP tool retired
- `src/tests/e2e/test_bot_flows.py` — reminder-driven bot flows removed
- `src/tests/e2e/test_scheduled_notifications.py` — reminder schedulers removed
- `tests/presentation/mcp/test_reminder_tools_summary_helpers.py` — helper coverage superseded by archive
- `tests/unit/domain/agents/handlers/test_reminders_handler.py` — reminder handlers deprecated

Legacy reminder functionality is no longer exercised; MCP and bot flows rely on digest/CLI replacements.
- `src/tests/presentation/mcp/test_pdf_digest_tools.py` — PDF MCP tests archived; CLI export covers functionality
- `tests/integration/test_pdf_digest_flow.py` — legacy PDF flow archived; CLI export replaces workflow
- `tests/contract/test_mcp_tools_schema.py` — backend MCP schema checks referencing PDF tools archived
- `tests/integration/test_mcp_comprehensive_demo.py` — legacy CLI orchestration demo superseded by backoffice CLI tests
