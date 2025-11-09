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
| `src/domain/agents/` | Archive | `packages/multipass-reviewer` services and `src/application/services/modular_review_service.py` | See dependency map (`Hard`: agent references) | Retain README snapshot in archive | Domain TL |
| `src/infrastructure/notifiers/telegram/` | Archive (pending confirmation) | CLI backoffice notifications + structured logging | See dependency map (`Soft`) | Ensure digest notifications remain in `src/presentation/bot` | Infrastructure TL |
| `src/presentation/bot/handlers/tasks.py` | Archive | Digest/channel handlers only | See dependency map (`No blockers`) | Remove state references from `states.py` before archive | Presentation TL |
| `src/presentation/mcp/tools/homework_review_tool.py` | Deprecate → Archive | Modular reviewer CLI/MCP replacement (post EP01) | See dependency map (`Hard`: gated usage) | Communicate final cutoff to MCP consumers | EP01 TL |
| `src/presentation/mcp/tools/pdf_digest_tools.py` | Deprecate → Archive | Stage 02_02 CLI digest export | See dependency map (`Soft`) | Provide CLI how-to in comms pack | EP02 TL |
| `src/presentation/mcp/tools/reminder_tools.py` | Archive | Feature retired (no replacement) | See dependency map (`No blockers`) | Remove from MCP registry immediately | EP02 TL |
| `src/presentation/mcp/tools/_summary_helpers.py` | Relocate → Archive | CLI backoffice shared formatters | See dependency map (`Soft`) | Move reusable functions before archive | EP02 TL |
| `src/infrastructure/mcp/adapters/orchestration_adapter.py` | Archive | Modular reviewer adapters (`review_adapter`, `model_adapter`) | See dependency map (`Soft`) | Validate tests switch to new adapters | EP02 TL |
| `src/infrastructure/mcp/orchestrators/mcp_mistral_wrapper.py` | Archive | Modular reviewer orchestration | See dependency map (`No blockers`) | Capture architecture notes in archive README | EP02 TL |
| `src/presentation/mcp/cli/interactive_mistral_chat.py` | Archive | CLI backoffice deterministic commands | See dependency map (`No blockers`) | Replace doc references with CLI instructions | EP02 TL |
| `src/presentation/mcp/cli/streaming_chat.py` | Archive | CLI backoffice deterministic commands | See dependency map (`No blockers`) | Remove console entry points | EP02 TL |
| `src/workers/message_sender.py` | Archive | Digest workers (`summary_worker.py`) only | See dependency map (`Soft`) | Confirm schedulers drop reminder jobs | Workers TL |
| `src/workers/schedulers.py` (reminder branches) | Archive | CLI-triggered digest scheduling | See dependency map (`Soft`) | Split digest scheduling into dedicated module | Workers TL |

## MCP Tools (Registry Impact)

| MCP Tool | Module | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|----------|--------|--------|-------------------------|--------------------|------------------|----------------|
| Homework review | `src/presentation/mcp/tools/homework_review_tool.py` | Deprecate → Archive | Modular reviewer MCP tool (post EP01) | See dependency map (`Hard`) | Keep behind feature flag until replacement ships | EP01 TL |
| PDF digest | `src/presentation/mcp/tools/pdf_digest_tools.py` | Deprecate → Archive | CLI digest export (`digest:export`) | See dependency map (`Soft`) | Remove from default registry now | EP02 TL |
| Reminder tools | `src/presentation/mcp/tools/reminder_tools.py` | Archive | No replacement | See dependency map (`No blockers`) | Delete registry bindings immediately | EP02 TL |
| Channel bulk ops | `src/presentation/mcp/tools/channels/channel_management.py` | Move to CLI | Backoffice CLI (`channels:*`) | See dependency map (`Soft`) | Retain read-only MCP paths until CLI rollout completes | EP02 TL |
| Channel posts ops | `src/presentation/mcp/tools/channels/posts_management.py` | Move to CLI | Backoffice CLI worker integration | See dependency map (`Soft`) | Deprecate in docs, final removal post CLI adoption | EP02 TL |
| Summary helpers | `src/presentation/mcp/tools/_summary_helpers.py` | Relocate → Archive | CLI formatting utilities | See dependency map (`Soft`) | Extract shared templates before archive | EP02 TL |

