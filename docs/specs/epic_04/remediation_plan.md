# Stage 04_02 · Hard Dependency Remediation Plan

Prepared: 2025-11-09
Owner: Assistant (Tech Lead)

## Wave Overview

| Wave | Focus | Assets | Key Actions | Dependencies | Target Window |
|------|-------|--------|-------------|--------------|----------------|
| Wave 0 | Documentation & Registry Prep | `docs/API_*`, MCP registry flags | Draft deprecation notices, gate deprecated tools behind flags | Sign-off approvals | T+0 to T+1 |
| Wave 1 | MCP Tool Replacement | `homework_review_tool`, `pdf_digest_tools`, `reminder_tools`, `orchestration_adapter` references | Implement modular reviewer MCP replacement stub, ship CLI digest export, remove reminder tool entrypoints, refactor MCP adapter wiring | EP01 reviewer API readiness, CLI backoffice availability | T+1 to T+5 |
| Wave 2 | Worker & Scheduler Cleanup | `message_sender.py`, reminder branches in `schedulers.py`, tests | Migrate digest send logic into summary worker, remove reminder jobs/tests, update metrics | Wave 1 completion | T+5 to T+7 |
| Wave 3 | Legacy Use Case / Domain Agents | `src/application/usecases/`, `src/domain/agents/*`, bot handler dependencies | Replace bot orchestration with modular reviewer services, migrate use case imports, archive legacy agent packages, update tests/docs | EP02 Telegram scope alignment, QA automation support | T+7 to T+12 |
| Wave 4 | CLI Orchestrator Deprecation | `mcp_mistral_wrapper`, `interactive_mistral_chat.py`, `streaming_chat.py`, legacy CLI commands | Replace CLI flows with backoffice commands, update Makefile/docs, archive legacy scripts | Wave 1 CLI deliverables | T+5 to T+8 (Completed 2025-11-09) |

## Detailed Tasks

### Wave 0
- Publish deprecation warnings in `src/presentation/mcp/server.py` for deprecated tools.
- Update `docs/API_MCP*.md` with retirement timeline and replacement commands.
- Coordinate with docs owner to schedule PR reviews.

### Wave 1
- **Homework review:** Completed 2025-11-09 — Modular reviewer MCP wrapper shipped, registry updated, tests migrated.
- **PDF digest:** Completed 2025-11-09 — CLI `digest:export` command added, PDF generation moved to backoffice; MCP registration scheduled for removal.
- **Reminder tools:** Completed 2025-11-09 — removed from registry, archived module/tests, bot reminder states scheduled for removal in Wave 2.
- **Orchestration adapter:** Completed 2025-11-09 — MCPApplicationAdapter now chains generation/review adapters; legacy orchestrator archived.

### Wave 2
- Completed 2025-11-09 — summary worker now owns notification pipeline; `send_with_retry` inlined and legacy helper archived.
- Reminder scheduler branches removed; cron references scheduled for cleanup alongside worker docs.
- Worker coverage aligned to digest-only behaviour (pending additional telemetry update).

### Wave 3
- Butler orchestrator no longer depends on reminders handler; dialog mode classifier falls back to chat (Completed 2025-11-09).
- Archived `src/application/usecases/` after migrating remaining flows to `use_cases/` and DTOs (2025-11-09).
- Replace bot factory dependencies on legacy agents with application services backed by modular reviewer.
- Remove legacy agent tests or convert to cover new services.
- Provide migration summary in bot and domain docs.

### Wave 4
- Completed 2025-11-09 — retired Mistral CLI orchestrator (`interactive_mistral_chat.py`, `streaming_chat.py`, `mcp_mistral_wrapper.py`) and associated use cases.
- Makefile targets now reference backoffice CLI helpers; docs updated to highlight deterministic CLI flows.
- Legacy CLI command modules and tests archived; integration suite aligned to modular reviewer/backoffice usage.

### Wave 4
- Update Makefile to drop legacy CLI entrypoints and reference backoffice commands.
- Archive CLI chat scripts and add pointers in `docs/MCP_GUIDE.md`.
- Remove tests/integration referencing Mistral wrapper.

## Coordination & Approvals

- Share wave plan with EP02/EP03 leads for resource scheduling.
- Align QA on regression suite focus per wave.
- Maintain sign-off status in `signoff_log.md`.

## Tracking

- Update `archive_scope.md` and `ARCHIVE_MANIFEST.md` after each wave.
- Record evidence (grep reports, test baselines) per wave in `docs/specs/epic_04/evidence/`.
- Document completion in `stage_04_02.md` migration log section.
