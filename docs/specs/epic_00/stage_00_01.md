# Stage 00_01 · Current-State Inventory

## Goal
Create a comprehensive map of repository assets and compare them with day-based
specifications. This stage captures what exists today and where it diverges from
expected behaviour.

## Checklist
- [x] Catalogue top-level directories (src/, packages/, shared/, docs/, scripts/, tests/).
- [x] Tag each module/component as **Keep / Archive / Rework**.
- [x] Cross-reference day specs (Day 11, 12, 15, 17, 18…) to ensure coverage.
- [x] Document known failing test suites and underlying causes.
- [x] Identify external dependencies (Mongo, Prometheus, LLM, Telegram, etc.).

### Completed Tasks
- Built MCP tool catalogue with keep/archive/rework decisions (see table below).
- Drafted CLI backoffice requirements (see section below) mapping bot scenarios to deterministic commands.

### In-Progress Tasks
- None (awaiting closure sign-off).

## Artifacts
- Component inventory table (to be embedded here once complete).
- Links to relevant source directories and existing design docs.
- Notes on discrepancies between code and historical specifications.

## Questions / Open Items
- Are Telegram-dependent flows still required, or should they be archived?
  **Decision:** reminder/tasks flows will move to archive; subscription and
  digest scenarios stay active (recorded in Stage 00_02).
- What is the minimum viable test baseline for CI while large lint debt exists?
  **Decision:** enforce passing tests on non-legacy code paths only (recorded in
  Stage 00_02).

## Status
*Completed — inventory consumed by Stage 00_02 decisions.*

## Repository Inventory (draft)

| Component | Path | Status | Notes |
|-----------|------|--------|-------|
| Core application | `src/` | Keep | Needs module-level tagging; multiple legacy flows still present. |
| Shared SDK | `shared/` | Keep | Acts as editable dependency for unified clients. |
| Modular reviewer package | `packages/multipass-reviewer/` | Keep | Canonical reviewer implementation. |
| Legacy reviewer assets | `archive/legacy/local_models/` | Archive | Already relocated; ensure references removed. |
| Documentation | `docs/` | Rework | Consolidate under `docs/specs/`, archive outdated guides. |
| Tests | `tests/`, `src/tests/` | Rework | Maintain green state for non-legacy suites. |
| Scripts | `scripts/` | Keep | Health checks and infra helpers; audit for legacy references. |
| Prompts | `prompts/` | Rework | Align with modular reviewer prompts/resources. |
| Examples / contracts / tasks | `examples/`, `contracts/`, `tasks/` | Evaluate | Determine ongoing relevance per stage 00_02. |

### MCP Tool Catalogue (updated draft)
| Tool | File/Module | Current Role | Updated Status |
|------|-------------|--------------|----------------|
| Homework review | `homework_review_tool.py` | Runs modular reviewer | Deprecate → replace with new tool built on refactored module |
| Digest generation | `digest_tools.py`, `channels/channel_digest.py` | Subscriptions and digests | Keep/Rework → keep subscriptions, daily digest, per-channel summary |
| Channel management & metadata | `channels/channel_management.py`, `channel_metadata.py`, `channel_resolution.py`, `posts_management.py` | Subscription/metadata/data collection management | Keep/Rework → move bulk operations into backoffice, expose MCP hooks if needed |
| PDF digest | `pdf_digest_tools.py` | PDF reports | Deprecate |
| NLP utilities | `nlp_tools.py` | User intent recognition | Keep |
| Reminder tools | `reminder_tools.py` | Reminders and tasks | Archive |
| Summary helpers | `_summary_helpers.py` | Shared summary helpers | Move to backoffice / reuse selectively |

### Top-Level Directory Snapshot (2025-11-09)
| Directory | Description | Preliminary Status |
|-----------|-------------|---------------------|
| `src/` | Main application layers (domain, application, infrastructure, presentation) | Keep (needs detailed tagging) |
| `packages/` | Modular reviewer package and other reusable modules | Keep |
| `shared/` | Editable shared SDK | Keep |
| `tests/` | Legacy monorepo test suite | Rework (focus on non-legacy coverage) |
| `docs/` | Documentation (day specs, guides, new specs) | Rework/Archive split |
| `scripts/` | Operational helpers, smoke tests | Keep |
| `archive/` | Legacy assets already parked | Archive |
| `prompts/` | Prompt assets (review, summarization) | Rework |
| `examples/`, `contracts/` | Supporting materials | Rework/Archive |
| `tasks/` | Historical artifacts | Keep (for history) |