## Documentation

| Document | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|----------|--------|-------------------------|--------------------|------------------|----------------|
| `docs/AGENT_INTEGRATION.md` / `.ru.md` | Archive | Modular reviewer integration guide + specs | See dependency map (`Soft`) | Link archive copy from README index | Docs Owner |
| `docs/MCP_HOMEWORK_REVIEW.md` | Archive | Updated MCP API reference (`docs/API_MCP.md`) | See dependency map (`Soft`) | Ensure EN/RU copies removed | Docs Owner |
| `docs/MCP_DEMO_GUIDE.md` | Archive | CLI backoffice demo instructions | See dependency map (`Soft`) | Capture video references in archive README | Docs Owner |
| `docs/MCP_GUIDE.md` | Archive | MCP tool matrix + API docs | See dependency map (`Soft`) | Update navigation index | Docs Owner |
| `docs/MCP_TOOL_USAGE.md` | Archive | CLI/MCP combined operations guide | See dependency map (`Soft`) | Replace links in specs | Docs Owner |
| `docs/MODEL_SETUP.md` | Archive | Operations guide shared infra section | See dependency map (`Soft`) | Confirm local model references removed from scripts | Ops Owner |
| `docs/architecture/mcp_agent_prompt_tuning_report.md` | Archive | Modular reviewer prompt docs | See dependency map (`No blockers`) | Preserve metrics tables in archive README | Docs Owner |
| `docs/archive/local_models/**` (if any) | Confirm archive | Git history + new archive wave | See dependency map (`No blockers`) | Move remaining notes into `archive/ep04_2025-11/docs/` | Docs Owner |

## Scripts & Automation

| Script / Folder | Status | Successor / Replacement | Dependencies Found | Special Handling | Owner Sign-off |
|-----------------|--------|-------------------------|--------------------|------------------|----------------|
| `scripts/start_models.sh` | Archive | Shared infra bootstrap (`make day-12-up`) | See dependency map (`Soft`) | Remove references from docs | Ops Owner |
| `scripts/check_model_status.sh` | Archive | Shared infra health checks (`scripts/test_review_system.py`) | See dependency map (`Soft`) | Provide alternative command list | Ops Owner |
| `scripts/wait_for_model.sh` | Archive | Shared infra readiness checks | See dependency map (`Soft`) | Document new readiness workflow | Ops Owner |
| `scripts/ci/test_day10.sh` | Archive | Updated CI pipelines (EP01) | See dependency map (`Soft`) | Delete invocation from CI configs | Ops Owner |
| `scripts/day12_run.py` | Archive | `make day-12-up` + CLI commands | See dependency map (`Soft`) | Capture usage samples in archive README | Ops Owner |
| `scripts/mcp_comprehensive_demo.py` | Archive | CLI backoffice demo script | See dependency map (`Soft`) | Replace doc references | EP02 TL |
| `scripts/healthcheck_mcp.py` | Archive | `scripts/test_review_system.py --metrics` | See dependency map (`Soft`) | Confirm CI jobs point to new script | EP03 TL |
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
| `src/tests/presentation/mcp/test_pdf_digest_tools.py` | Archive | CLI digest export tests (Stage 02_02) | See dependency map (`Soft`) | Mark xfail until CLI tests merge | QA Lead |
| `src/tests/presentation/mcp/test_reminder_tools.py` | Archive | None (feature removed) | See dependency map (`No blockers`) | Remove skip markers referencing reminders | QA Lead |
| `src/tests/presentation/mcp/test_performance.py` (legacy expectations) | Archive | New performance benchmarks (EP03/EP05) | See dependency map (`Soft`) | Capture threshold notes in archive README | QA Lead |
| `tests/presentation/mcp/**` (legacy duplicates) | Archive | Unified `src/tests/` suites | See dependency map (`Soft`) | Verify CI excludes archived path | QA Lead |
| `src/tests/workers/test_message_sender.py` | Archive | Digest worker tests | See dependency map (`Soft`) | Remove fixture dependencies on reminders | QA Lead |

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


