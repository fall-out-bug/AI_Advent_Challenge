# Stage 00_02 · Decision Log & Scope Definition

## Goal
Translate the inventory into actionable decisions. This stage finalises what is
kept in the active codebase, what is migrated to `archive/`, and what requires
redesign in future epics.

## Decisions To Record
- Component classification (Keep / Archive / Rework) with rationale.
- Feature ownership (e.g., Modular Reviewer, MCP Bot, Telegram flows).
- Test strategy for short term (critical suites mandatory, others scheduled for
  revival).
- Observability baseline (metrics, logging, tracing) aligned with shared infra.

## Outputs
- Decision table appended below (TBD once audit concludes).
- Tickets/epics raised for each Rework cluster (EP01+).
- Risk register: outstanding blockers, technical debt, resource needs.

## Decisions to Date
- **Telegram Bot Scope:** Reminder/task flows move to archive; subscription and
  digest scenarios stay active. Single-user operation (owner) allows a
  self-service UI.
- **Homework Review MCP:** Current tool is deprecated; a replacement will ship
  after the checker API refactor.
- **Test Baseline:** CI must keep non-legacy test suites green; legacy suites may
  remain skipped until future epics refactor them.
- **MCP Tooling:** Homework review and PDF digest are marked for deprecation;
  reminder tools move to archive; digest/channel management stays (bulk actions
  migrate to backoffice). NLP utilities stay active.
- **Localization:** Primary user-facing language is Russian; user-facing copy and
  tests follow RU localisation. Core documentation remains bilingual (EN + RU).
- **Baseline Confirmation:** Final list of mandatory tests will be confirmed
  after Stage 00_01 audit wraps.
- **Canonical Specs:** Day 11 onward act as the canonical timeline; hypotheses
  and validations tie back to those sprints.
- **Auxiliary Catalogues:** Keep `tasks/` for history; `examples/` and
  `contracts/` may be reworked or archived.
- **Orchestrators:** Legacy orchestrators/agents undergo refactor; multi-agent
  scenarios are deprioritised unless revived explicitly.
- **Bot Backoffice:** Deliver a CLI interface for backoffice features (channel
  management, digest controls).
- **Shared & Packages:** Raise quality to reusable standard (structure, docs,
  publishability).

## Decision Table (initial draft)
| Area | Decision | Status | Follow-up / Owner | Target Epic |
|------|----------|--------|-------------------|-------------|
| MCP Tools | Deprecate homework review & PDF digest; archive reminders; keep digest/channel/NLP with refactor | Approved (Stage 00_01) | Assistant: draft refactor plan & tickets; User: approve scope | EP02 |
| Modular Reviewer | Keep modular reviewer as canonical implementation; legacy agents archived | Approved | Assistant: maintain wiring & metrics; User: monitor rollout | EP01 |
| Multi-agent Workflow | Archive legacy multi-agent orchestrator and reviewer agent; keep generator for future refactor | Approved | Assistant: create cleanup tasks; User: confirm generator roadmap | EP02 / EP04 |
| Localization & Docs | RU for user-facing copy/tests; maintain bilingual (EN/RU) documentation | Approved | Assistant: consolidate docs; User: review translations | EP03 |
| CLI Backoffice | Provide owner-only deterministic CLI for channel/digest operations | Approved | Assistant: design CLI command set; User: validate command coverage | EP02 |
| Documentation Inventory | Consolidate API docs, archive legacy guides, maintain specs as source of truth | Approved | Assistant: execute migration; User: sign off structure | EP03 |
| Shared SDK | Retain clients/validation; archive obsolete agents/orchestrators; keep scaffolding | Approved | Assistant: refactor modules; User: approve releases | EP01 / EP04 |
| Scripts & Prompts | Update operational scripts to shared infra, retire legacy Day10/12 flows; align prompts with modular passes | Approved | Assistant: update automation/prompts; User: verify coverage | EP03 / EP04 |
| Testing Baseline | Enforce non-legacy tests in CI; legacy suites scheduled for later refactor | Approved | Assistant: update CI pipelines; User: review MR | EP01 |

