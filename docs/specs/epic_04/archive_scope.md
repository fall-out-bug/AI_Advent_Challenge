# Stage 04_01 · Archive Scope

## Purpose

This document lists every asset slated for archival or deletion during Epic 04
Stage 04_01. Each entry records its replacement path, dependency posture, and
required sign-offs so that Stage 04_02 migrations can proceed without risk.

## Summary

- Archive scope covers legacy reviewer agents, deprecated MCP tooling, obsolete
  documentation, local model scripts, unused prompts, and tests tied to retired
  features.
- Successor implementations live in the modular reviewer package, refreshed MCP
  digest/channel flows, or the upcoming CLI backoffice.
- Dependency checks are tracked in `dependency_map.md`; entries flagged as
  `Hard` require remediation before removal.
- All stakeholders listed in the communication plan must approve this document
  before execution begins.

## Code Modules

| Asset Path | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|------------|--------|-------------------------|--------------------|------------------|----------------|
| `src/application/usecases/` | Archive | `src/application/use_cases/` (new modular orchestrations) | See dependency map (`Hard`: legacy imports) | Move surviving helpers into `use_cases/` if referenced | Application TL |
| `src/application/usecases/` | Archived 2025-11-09 | Logic migrated to `src/application/use_cases/` (+ DTOs) | Resolved | Preserve legacy implementation snapshot in archive bundle | Application TL |
| `src/domain/agents/` | Archive (Wave 3) | `src/presentation/bot/orchestrator.py`, `src/presentation/bot/handlers/*`, `src/application/services/mode_classifier.py` | See dependency map (`Hard`: agent references) | Retain README snapshot in archive | Domain TL |
| `src/domain/agents/handlers/reminders_handler.py` | Archived 2025-11-09 | Summary worker + CLI notifications handle user messaging | Completed | Dialog mode falls back to chat; reminders mode retired | Domain TL |
| `src/infrastructure/notifiers/telegram/` | Archive (pending confirmation) | CLI backoffice notifications + structured logging | See dependency map (`Soft`) | Ensure digest notifications remain in `src/presentation/bot` | Infrastructure TL |
| `src/presentation/bot/handlers/tasks.py` | Archive | Digest/channel handlers only | See dependency map (`No blockers`) | Remove state references from `states.py` before archive | Presentation TL |
| `src/presentation/mcp/tools/homework_review_tool.py` | Retain (Refactored) | Modular reviewer MCP wrapper shipped Stage 04_02 | Dependency resolved (`Completed`) | Remove deprecation notices; update docs to reference new workflow | EP01 TL |
| `src/presentation/mcp/tools/pdf_digest_tools.py` | Deprecate → Archive | Stage 02_02 CLI digest export | See dependency map (`Soft`) | Provide CLI how-to in comms pack | EP02 TL |
| `src/presentation/mcp/tools/reminder_tools.py` | Archive | Feature retired (no replacement) | See dependency map (`No blockers`) | Remove from MCP registry immediately | EP02 TL |
| `src/presentation/mcp/tools/_summary_helpers.py` | Relocate → Archive | CLI backoffice shared formatters | See dependency map (`Soft`) | Move reusable functions before archive | EP02 TL |
| `src/presentation/mcp/adapters/orchestration_adapter.py` | Archived 2025-11-09 | MCPApplicationAdapter sequential workflow using modular reviewer services | Resolved | Legacy multi-agent adapter retired; MCPApplicationAdapter handles orchestration inline | EP02 TL |
| `src/infrastructure/mcp/orchestrators/mcp_mistral_wrapper.py` | Archive | Modular reviewer orchestration | See dependency map (`No blockers`) | Capture architecture notes in archive README | EP02 TL |
| `src/presentation/mcp/cli/interactive_mistral_chat.py` | Archive | CLI backoffice deterministic commands | See dependency map (`No blockers`) | Replace doc references with CLI instructions | EP02 TL |
| `src/presentation/mcp/cli/streaming_chat.py` | Archive | CLI backoffice deterministic commands | See dependency map (`No blockers`) | Remove console entry points | EP02 TL |
| `src/workers/message_sender.py` | Archived 2025-11-09 | Summary worker owns notification flow | Resolved | Retry helper inlined; schedulers updated | Workers TL |
| `src/workers/schedulers.py` (reminder branches) | Archive | CLI-triggered digest scheduling | See dependency map (`Soft`) | Split digest scheduling into dedicated module | Workers TL |