### `src/` Module Breakdown (draft)
| Layer / Module | Description | Status | Notes |
|----------------|-------------|--------|-------|
| `src/application/dtos` | DTO definitions for orchestration/use cases | Keep | Ensure coverage in specs. |
| `src/application/orchestration` | Intent parsing orchestration | Rework | Align with new orchestrator dependencies. |
| `src/application/orchestrators` | Multi-agent orchestrators (legacy + new) | Rework | Decide which orchestrators remain; multi-agent path requires audit. |
| `src/application/services` | Context manager, modular reviewer adapter, rate limiter | Keep | Modular reviewer service is core. |
| `src/application/use_cases` | Use cases (review, digest, subscriptions) | Keep/Rework | Separate digest vs reminder flows. |
| `src/application/usecases` (legacy) | Older use-case implementations | Archive | Superseded by new `use_cases/`. |
| `src/domain/agents` | Butler agents, handlers, state machines | Rework | Remove references to deleted multi-pass reviewer. |
| `src/domain/entities` | Core entities (conversation, intent, task) | Keep | Validate against day specs. |
| `src/domain/intent` | Intent classifiers (rule-based, LLM, hybrid) | Keep | Requires refreshed tests. |
| `src/domain/services` | Diff analyzer, quality checker, etc. | Keep | Ensure modular reviewer integration. |
| `src/infrastructure/clients` | External clients (LLM, MCP, Telegram) | Rework | Telegram reminder pieces to archive. |
| `src/infrastructure/llm` | Summarizer, prompts, token counter | Rework | Align with modular reviewer + localization. |
| `src/infrastructure/logging` | Logging utilities | Keep | Structured logger in place. |
| `src/infrastructure/mcp` | Tools registry and adapters | Rework | Reflect supported tool set. |
| `src/infrastructure/notifiers/telegram` | Telegram notifier | Archive | Pending final confirmation. |
| `src/presentation/api` | HTTP APIs | Keep | Need contract review vs day specs. |
| `src/presentation/bot` | Telegram bot flows | Keep/Archive mix | Digest flows keep; reminders archive. |
| `src/presentation/mcp` | MCP server, adapters, tools | Rework | Key area for subsequent epics. |
| `src/workers` | Background workers | Rework | Logging/metrics cleanup needed. |
| `src/tests` | Newer test suites | Rework | Evaluate vs `tests/`. |
| `tests/` (root) | Legacy suites | Rework/Archive | Only subset remains active. |

**Orchestrator Track Notes**
- `multi_agent_orchestrator.py` is marked for archival (workflow deemed unused); remove from active scenarios.
- `CodeReviewerAgent` stays deprecated; ModularReviewService is the canonical replacement.
- `CodeGeneratorAgent` remains for future refactor — introduce interfaces/adapters to keep layer boundaries intact.
- MCP `orchestration_adapter.py` can be sunset alongside the workflow.

#### `src/presentation/mcp/tools` Breakdown
| Component | Status | Notes |
|-----------|--------|-------|
| `_summary_helpers.py` | Rework → move to backoffice | Shared helpers should become CLI/shared utilities. |
| `digest_tools.py` | Keep/Rework | Keep core digest endpoints; align with shared infra and Russian copy. |
| `homework_review_tool.py` | Deprecate | Replace with new module built on modular reviewer API. |
| `nlp_tools.py` | Keep | Required for intent parsing; ensure tests updated. |
| `pdf_digest_tools.py` | Deprecate | Functionality redundant; depends on heavy WeasyPrint stack. |
| `reminder_tools.py` | Archive | Reminders/tasks scenario dropped per decisions. |
| `channels/channel_digest.py` | Keep/Rework | Keep daily digest; refactor toward CLI-managed operations. |
| `channels/channel_management.py` | Keep/Rework | Move bulk management to CLI/backoffice; keep lightweight MCP hooks. |
| `channels/channel_metadata.py` | Keep | Needed for lookup flows; ensure logging/tests updated. |
| `channels/channel_resolution.py` | Keep/Rework | Validate relevance once CLI plan finalised. |
| `channels/posts_management.py` | Rework | Align with new storage strategy and auth. |
| `channels/utils.py` | Rework | Audit helpers; drop reminder-specific logic. |
| `channels/README.md` | Rework | Update doc once tool split decided. |