## Spec Alignment Plan (Day 11+)
| Day | Canon Source | Alignment Status | Planned Action | Owner |
|-----|--------------|------------------|----------------|-------|
| Day 11 | `docs/specs/day11-17_summary.md` | Completed | Keep summary as canonical reference | Assistant & User (monitor) |
| Day 12 | `tasks/day_12/` notes & quick-start docs | Completed (Day12 quick start captured) | Deployment quick start merged into Operations guide; archive follow-up pending | Assistant (done), User (review) |
| Day 15 | `release_notes/day_15.md`, `tasks/day_15/` | Completed (summarisation/fine-tuning captured) | Specs updated with summarisation + self-improving pipeline; monitor metrics backlog | Assistant (done), User (review) |
| Day 17 | `tasks/day_17/` MLOps guides | Completed (log analysis pass recorded) | Architecture/specs document Pass 4 + MLOps integration; archive cleanup remains | Assistant (done), User (review) |
| Day 18 | `docs/reference/en/PERFORMANCE_BENCHMARKS.md` | In progress | Ensure benchmarks reflect modular reviewer (latest run 2025-11-08) | Assistant |
| Post-Day 18 | Future specs | TBA | Create rolling checklist for new sprints | User |

## Documentation Consolidation Plan
| Doc Pair (EN/RU) | Scope | Current Sources | Target Actions | Owner |
|------------------|-------|-----------------|----------------|-------|
| `API_REVIEWER.md` / `.ru.md` | Modular reviewer service & MCP integration | `API.md`, `review_system_architecture.md`, `MODULAR_REVIEWER_INTEGRATION_GUIDE.md` | Merge into single bilingual reference; include request/response schemas & examples | Assistant (draft ✅), User (review) |
| `API_MCP.md` / `.ru.md` | MCP tool catalogue (digest/channel/NLP) | `API_MCP_TOOLS.md`, Stage 00_01 MCP table | Strip reminders/homework sections, document retained tools with CLI equivalents | Assistant (draft ✅), User (review) |
| `API_BOT_BACKOFFICE.md` / `.ru.md` | CLI commands & Telegram mapping | Stage 00_01 CLI requirements | Define command syntax + operator guide; align with digest/channel flows | Assistant (draft ✅), User (review) |
| `DOCS_OVERVIEW.md` / `.ru.md` | Documentation index & navigation | `INDEX.md`, `USER_GUIDE.md`, `guides/` | Provide canonical structure pointing to bilingual pairs and specs | Assistant (draft ✅), User (review ✅) |

## CLI Backoffice Command Set (draft)
| Command | Description | Inputs | Output/Notes | Dependencies |
|---------|-------------|--------|---------------|--------------|
| `channels:list` | List active channel subscriptions with tags/status | `--limit`, `--include-tags` | Table/JSON list of channels | Mongo (subscriptions collection) |
| `channels:add` | Subscribe to a new channel | `--username`, `--tags` | Confirmation with channel ID | Uses channel metadata resolver |
| `channels:remove` | Unsubscribe from channel | `--channel-id` or `--username` | Status (`removed`/`not_found`) | Mongo + Telegram API check |
| `channels:refresh` | Trigger immediate fetch for a channel | `--channel-id` or `--username`, optional `--hours` | Job enqueued/log entry | Worker queue (`post_fetcher`) |
| `digest:run` | Generate digest for channel(s) over period | `--channel`, `--hours` or `--range` | Markdown/JSON digest output | Modular reviewer summariser + Mongo |
| `digest:last` | Show last generated digest metadata | `--channel` | Timestamp, post count, summary snippet | Mongo (digests collection) |
| `digest:export` | Export digest to PDF/Markdown | `--user-id`, `--channel`, `--hours`, `--output`, `--format` | Generates file via backoffice CLI; uses shared infra + WeasyPrint | CLI backoffice |
| `nlp:test` | (Optional) Run intent detection on sample text | `--text` | Parsed intent structure | Shared NLP utilities |