## MCP Tools (Registry Impact)

| MCP Tool | Module | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|----------|--------|--------|-------------------------|--------------------|------------------|----------------|
| Homework review | `src/presentation/mcp/tools/homework_review_tool.py` | Active (Refactored) | Modular reviewer MCP tool (Stage 04_02) | Dependency resolved (`Completed`) | Remove feature flag docs; advertise CLI + MCP parity | EP01 TL |
| PDF digest | `src/presentation/mcp/tools/pdf_digest_tools.py` | Deprecate → Archive | CLI digest export (`digest:export`) | See dependency map (`Soft`) | CLI command shipped 2025-11-09; remove MCP module and tests in Wave 1 | EP02 TL |
| Reminder tools | `src/presentation/mcp/tools/reminder_tools.py` | Archive | No replacement | See dependency map (`No blockers`) | Delete registry bindings immediately | EP02 TL |
| Channel bulk ops | `src/presentation/mcp/tools/channels/channel_management.py` | Move to CLI | Backoffice CLI (`channels:*`) | See dependency map (`Soft`) | Retain read-only MCP paths until CLI rollout completes | EP02 TL |
| Channel posts ops | `src/presentation/mcp/tools/channels/posts_management.py` | Move to CLI | Backoffice CLI worker integration | See dependency map (`Soft`) | Deprecate in docs, final removal post CLI adoption | EP02 TL |
| Summary helpers | `src/presentation/mcp/tools/_summary_helpers.py` | Relocate → Archive | CLI formatting utilities | See dependency map (`Soft`) | Extract shared templates before archive | EP02 TL |

## Documentation

| Document | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|----------|--------|-------------------------|--------------------|------------------|----------------|
| `docs/guides/en/AGENT_INTEGRATION.md` / `docs/guides/ru/AGENT_INTEGRATION.ru.md` | Archive | Modular reviewer integration guide + specs | See dependency map (`Soft`) | Link archive copy from README index | Docs Owner |
| `docs/guides/en/MCP_HOMEWORK_REVIEW.md` | Archive | Updated MCP API reference (`docs/reference/en/API_MCP.md`) | See dependency map (`Soft`) | Ensure EN/RU copies removed | Docs Owner |
| `docs/guides/en/MCP_DEMO_GUIDE.md` | Archive | CLI backoffice demo instructions | See dependency map (`Soft`) | Capture video references in archive README | Docs Owner |
| `docs/guides/en/MCP_GUIDE.md` | Archive | MCP tool matrix + API docs | See dependency map (`Soft`) | Update navigation index | Docs Owner |
| `docs/guides/en/MCP_TOOL_USAGE.md` | Archive | CLI/MCP combined operations guide | See dependency map (`Soft`) | Replace links in specs | Docs Owner |
| `docs/reference/en/MODEL_SETUP.md` | Archive | Operations guide shared infra section | See dependency map (`Soft`) | Confirm local model references removed from scripts | Ops Owner |
| `docs/architecture/mcp_agent_prompt_tuning_report.md` | Archive | Modular reviewer prompt docs | See dependency map (`No blockers`) | Preserve metrics tables in archive README | Docs Owner |
| `docs/archive/local_models/**` (if any) | Confirm archive | Git history + new archive wave | See dependency map (`No blockers`) | Move remaining notes into `archive/ep04_2025-11/docs/` | Docs Owner |

## Scripts & Automation

