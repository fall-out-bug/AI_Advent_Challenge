# EP04 · November 2025 Archive Manifest

## Purpose

This manifest tracks every asset moved into `archive/ep04_2025-11` during Epic 04 Stage 04_02. Use it as the single source of truth for retrieval, replacements, and approvals.

## Structure

```
archive/ep04_2025-11/
├── code/
│   └── README.md
├── docs/
│   └── README.md
├── scripts/
│   └── README.md
├── tests/
│   └── README.md
└── ARCHIVE_MANIFEST.md
```

## Entry Format

Each archived asset must be appended to the table below with:

- Original repository path
- New archive location (relative to `archive/ep04_2025-11/`)
- Successor or replacement reference
- Archive date (YYYY-MM-DD)
- Archived by (owner)
- Sign-off stakeholders

| Original Path | Archive Location | Replacement / Notes | Date | Archived By | Sign-offs |
|---------------|------------------|---------------------|------|-------------|-----------|
| docs/AGENT_INTEGRATION.md | docs/AGENT_INTEGRATION.md | See `docs/API_REVIEWER.md` for current integration guidance | 2025-11-09 | Assistant | Pending |
| docs/AGENT_INTEGRATION.ru.md | docs/AGENT_INTEGRATION.ru.md | Use updated RU modular reviewer docs | 2025-11-09 | Assistant | Pending |
| docs/MCP_HOMEWORK_REVIEW.md | docs/MCP_HOMEWORK_REVIEW.md | Refer to `docs/API_MCP.md` | 2025-11-09 | Assistant | Pending |
| docs/MCP_GUIDE.md | docs/MCP_GUIDE.md | Superseded by MCP tool matrix + CLI docs | 2025-11-09 | Assistant | Pending |
| docs/MCP_DEMO_GUIDE.md | docs/MCP_DEMO_GUIDE.md | Use CLI backoffice demo instructions | 2025-11-09 | Assistant | Pending |
| docs/MCP_TOOL_USAGE.md | docs/MCP_TOOL_USAGE.md | Covered by MCP tool matrix + CLI references | 2025-11-09 | Assistant | Pending |
| docs/MODEL_SETUP.md | docs/MODEL_SETUP.md | See operations guide shared infra section | 2025-11-09 | Assistant | Pending |
| docs/architecture/mcp_agent_prompt_tuning_report.md | docs/architecture/mcp_agent_prompt_tuning_report.md | Superseded by modular reviewer prompt documentation | 2025-11-09 | Assistant | Pending |
| scripts/start_models.sh | scripts/start_models.sh | Use `make day-12-up` | 2025-11-09 | Assistant | Pending |
| scripts/wait_for_model.sh | scripts/wait_for_model.sh | Shared infra handles readiness | 2025-11-09 | Assistant | Pending |
| scripts/check_model_status.sh | scripts/check_model_status.sh | Run `scripts/test_review_system.py --metrics` | 2025-11-09 | Assistant | Pending |
| scripts/test_day10.sh | scripts/test_day10.sh | CI pipelines updated; see docs/specs/operations.md | 2025-11-09 | Assistant | Pending |
| scripts/day12_run.py | scripts/day12_run.py | Use `make day-12-up` + CLI backoffice | 2025-11-09 | Assistant | Pending |
| scripts/mcp_comprehensive_demo.py | scripts/mcp_comprehensive_demo.py | See updated MCP demos | 2025-11-09 | Assistant | Pending |
| scripts/healthcheck_mcp.py | scripts/healthcheck_mcp.py | Consolidated into review system test script | 2025-11-09 | Assistant | Pending |
| scripts/telegram_channel_reader.session | (deleted) | Removed sensitive session; use new auth flow | 2025-11-09 | Assistant | Pending |
| src/presentation/mcp/tools/reminder_tools.py | code/src/presentation/mcp/tools/reminder_tools.py | Reminder MCP functionality retired (use CLI/backoffice flows) | 2025-11-09 | Assistant | Pending |
| src/tests/presentation/mcp/test_reminder_tools.py | tests/src/tests/presentation/mcp/test_reminder_tools.py | Legacy reminder MCP tests retired | 2025-11-09 | Assistant | Pending |
| src/tests/e2e/test_bot_flows.py | tests/src/tests/e2e/test_bot_flows.py | Reminder bot flows removed | 2025-11-09 | Assistant | Pending |
| src/tests/e2e/test_scheduled_notifications.py | tests/src/tests/e2e/test_scheduled_notifications.py | Reminder scheduling removed | 2025-11-09 | Assistant | Pending |
| tests/presentation/mcp/test_reminder_tools_summary_helpers.py | tests/tests/presentation/mcp/test_reminder_tools_summary_helpers.py | Legacy reminder summary helpers retired | 2025-11-09 | Assistant | Pending |
| tests/unit/domain/agents/handlers/test_reminders_handler.py | tests/tests/unit/domain/agents/handlers/test_reminders_handler.py | Reminder handlers removed from active flows | 2025-11-09 | Assistant | Pending |