#### `src/presentation/bot` Breakdown
| Component | Status | Notes |
|-----------|--------|-------|
| `butler_bot.py` / `__main__.py` | Rework | Trim to active digest/channel flows; remove task wiring. |
| `factory.py` | Rework | Update dependency graph after modular reviewer + CLI split. |
| `handlers/channels.py` | Keep/Rework | Keep subscription management; sync localisation. |
| `handlers/menu.py` | Rework | Menu must drop task shortcuts, add digest controls. |
| `handlers/tasks.py` | Archive | Task/reminder flows no longer supported. |
| `handlers/butler_handler.py` | Rework | Ensure it routes only to supported scenarios. |
| `intent_detection/` | Keep | Needed for NLP routing; confirm ownership vs shared NLP tools. |
| `middleware/state_middleware.py` | Rework | Revisit state transitions once legacy tasks removed. |
| `metrics_server.py` | Keep/Rework | Keep Prom metrics; ensure compatibility with shared infra. |
| `states.py` | Rework | Drop task states; add digest/backoffice states if needed. |

##### CLI Backoffice Requirements (initial)
- Scope: deterministic equivalents of existing Telegram bot scenarios (subscribe/unsubscribe channel, request digest for channel over given period, list active subscriptions).
- Mode: owner-only CLI; no intent recognition, forms, or conversational flows.
- Interface: simple commands/flags (e.g., `cli channels add`, `cli digest run --channel X --hours 24`); avoid complex batch operations for now.
- Integration: may call existing MCP/API endpoints or application services; final wiring to be resolved in later stage.
- Extensibility: keep structure ready to plug in additional operations (e.g., NLP controls) once requirements emerge.

#### `src/presentation/mcp` Breakdown (non-tool modules)
| Component | Status | Notes |
|-----------|--------|-------|
| `adapters.py` | Keep/Rework | Recent DI refactor; ensure coverage for all active adapters and drop unused ones. |
| `adapters/base_adapter.py` | Keep | Shared base class; validate docstrings/type hints. |
| `adapters/complexity_adapter.py` | Rework | Confirm demand; may move to backoffice CLI. |
| `adapters/formalize_adapter.py` | Rework | Align with updated summarisation/intent flows. |
| `adapters/format_adapter.py` | Keep/Rework | Logging fix landed; needs localisation + tests. |
| `adapters/generation_adapter.py` | Rework | Depends on legacy orchestration; determine future. |
| `adapters/model_adapter.py` | Keep/Rework | Core for MCP review; sync with modular reviewer config. |
| `adapters/model_client_adapter.py` | Keep | Bridges unified client under DI. |
| `adapters/orchestration_adapter.py` | Archive | Tied to deprecated multi-agent workflow. |
| `adapters/review_adapter.py` | Keep/Rework | Use modular reviewer service; ensure metrics/logging captured. |
| `adapters/test_generation_adapter.py` | Rework | Needs doc/test updates after async fixes. |
| `adapters/token_adapter.py` | Keep | Token analysis still required. |
| `cli/interactive_mistral_chat.py` | Archive | Superseded by modular reviewer + CLI plan; keep snippets for reference only. |
| `cli/streaming_chat.py` | Archive | Same as above; move to historical docs if needed. |
| `client.py` | Keep/Rework | MCP client wrapper; verify compatibility with shared infra. |
| `config.py` | Keep | Central configuration; ensure feature flags documented. |
| `exceptions.py` | Keep | Shared exception types for MCP adapters/tools. |
| `http_client.py` | Rework | Validate usage; may collapse into unified client. |
| `http_server.py` | Keep/Rework | HTTP wrapper; align endpoints with CLI/backoffice decisions. |
| `orchestrators/mcp_mistral_wrapper.py` | Archive | Legacy Mistral-specific wrapper; remove once modular reviewer fully adopted. |
| `prompts/` | Rework | Rationalise prompts post-modular reviewer. |
| `resources/` | Keep/Rework | Ensure only active templates remain; convert to importlib resources. |
| `schemas.py` | Keep | Interfaces for MCP requests/responses. |
| `server.py` | Keep/Rework | Main entrypoint; align tool registration with final catalogue. |
| `tools_registry.py` | Rework | Update registry once tool statuses (keep/archive) are finalised. |