| Script / Folder | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|-----------------|--------|-------------------------|--------------------|------------------|----------------|
| `scripts/start_models.sh` | Archived 2025-11-09 | Shared infra bootstrap (`make day-12-up`) | See dependency map (`Soft`) | Docs updated to reference `scripts/infra/start_shared_infra.sh` | Ops Owner |
| `scripts/infra/check_model_status.sh` | Archived 2025-11-09 | Shared infra health checks (`scripts/quality/test_review_system.py`) | See dependency map (`Soft`) | README updated with new verification steps | Ops Owner |
| `scripts/wait_for_model.sh` | Archived 2025-11-09 | Shared infra readiness checks | See dependency map (`Soft`) | README updated with readiness guidance | Ops Owner |
| `scripts/ci/test_day10.sh` | Archived 2025-11-09 | Updated CI pipelines (EP01) | See dependency map (`Soft`) | Makefile/doc references dropped | Ops Owner |
| `scripts/day12_run.py` | Archived 2025-11-09 | `make day-12-up` + CLI commands | See dependency map (`Soft`) | Shared infra wrapper + Makefile update in place | Ops Owner |
| `scripts/mcp_comprehensive_demo.py` | Archived 2025-11-09 | CLI backoffice demo script | See dependency map (`Soft`) | Backoffice CLI tests cover discovery | EP02 TL |
| `scripts/infra/healthcheck_mcp.py` | Archived 2025-11-09 | `scripts/quality/test_review_system.py --metrics` | See dependency map (`Soft`) | Ops docs reference review system script | EP03 TL |
| `scripts/telegram_channel_reader.session` | Delete | Not required (credential artifact) | See dependency map (`No blockers`) | Ensure secret rotation policy referenced | Ops Owner |

## Prompts & Resources

| Asset | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|-------|--------|-------------------------|--------------------|------------------|----------------|
| `prompts/v1/pass_*/` | Relocate → Archive | `packages/multipass-reviewer/prompts/` | See dependency map (`Soft`) | Ensure package exposes importlib resources | EP01 TL |
| `src/presentation/mcp/prompts/**` | Archive | Modular reviewer prompt registry | See dependency map (`Soft`) | Confirm CLI uses new registry | EP02 TL |
| `src/presentation/mcp/resources/**` | Archive | CLI/importlib resources | See dependency map (`Soft`) | Move live assets before archive | EP02 TL |

## Tests

| Test Suite / File | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|-------------------|--------|-------------------------|--------------------|------------------|----------------|
| `src/tests/presentation/mcp/test_pdf_digest_tools.py` | Archived 2025-11-09 | CLI digest export tests (Stage 02_02) | Resolved | Legacy suite moved to archive; CLI coverage in place | QA Lead |
| `src/tests/presentation/mcp/test_reminder_tools.py` | Archive | None (feature removed) | See dependency map (`No blockers`) | Remove skip markers referencing reminders | QA Lead |
| `src/tests/presentation/mcp/test_performance.py` (legacy expectations) | Archive | New performance benchmarks (EP03/EP05) | See dependency map (`Soft`) | Capture threshold notes in archive README | QA Lead |
| `tests/presentation/mcp/**` (legacy duplicates) | Archive | Unified `src/tests/` suites | See dependency map (`Soft`) | Verify CI excludes archived path | QA Lead |
| `src/tests/workers/test_message_sender.py` | Archived 2025-11-09 | Digest workflow covered by summary worker integration | Resolved | Legacy suite retired with helper | QA Lead |
| `tests/integration/test_pdf_digest_flow.py` | Archived 2025-11-09 | CLI digest export replaces PDF MCP flow | Resolved | Integration suite moved to archive; re-implement via CLI if needed | QA Lead |
| `tests/integration/test_mcp_comprehensive_demo.py` | Archived 2025-11-09 | Backoffice CLI integration tests replace legacy demo | Resolved | New CLI tests added under `tests/integration/presentation/cli` | QA Lead |
| `tests/contract/test_mcp_tools_schema.py` | Archived 2025-11-09 | CLI contracts maintained via new services | Resolved | Contract tests referencing legacy MCP removed | QA Lead |

## Approvals

| Stakeholder | Role | Approval Needed |
|-------------|------|-----------------|
| EP01 Tech Lead | Modular reviewer hardening | Confirm legacy reviewer assets ready for archive |
| EP02 Tech Lead | MCP & bot consolidation | Confirm MCP tool replacements and CLI availability |
| EP03 Tech Lead | Observability & ops | Ensure logging/metrics coverage preserved post-archive |
| Documentation Owner | Docs consolidation | Validate doc replacements and navigation updates |
| Operations Owner | Scripts & infra | Confirm shared infra commands cover retired scripts |
| QA Lead | Testing | Agree on replacement test suites and coverage |

## Next Steps

1. Finalise dependency analysis (`dependency_map.md`) and address any `Hard`
   blockers.
2. Publish communication plan with timelines and stakeholder responsibilities.
3. Confirm archive folder structure and manifest before moving files in Stage
   04_02.
4. Collect evidence (search logs, test baselines, sign-offs) and store under
   `docs/specs/epic_04/evidence/`.