| src/presentation/mcp/tools/pdf_digest_tools.py | code/src/presentation/mcp/tools/pdf_digest_tools.py | CLI `digest:export` supersedes MCP PDF functionality | 2025-11-09 | Assistant | Pending |
| src/tests/presentation/mcp/test_pdf_digest_tools.py | tests/src/tests/presentation/mcp/test_pdf_digest_tools.py | PDF MCP tests archived; replaced by CLI coverage | 2025-11-09 | Assistant | Pending |
| tests/integration/test_pdf_digest_flow.py | tests/tests/integration/test_pdf_digest_flow.py | Legacy PDF flow archived; CLI export replaces workflow | 2025-11-09 | Assistant | Pending |
| tests/integration/test_mcp_comprehensive_demo.py | tests/tests/integration/test_mcp_comprehensive_demo.py | Backoffice CLI tests cover MCP scenarios | 2025-11-09 | Assistant | Pending |
| tests/contract/test_mcp_tools_schema.py | tests/tests/contract/test_mcp_tools_schema.py | Legacy MCP schema references archived | 2025-11-09 | Assistant | Pending |
| src/presentation/mcp/adapters/orchestration_adapter.py | code/src/presentation/mcp/adapters/orchestration_adapter.py | Modular reviewer workflow in MCPApplicationAdapter handles orchestration | 2025-11-09 | Assistant | Pending |
| src/workers/message_sender.py | code/src/workers/message_sender.py | Summary worker owns digests; notifier inlined with retries | 2025-11-09 | Assistant | Pending |
| src/domain/agents/handlers/reminders_handler.py | code/src/domain/agents/handlers/reminders_handler.py | Reminders mode retired; chat fallback handles legacy requests | 2025-11-09 | Assistant | Pending |
| src/application/usecases/ | code/src/application/usecases/ | Butler legacy task/data use cases migrated to new `use_cases/` namespace | 2025-11-09 | Assistant | Pending |
| src/application/orchestrators/mistral_orchestrator.py | code/src/application/orchestrators/mistral_orchestrator.py | Backoffice CLI replaces bespoke Mistral orchestration | 2025-11-09 | Assistant | Pending |
| src/application/use_cases/mistral_chat_use_case.py | code/src/application/use_cases/mistral_chat_use_case.py | Chat workflow retired; use modular reviewer/backoffice flows | 2025-11-09 | Assistant | Pending |
| src/presentation/mcp/cli/interactive_mistral_chat.py | code/src/presentation/mcp/cli/interactive_mistral_chat.py | Replaced by deterministic backoffice CLI commands | 2025-11-09 | Assistant | Pending |
| src/presentation/mcp/cli/streaming_chat.py | code/src/presentation/mcp/cli/streaming_chat.py | Same as above; streaming mode deprecated | 2025-11-09 | Assistant | Pending |
| src/presentation/mcp/orchestrators/mcp_mistral_wrapper.py | code/src/presentation/mcp/orchestrators/mcp_mistral_wrapper.py | Modular reviewer + backoffice flows supersede wrapper | 2025-11-09 | Assistant | Pending |
| src/presentation/cli/main_cli.py | code/src/presentation/cli/main_cli.py | Backoffice CLI (`src/presentation/cli/backoffice/main.py`) | 2025-11-09 | Assistant | Pending |
| src/presentation/cli/commands/config_cmd.py | code/src/presentation/cli/commands/config_cmd.py | Command set folded into backoffice telemetry tooling | 2025-11-09 | Assistant | Pending |
| src/presentation/cli/commands/health_cmd.py | code/src/presentation/cli/commands/health_cmd.py | See `docs/DEVELOPMENT.md` for new health checks | 2025-11-09 | Assistant | Pending |
| src/presentation/cli/commands/metrics_cmd.py | code/src/presentation/cli/commands/metrics_cmd.py | Metrics exported via backoffice CLI + Prometheus dashboards | 2025-11-09 | Assistant | Pending |
| src/presentation/cli/commands/status_cmd.py | code/src/presentation/cli/commands/status_cmd.py | Backoffice CLI supersedes ad-hoc status command | 2025-11-09 | Assistant | Pending |
| tests/integration/test_day10_e2e.py | tests/tests/integration/test_day10_e2e.py | Legacy Mistral E2E flow archived | 2025-11-09 | Assistant | Pending |
| tests/integration/test_mistral_orchestrator.py | tests/tests/integration/test_mistral_orchestrator.py | Archived with orchestrator removal | 2025-11-09 | Assistant | Pending |
| tests/unit/application/test_mistral_orchestrator.py | tests/tests/unit/application/test_mistral_orchestrator.py | Archived with orchestrator removal | 2025-11-09 | Assistant | Pending |
| src/tests/presentation/test_cli.py | tests/src/tests/presentation/test_cli.py | Legacy CLI harness replaced by backoffice CLI | 2025-11-09 | Assistant | Pending |
| src/tests/unit/cli/test_status_cmd.py | tests/src/tests/unit/cli/test_status_cmd.py | Archived with removal of `status_cmd` module | 2025-11-09 | Assistant | Pending |
| src/tests/unit/cli/test_config_cmd.py | tests/src/tests/unit/cli/test_config_cmd.py | Archived with removal of `config_cmd` module | 2025-11-09 | Assistant | Pending |
| src/tests/unit/cli/test_health_cmd.py | tests/src/tests/unit/cli/test_health_cmd.py | Archived with removal of `health_cmd` module | 2025-11-09 | Assistant | Pending |
| src/tests/unit/cli/test_metrics_cmd.py | tests/src/tests/unit/cli/test_metrics_cmd.py | Archived with removal of `metrics_cmd` module | 2025-11-09 | Assistant | Pending |
## Process Checklist

1. Confirm asset appears in `docs/specs/epic_04/archive_scope.md`.
2. Ensure dependencies resolved or documented in `dependency_map.md`.
3. Move files to appropriate subfolder (`code/`, `docs/`, `scripts/`, `tests/`).
4. Update subfolder `README.md` with context.
5. Append manifest entry and capture approvals in `docs/specs/progress.md`.

## Retrieval Guidance

- Archived assets remain readable but should not be imported or executed.
- For rollbacks, copy files back to active locations via PR with stakeholder approval.
- Keep archive immutable after Stage 04_02 unless incident response requires adjustments.