#### `src/workers` Breakdown
| Component | Status | Notes |
|-----------|--------|-------|
| `summary_worker.py` | Keep/Rework | Keep daily summaries; ensure logging extras fixed. |
| `cache_refresh_worker.py` | Rework | Validate necessity once reminders removed. |
| `post_fetcher_worker*.py` | Keep/Rework | Needed for channel harvest; align with Mongo auth. |
| `message_sender.py` | Archive | Dependent on reminder flows; confirm before removal. |
| `formatters.py` | Rework | Logging already adjusted; continue cleanup. |
| `data_fetchers.py` | Rework | Audit dependencies; ensure modular reviewer not required. |
| `schedulers.py` | Rework | Drop reminder cron triggers; keep digest schedules. |
| `finetuning_worker.py` | Evaluate | Determine if still used; otherwise archive. |
| `unified_task_worker_main.py` / `base_worker.py` | Keep/Rework | Central runner; needs doc + DI alignment. |

#### `docs/` Breakdown (non-specs)
| Document/Folder | Status | Notes |
|-----------------|--------|-------|
| `specs/` | Keep | Canonical source; continue iterating. |
| `archive/` | Keep | Historical artefacts; ensure new archives stored here. |
| `USER_GUIDE.md`, `DEVELOPMENT.md`, `OPERATIONS.md`, `TROUBLESHOOTING.md`, `PERFORMANCE_BENCHMARKS.md` | Keep/Rework | Core guides; update as new architecture lands. |
| `API_MCP_TOOLS.md`, `API_DOCUMENTATION.md`, `API.md` | Rework → consolidate | Merge into a single up-to-date API reference. |
| `AGENT_INTEGRATION.md` (+ `.ru`), `TECHNICAL_DESIGN.ru.md` | Archive | Superseded by modular reviewer docs; retain in archive if needed. |
| `ARCHITECTURE.md`, `ARCHITECTURE_FSM.md`, `review_system_architecture.md` | Rework | Align with new architecture spec, avoid duplication. |
| `MCP_*` guides (`MCP_GUIDE.md`, `MCP_DEMO_GUIDE.md`, `MCP_HOMEWORK_REVIEW.md`, `MCP_TOOL_USAGE.md`) | Rework | Update to reflect new tool catalogue and archived flows. |
| `MODEL_SETUP.md`, `start_models` references | Archive | Local models deprecated; keep instructions only under archive. |
| `MODULAR_REVIEWER_INTEGRATION_GUIDE.md` | Keep | Reference for downstream consumers. |
| `shared_infra_cutover.md`, `ML_MONITORING.md`, `MONITORING.md` | Rework | Consolidate under operations/observability. |
| `mongo_inventory_before.json`, `mongodb-warnings.md` | Archive | Historical snapshots. |
| `release_notes/`, `PHASE_1_IMPLEMENTATION.md`, `PHASE_1_*` | Archive | Historical execution records. |
| `CHANNEL_*`, `COMPONENT_DETECTION_STRATEGY.md`, `CONTEXT_COMPRESSION_STRATEGY.md` | Rework | Validate against current bot/backoffice roadmap. |
| `guides/`, `api/`, `operations/architecture` subfolders | Rework | Curate contents, remove outdated translations. |

