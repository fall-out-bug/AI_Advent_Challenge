# Stage 04_01 · Dependency Map

This map records active dependencies for each archive candidate so that Stage
04_02 migrations can proceed safely. References were gathered on 2025-11-09
using repository searches (saved under `docs/specs/epic_04/evidence/`).

## Legend

- **Hard** — Active runtime dependency; archive blocked until replacement lands.
- **Soft** — Documentation, Makefile, or optional tooling reference; update in
  same PR as archive.
- **Test-Only** — Referenced solely in tests/fixtures; archive with associated
  tests or rewrite coverage.
- **None** — No references detected; safe to archive once approvals complete.

## Hard Dependencies

| Asset | Key References | Remediation | Status |
|-------|----------------|-------------|--------|
| `src/application/usecases/` | Previously imported by bot factory, tests, docs | Migrated to `src/application/use_cases/` + `src/application/dtos/butler_use_case_dtos.py`; archive directory | Completed 2025-11-09 |
| `src/domain/agents/*` | Previously wired into bot factory, orchestrator, and integration tests | Replaced by `src/presentation/bot/orchestrator.py` and handlers under `src/presentation/bot/handlers/`; tests updated accordingly | Completed |
| `src/presentation/mcp/tools/homework_review_tool.py` | Registered in `src/presentation/mcp/server.py`, referenced in docs (`docs/API_REVIEWER*.md`) | Refactored 2025-11-09 to modular reviewer MCP; registry updated, docs next | Completed |
| `src/presentation/mcp/adapters/orchestration_adapter.py` | Previously instantiated in `src/presentation/mcp/adapters.py`, referenced by tests | Archived 2025-11-09; MCPApplicationAdapter now chains generation+review adapters | Completed |
| `src/presentation/mcp/orchestrators/mcp_mistral_wrapper.py` | Used by CLI chat scripts, integration tests, examples | Archived 2025-11-09; backoffice CLI replaces interactive chat flows | Completed |
| `src/workers/message_sender.py` | Previously imported by `src/workers/summary_worker.py` | Archived 2025-11-09; summary worker now sends notifications directly | Completed |
| `src/workers/schedulers.py` (reminder branches) | Reminder scheduling invoked by workers/tests | Remove reminder jobs, confirm digest scheduling moved to dedicated module | Blocked |

## Soft Dependencies

| Asset | References | Required Update | Status |
|-------|------------|-----------------|--------|
| `src/presentation/mcp/cli/interactive_mistral_chat.py` | Invoked from `Makefile`, documented in `docs/MCP_GUIDE.md` | Removed from Makefile/docs; archived under `archive/ep04_2025-11/` | Completed 2025-11-09 |
| `src/presentation/mcp/cli/streaming_chat.py` | Invoked from `Makefile`, docs, day tasks | Removed from Makefile/docs; archived | Completed 2025-11-09 |
| `scripts/start_models.sh` / `wait_for_model.sh` / `check_model_status.sh` | Referenced in docs and older scripts | Docs updated 2025-11-09 to point at `scripts/start_shared_infra.sh`; legacy scripts archived | Completed 2025-11-09 |
| `scripts/ci/test_day10.sh` | Mentioned in CI docs (`docs/specs/epic_00/stage_00_01.md`) | Makefile/docs updated; archive entry recorded | Completed 2025-11-09 |
| `scripts/day12_run.py` | Referenced in docs and scripts README | Stub + Makefile update replaced with shared infra wrapper | Completed 2025-11-09 |
| `scripts/mcp_comprehensive_demo.py` | Linked in MCP guides | Makefile/docs now reference backoffice CLI; integration test archived | Completed 2025-11-09 |
| `scripts/healthcheck_mcp.py` | Linked in ops docs | Ops docs direct to `scripts/test_review_system.py --metrics`; script stub archived | Completed 2025-11-09 |
| `docs/AGENT_INTEGRATION*.md`, `docs/MCP_*` guides, `docs/MODEL_SETUP.md` | Linked from doc index, README, day guides | Update indices to point at successor docs | Planned |
| `prompts/v1/pass_*`, `src/presentation/mcp/prompts/**` | Referenced in modular reviewer docs and CLI | Move to package resources; update imports | Planned |
| `scripts/telegram_channel_reader.session` | Mentioned in `docs/telegram_setup.md`, `scripts/init_pyrogram.py` | Document new credential flow; delete file | Planned |

## Test-Only Dependencies

| Asset | Tests Depending | Action | Status |
|-------|-----------------|--------|--------|
| `src/tests/presentation/mcp/test_pdf_digest_tools.py` | Direct imports of MCP PDF digest functions | Archived 2025-11-09; CLI tests cover export flow | Completed |
| `tests/unit/presentation/mcp/tools/test_homework_review_tool.py` | Tests modular reviewer MCP workflow | Updated 2025-11-09; coverage migrated off deprecated flows | Completed |
| `src/tests/workers/test_message_sender.py` | Legacy reminder sender tests | Archived prior to Stage 04_02; no active suite remaining | Completed |
| `tests/integration/test_day10_e2e.py` | Exercises Mistral wrapper CLI | Remove/replace with Stage 02 CLI scenario | Pending |

## No Detected Dependencies

| Asset | Notes | Action |
|-------|-------|--------|
| `docs/archive/local_models/**` | Already isolated under `docs/archive` | Move to new archive wave for consistency | Proceed |
| `docs/architecture/mcp_agent_prompt_tuning_report.md` | Only referenced in archive scope | Safe to relocate | Proceed |
| `tests/presentation/mcp/**` (legacy duplicates under `tests/`) | Not executed in CI; superseded by `src/tests/` | Archive with manifest | Proceed |

## Blocker Summary

- **Total hard blockers:** 5
  - Owners: Application, Domain, EP01, EP02, Workers.
- **Soft dependencies requiring doc/workflow updates:** 10
- **Test-only dependencies to retire alongside archives:** 5

## Follow-Up Actions

1. Assign remediation tasks for each hard dependency to epic owners.
2. Prepare doc/Makefile updates to land with archival PRs.
3. Schedule test suite rewrites or mark as xfail until replacements merge.
4. Attach updated dependency status when requesting approvals.