### CLI Wiring Plan

| Command | Primary Adapter/Service | Notes |
|---------|-------------------------|-------|
| `channels list` | `channels_list` MCP tool (`src/presentation/mcp/tools/channels/channel_management.py`) | Invoke via `MCPClient.call_tool`, format response table. |
| `channels add` | `channels_add` MCP tool | Validate username via `channel_metadata`, reuse existing error codes. |
| `channels remove` | `channels_remove` MCP tool | Allow channel ID lookup via Mongo repository helper. |
| `channels refresh` | Worker enqueue (`post_fetcher_queue.enqueue_refresh`) | CLI issues task directly through application service (no MCP). |
| `digest run` | `digest_generate` MCP tool | Support `--format` option by switching rendering template. |
| `digest last` | `digest_get_last` MCP tool | Provide fallback message when digest missing. |
| `digest export` | `digest_exporter.export_digest_to_file` | Uses CLI service with shared infra + WeasyPrint; outputs PDF/Markdown. |
| `nlp test` | `nlp_parse_intent` MCP tool | Optional; wraps intent orchestrator via MCP. |

Implementation skeleton to live in `src/presentation/cli/backoffice/commands.py`, sharing auth/config with existing CLI utilities.

## Risk Register (initial)
| Risk | Impact | Mitigation | Owner | Status |
|------|--------|------------|-------|--------|
| Legacy MCP tests require Mongo/Telegram credentials causing instability | High | Introduce mocks, skip until infra ready | Assistant (implementation); User (infra access) | Open (likelihood: high) |
| PDF digest tooling depends on heavy libs (WeasyPrint) | Medium | Deprecate module, replace with CLI-based exports | Assistant | In progress |
| Documentation divergence between EN/RU versions | Medium | Establish publishing workflow; automate sync where possible | Assistant (process); User (review) | Open (likelihood: medium) |
| Local model scripts still referenced in docs/scripts | Medium | Update guides/scripts to shared infra only | Assistant | In progress (likelihood: medium) |
| Modular reviewer scaffolding (adapters/loaders) unused | Low | Track in EP01 backlog, keep placeholders | Assistant & User | Accepted |

### Test Baseline Proposal

| Suite | Command | Rationale | Status |
|-------|---------|-----------|--------|
| Modular reviewer unit/integration | `poetry run pytest packages/multipass-reviewer -q` | Must stay green (strict coverage ≥90%) | Mandatory |
| Shared SDK unit tests | `poetry run pytest shared/tests -q` | Validates unified client retries and validation | Mandatory |
| Application/unit core | `poetry run pytest src/tests/unit -q` | Covers non-legacy logic (modular reviewer, MCP adapters) | Mandatory |
| Shared infra integration | `poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py -q` | Ensures Mongo/LLM/Prom endpoints reachable | Mandatory |
| Review pipeline integration | `poetry run pytest tests/integration/test_modular_review_service.py -q` | Guards integration wiring | Mandatory |
| Legacy MCP suites | Various (`tests/presentation/mcp/*`) | Currently flaky due to credentials/logging; skip until refactor | Excluded (tracked for EP02) |
| PDF digest tests | `tests/presentation/mcp/test_pdf_digest_tools.py` | Relies on WeasyPrint; mark xfail until CLI backoffice replaces functionality | Excluded (pending replacement) |
| Bot E2E telemetry | `tests/e2e/telegram/*` | Requires Telegram creds; run manually on demand | Optional |

Document final baseline in CI config once agreed.

## Status
*Deliverables complete — ready for epic closure.*

## Next Actions
- Monitor Day 18 requirements (separate epic).
- Execute remaining follow-up work within respective epics (EP01–EP04).
- Close Epic 00 upon stakeholder sign-off.