#### `scripts/` Breakdown
| Script/Folder | Status | Notes |
|---------------|--------|-------|
| `test_review_system.py`, `check_model_status.sh`, `start_models.sh`, `wait_for_model.sh` | Rework/Archive | Update to use modular reviewer & shared infra; remove local model steps where obsolete. |
| `quality/` suite (`check_coverage.py`, `run_all_checks.sh`, etc.) | Keep/Rework | Keep automation; ensure targets match new lint/test baseline. |
| `qa/` smoke scripts | Keep/Rework | Align with current infra endpoints and feature flags. |
| `maintenance/` (backup/cleanup/export) | Keep | Useful for ops; document prerequisites. |
| `security/docker_scan.sh` | Keep | Retain security scanning hook. |
| `ci/test_day10.sh`, `diag_*`, `day12_run.py` | Archive | Legacy workflows tied to older days. |
| `mcp_comprehensive_demo.py`, `healthcheck_mcp.py` | Rework | Update to new tool set; drop reference to deprecated flows. |
| `clear_channels.py`, `export_channel_posts.py` | Keep/Rework | Needed for digest pipeline; move to backoffice tooling eventually. |
| `telegram_channel_reader.session` | Archive | Remove committed session file after confirming not needed. |

#### `prompts/` Breakdown
| Asset | Status | Notes |
|-------|--------|-------|
| `prompts/v1/pass_*` | Rework | Ensure they align with modular passes (may migrate into package resources). |
| `prompt_registry.yaml` | Rework | Update registry to match current prompt usage; avoid unused entries. |
| `__init__.py` | Keep | Provide packaging hooks; convert to importlib resources. |

#### `examples/` Breakdown
| Asset | Status | Notes |
|-------|--------|-------|
| `basic_usage.py`, `full_workflow.py` | Rework | Update to modular reviewer APIs and shared infra settings. |
| `mcp/basic_discovery.py` | Rework | Reflect trimmed MCP tool set. |
| `README.md` | Rework | Provide quickstart aligned with Day 15+ architecture. |

#### `contracts/` Breakdown
| Asset | Status | Notes |
|-------|--------|-------|
| `review_api_v1.yaml`, `hw_check_payload_schema.json` | Keep/Rework | Validate contracts against modular reviewer outputs. |
| `examples/` (curl/python) | Rework | Update payloads/endpoints. |
| `INTEGRATION_GUIDE.md`, `log_archive_format.md` | Rework | Align with new archive service and modular reporter. |
| `README.md` | Rework | Document current API surface. |

#### `tasks/` Breakdown
| Folder | Status | Notes |
|--------|--------|-------|
| `day_01` – `day_10` | Archive | Historical backlog; keep for reference. |
| `day_11` – `day_17` | Keep | Canonical specs; ensure summaries linked from `docs/specs`. |
| `day_12/improvements/` and other subfolders | Archive/Curate | Move relevant insights to specs, archive raw brainstorming. |
| `day_16`, `day_17` outstanding docs | Rework | Classify and migrate key requirements into specs. |

