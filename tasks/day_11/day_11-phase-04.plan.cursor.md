<!-- 86473cf7-3a7d-44c3-8ebe-ddcffc5e019a 2af0b555-37be-4c5f-8633-7c9495881bcd -->
# Phase 4 Plan — Channel Digests, Schedules, and Monitoring

## Scope
- Channel digest MCP tools and Telegram delivery (evening)
- Scheduled workers: morning summary (9:00), evening digest (20:00), quiet hours respected
- Complete channels UI (subscribe/list/unsubscribe) wired to MCP
- Monitoring/health endpoints and basic logging/metrics
- End-to-end tests for digests and schedules (mock time/LLM/Telegram)

## Architecture Decisions (chief-architect)
- Keep digest logic in MCP layer: `src/presentation/mcp/tools/digest_tools.py`
  - Fetch posts via `telegram_utils` client; summarize via LLM adapter
- Background worker: `src/workers/summary_worker.py` (async loop) with schedule helper
  - Reads `default_timezone` from settings; respects quiet hours
- Bot remains thin: triggers and display only; business logic lives in MCP/worker
- Config-driven schedule/quiet hours in `settings.py`

## Files to Add/Change
- Add: `src/infrastructure/clients/telegram_utils.py`
  - `fetch_channel_posts(channel_username: str, since: datetime) -> list[dict]`
- Add: `src/infrastructure/llm/summarizer.py`
  - `summarize_posts(posts: list[dict], max_sentences: int) -> str`
- Add: `src/presentation/mcp/tools/digest_tools.py`
  - Tools: `add_channel`, `list_channels`, `delete_channel`, `get_channel_digest`
- Change: `src/presentation/bot/handlers/channels.py`
  - Wire to MCP tools (subscribe/list/unsubscribe); basic pagination
- Add: `src/workers/schedulers.py`
  - Helper functions for “is_time_to_send”, “is_quiet_hours”, tz-aware comparisons
- Change: `src/workers/summary_worker.py`
  - Use helpers; call MCP `get_summary`/`get_channel_digest`; robust error handling
- Change: `src/infrastructure/config/settings.py`
  - `morning_summary_time`, `evening_digest_time`, `quiet_hours_start`, `quiet_hours_end`
- Add: `scripts/cron/README.md` (optional local cron alternative usage)
- Docker: ensure worker service in compose uses same env and network

## ML Engineering (ml-engineer)
- Summarizer uses LLMClient; limit tokens and temperature (configurable)
- Deterministic summarization prompt with JSON-free text output
- Retry summarization up to 2 times; fallback to bullet list on failure

## Testing Strategy (TDD)
- Unit tests:
  - `src/tests/infrastructure/test_telegram_utils.py` (mock HTTP)
  - `src/tests/infrastructure/test_summarizer.py` (mock LLM)
  - `src/tests/workers/test_schedulers.py` (quiet hours, boundary times)
- Integration tests:
  - `src/tests/presentation/mcp/test_digest_tools.py` (mock fetch + summarizer)
  - `src/tests/workers/test_summary_worker.py` (fake clock; verify sends)
- Coverage ≥80% for new code

## Monitoring & Ops
- Health endpoints already present for MCP HTTP wrapper; add worker heartbeat log
- Structured logs with level and component, minimal PII

## Config & Env
- Add env vars for schedule times and quiet hours; defaults:
  - morning 09:00, evening 20:00, quiet 22→08
- Respect `default_timezone`

## Final Deliverables (save under tasks/day_11)
- Plan: `tasks/day_11/day_11-phase-04.plan.cursor.md`
- Summary: `tasks/day_11/day_11-phase-04-summary.md`

## To-dos
- [ ] Implement Telegram fetch client (mockable)
- [ ] Implement LLM summarizer adapter
- [ ] Implement MCP digest tools (subscribe/list/delete/digest)
- [ ] Wire channels UI to MCP tools
- [ ] Add schedule/quiet hours helpers
- [ ] Update summary worker to use helpers and digest
- [ ] Extend settings with schedule and quiet hours
- [ ] Write unit tests (utils, summarizer, schedulers)
- [ ] Write integration tests (digest tools, worker)
- [ ] Produce Phase 4 summary file

### To-dos

- [ ] Implement Telegram fetch client (mockable)
- [ ] Implement LLM summarizer adapter
- [ ] Implement MCP digest tools (subscribe/list/delete/digest)
- [ ] Wire channels UI to MCP tools
- [ ] Add schedule and quiet-hours helpers
- [ ] Update summary worker to send digest using helpers
- [ ] Extend settings with schedule and quiet hours
- [ ] Write unit tests for utils, summarizer, schedulers
- [ ] Write integration tests for digest tools and worker
- [ ] Produce tasks/day_11/day_11-phase-04-summary.md