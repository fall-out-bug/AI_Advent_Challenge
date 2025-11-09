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
| `src/application/usecases/` | Imported by bot factory, tests, legacy handlers (`src/presentation/bot/factory.py`, `tests/unit/application/usecases/*`, docs) | Migrate remaining flows to `src/application/use_cases/` and adjust imports; archive after parity tests pass | Blocked |
| `src/domain/agents/*` | Imported across bot handlers, MCP adapters, orchestration tests (`src/presentation/bot/butler_bot.py`, `src/presentation/mcp/adapters/{generation,review}_adapter.py`, numerous tests) | Replace with modular reviewer pathways; retire bot orchestration or shim modular services | Blocked |
| `src/presentation/mcp/tools/homework_review_tool.py` | Registered in `src/presentation/mcp/server.py`, referenced in tests (`tests/unit/presentation/mcp/tools/test_homework_review_tool.py`), docs (`docs/API_REVIEWER*.md`) | Introduce modular reviewer MCP replacement; update registry and tests before archive | Blocked |
| `src/presentation/mcp/tools/reminder_tools.py` | Imported in E2E tests (`src/tests/e2e/test_bot_flows.py`), reminder tests, legacy docs | Remove reminder flows/tests; ensure bot states drop reminders prior to archive | Blocked |
| `src/presentation/mcp/tools/pdf_digest_tools.py` | Registered in MCP server, used in monitoring tests, integration suites | Deliver CLI digest export + new tests; update monitoring to new metrics hooks | Blocked |
| `src/infrastructure/mcp/adapters/orchestration_adapter.py` | Instantiated in `src/presentation/mcp/adapters.py`, referenced by tests | Refactor MCP adapters to call modular reviewer service directly; delete orchestration adapter afterwards | Blocked |
| `src/presentation/mcp/orchestrators/mcp_mistral_wrapper.py` | Used by CLI chat scripts, integration tests, examples | Replace CLI flows with deterministic backoffice; migrate examples/tests | Blocked |
| `src/workers/message_sender.py` | Imported by `src/workers/summary_worker.py` | Inline digest-specific sender or move helper into summary worker; adjust tests | Blocked |
| `src/workers/schedulers.py` (reminder branches) | Reminder scheduling invoked by workers/tests | Remove reminder jobs, confirm digest scheduling moved to dedicated module | Blocked |

## Soft Dependencies

| Asset | References | Required Update | Status |
|-------|------------|-----------------|--------|
| `src/presentation/mcp/cli/interactive_mistral_chat.py` | Invoked from `Makefile`, documented in `docs/MCP_GUIDE.md` | Remove Makefile targets; replace docs with CLI backoffice instructions | Planned |
| `src/presentation/mcp/cli/streaming_chat.py` | Invoked from `Makefile`, docs, day tasks | Same as above | Planned |
| `scripts/start_models.sh` / `wait_for_model.sh` / `check_model_status.sh` | Referenced in docs and older scripts | Update docs to shared infra commands; drop references | Planned |
| `scripts/ci/test_day10.sh` | Mentioned in CI docs (`docs/specs/epic_00/stage_00_01.md`) | Remove from CI configs and docs | Planned |
| `scripts/day12_run.py` | Referenced in docs and scripts README | Replace with `make day-12-up` instructions | Planned |
| `scripts/mcp_comprehensive_demo.py` | Linked in MCP guides | Replace with CLI walkthrough | Planned |
| `scripts/healthcheck_mcp.py` | Linked in ops docs | Update to use `scripts/test_review_system.py --metrics` | Planned |
| `docs/AGENT_INTEGRATION*.md`, `docs/MCP_*` guides, `docs/MODEL_SETUP.md` | Linked from doc index, README, day guides | Update indices to point at successor docs | Planned |
| `prompts/v1/pass_*`, `src/presentation/mcp/prompts/**` | Referenced in modular reviewer docs and CLI | Move to package resources; update imports | Planned |
| `scripts/telegram_channel_reader.session` | Mentioned in `docs/telegram_setup.md`, `scripts/init_pyrogram.py` | Document new credential flow; delete file | Planned |

## Test-Only Dependencies

| Asset | Tests Depending | Action | Status |
|-------|-----------------|--------|--------|
| `src/tests/presentation/mcp/test_pdf_digest_tools.py` | Direct imports of MCP PDF digest functions | Replace with CLI digest tests; archive legacy suite | Pending |
| `src/tests/presentation/mcp/test_reminder_tools.py` | Imports reminder tools only | Remove once reminder MCP archived | Pending |
| `tests/unit/presentation/mcp/tools/test_homework_review_tool.py` | Tests deprecated tool | Replace with modular reviewer MCP tests | Pending |
| `src/tests/workers/test_message_sender.py` | Exercises reminder sender | Drop after worker refactor | Pending |
| `tests/integration/test_day10_e2e.py` | Exercises Mistral wrapper CLI | Remove/replace with Stage 02 CLI scenario | Pending |

## No Detected Dependencies

| Asset | Notes | Action |
|-------|-------|--------|
| `docs/archive/local_models/**` | Already isolated under `docs/archive` | Move to new archive wave for consistency | Proceed |
| `docs/architecture/mcp_agent_prompt_tuning_report.md` | Only referenced in archive scope | Safe to relocate | Proceed |
| `tests/presentation/mcp/**` (legacy duplicates under `tests/`) | Not executed in CI; superseded by `src/tests/` | Archive with manifest | Proceed |

## Blocker Summary

- **Total hard blockers:** 9  
  - Owners: Application, Domain, EP01, EP02, Workers.
- **Soft dependencies requiring doc/workflow updates:** 10
- **Test-only dependencies to retire alongside archives:** 5

## Follow-Up Actions

1. Assign remediation tasks for each hard dependency to epic owners.
2. Prepare doc/Makefile updates to land with archival PRs.
3. Schedule test suite rewrites or mark as xfail until replacements merge.
4. Attach updated dependency status when requesting approvals.