### `shared/` Inventory
| Component | Description | Status | Notes |
|-----------|-------------|--------|-------|
| `shared/shared_package/agents` | Shared agents (code generator/reviewer) | Rework | Validate relevance after modular reviewer adoption. |
| `shared/shared_package/clients` | Unified/base client with retry/backoff | Keep | Consumed by application and MCP layers. |
| `shared/shared_package/config` | Model/agent configuration | Rework | Align with main project settings. |
| `shared/shared_package/orchestration` | Sequential/parallel orchestrators | Rework | Define strategy alongside multi-agent refactor. |
| `shared/tests` | SDK automated tests | Keep | Maintain as part of reusable package. |
| `shared/validation` | Pydantic models | Keep | Used for API validation. |
| Packaging (`pyproject`, README`) | Package metadata/docs | Rework | Bring up to publishable quality. |

#### `shared/shared_package` Breakdown
| Submodule | Status | Notes |
|-----------|--------|-------|
| `agents/base_agent.py` | Archive | Superseded by modular reviewer abstractions. |
| `agents/code_generator.py` | Keep/Rework | Align with future generator refactor. |
| `agents/code_reviewer.py` | Archive | Reviewer replaced; mark for removal with orchestrators. |
| `agents/schemas.py` | Rework | Keep only shared message formats still in use. |
| `clients/base_client.py` | Keep | Recently updated with retries; shared dependency. |
| `clients/unified_client.py` | Keep | Core HTTP client; ensure OpenAI-compatible path documented. |
| `config/agents.py` | Rework | Update to reflect deprecated reviewer. |
| `config/models.py` | Keep/Rework | Sync with main settings (model aliases). |
| `config/api_keys.py` | Archive | Remove if secrets handled via env only. |
| `config/constants.py` | Rework | Validate constants still referenced. |
| `exceptions/model_errors.py` | Keep | Used across clients. |
| `orchestration/*` | Archive | Sequential/parallel orchestrators tied to legacy agents. |
| `utils/` | Keep | Placeholder for shared helpers (currently empty). |
| `validation/models.py` | Keep | Active request/response validation. |

### `packages/` Inventory
| Package | Description | Status | Notes |
|---------|-------------|--------|-------|
| `multipass-reviewer` | Reusable modular reviewer | Keep | Primary package; continue evolving. |
| `multipass-reviewer/examples` | Usage examples | Rework | Sync with current API surface. |
| `multipass-reviewer/tests` | Unit/integration tests | Keep | Maintain ≥90% coverage. |

#### `multipass-reviewer` Package Breakdown
| Module | Status | Notes |
|--------|--------|-------|
| `application/config.py` | Keep | Fluent config builder and presets; maintain strict typing. |
| `application/orchestrator.py` | Keep | Core orchestrator; ensure DI remains pure and metrics instrumented. |
| `domain/interfaces/*` | Keep | Contracts for archive reader, LLM client, review logger. |
| `domain/models/` | Keep/Rework | Confirm models stay minimal; document partial report semantics. |
| `domain/passes/` | Keep | Architecture/component/synthesis passes with metrics. |
| `domain/services/diff_analyzer.py` | Keep/Rework | Evaluate opportunities to share with main app. |
| `domain/value_objects/` | Keep | Provide typed containers for review artefacts. |
| `infrastructure/checkers/` | Keep | Maintain coverage and Prometheus metrics. |
| `infrastructure/adapters/` | Keep (scaffolding) | Reserve namespace for future integrations. |
| `infrastructure/loaders/` | Keep (scaffolding) | Placeholder for resource loaders; populate in future releases. |
| `infrastructure/monitoring/metrics.py` | Keep | Prometheus instrumentation. |
| `presentation/` | Keep (scaffolding) | Namespace for potential CLI/API wrappers. |
| `prompts/` | Rework | Consolidate prompts/resources, ensure packaging via importlib. |
| `tests/` | Keep | Unit/integration suite – maintain ≥90% coverage. |
| `CHANGELOG.md`, `VERSIONING.md` | Keep | Continue documenting releases. |

### Documentation Cross-Reference
| Day Spec | Key Topics | Status |
|----------|------------|--------|
| Day 11 | Shared infra integration, MCP API | Canonical |
| Day 12 | Deployment, quick start, testing | Canonical |
| Day 15 | Modular reviewer rollout, migrations | Canonical |
| Day 17 | Integration contracts, README | Canonical |
| Day 11–17 Summary | `docs/specs/day11-17_summary.md` | New summary |
| Day 18+ | Performance benchmarks, ops notes | To align |
| Legacy docs (pre-Day 11) | Historical materials | Archive |

### Known Failing Test Suites (latest run)
- `src/tests/infrastructure/test_summarizer.py` – localisation mismatch (RU vs EN messages).
- `src/tests/presentation/bot/test_natural_language_flow.py` – `ButlerBot` constructor now requires an orchestrator.
- MCP suites (`src/tests/presentation/mcp/test_adapters.py`, `test_digest_tools.py`, `test_pdf_digest_tools.py`, `test_performance.py`) – blocked by Mongo auth, logging kwargs, heavyweight dependencies.
- `src/tests/presentation/mcp/test_pdf_digest_tools.py` – needs Mongo auth and WeasyPrint stubs.
- `src/tests/presentation/mcp/test_performance.py` – latency thresholds exceeded in current environment.
- `src/tests/workers/test_summary_worker.py` – fixed after StructuredLogger update (now passing).

### External Dependencies
- MongoDB (`shared-mongo:27017`, auth required).
- Prometheus (`http://127.0.0.1:9090`, readiness/metrics).
- LLM API (`http://127.0.0.1:8000`, OpenAI-compatible).
- Grafana (`http://127.0.0.1:3000`), Kafka, Redis – part of shared infra.
- Telegram API (Pyrogram) – `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, session string.
- WeasyPrint/Pydyf – used by PDF digest (marked for deprecation but still present).
