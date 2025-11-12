<!-- 86473cf7-3a7d-44c3-8ebe-ddcffc5e019a be1e1d7f-eef0-4881-99f4-d329ab93b64a -->
# Phase 5 Plan — Testing, Polish, and Deployment

## Scope

- End-to-end testing for complete user flows (NL task creation → list → complete)
- Error handling and resilience improvements
- Documentation (README, user guide, API docs)
- Docker Compose for all services (mongodb, mcp-server, bot, worker)
- Production readiness checks and monitoring improvements

## Architecture Decisions (chief-architect)

- E2E tests should cover happy paths and error scenarios
- Error handling should be graceful with user-friendly messages
- Documentation should be production-ready with examples
- Docker setup should support local development and production-like testing

## Files to Add/Change

- Add: `src/tests/e2e/test_bot_flows.py`
- Test complete flows: NL task → clarification → list → complete → delete
- Add: `src/tests/e2e/test_scheduled_notifications.py`
- Test worker notifications with mocked time and Telegram
- Change: `src/presentation/bot/butler_bot.py`
- Improve error handling with try/except blocks and user-friendly messages
- Refactor `handle_natural_language` if >15 lines (per ai-reviewer: function size)
- Integrate structured logger from `src/infrastructure/monitoring/logger.py`
- Change: `src/workers/summary_worker.py`
- Add retry logic with exponential backoff (3 attempts)
- Integrate structured logger instead of basic logging
- Add graceful shutdown handler (SIGTERM/SIGINT)
- Change: `src/presentation/bot/handlers/tasks.py` and `channels.py`
- Wrap handlers with try/except; use structured logging
- Refactor functions >15 lines if needed
- Change: `src/presentation/mcp/tools/reminder_tools.py` and `digest_tools.py`
- Add input validation and clear error dictionaries
- Use structured logging for tool calls
- Add: `Dockerfile.bot`
- Follow docker-reviewer: python-slim, non-root user, healthcheck, no secrets
- Minimal dependencies, multi-stage if needed
- Add: `Dockerfile.worker`
- Same docker-reviewer rules as bot
- Change: `docker-compose.day11.yml` (enhance)
- Add `telegram-bot` and `summary-worker` services
- Resource limits, healthchecks, proper dependencies
- Environment variable documentation in comments
- Add: `tasks/day_11/README.md`
- User guide with examples, setup instructions, troubleshooting (technical-writer)
- Command reference, architecture overview
- Add: `docs/day11/api.md`
- MCP tools API documentation with request/response examples (technical-writer)
- Update: Root `README.md`
- Add Day 11 section with overview and quick start

## Error Handling (python-zen-writer)

- All bot handlers wrapped with try/except; log errors; show friendly messages
- MCP tools validate inputs and return clear error dictionaries
- Worker retries failed sends up to 3 times with exponential backoff
- No silent failures; all exceptions logged with context

## Testing Strategy (TDD - qa-tdd-reviewer)

- Write tests FIRST before implementation fixes (red-green-refactor cycle)
- Test organization:
  - `src/tests/e2e/test_bot_flows.py` - Complete user journeys with proper fixtures
  - `src/tests/e2e/test_scheduled_notifications.py` - Worker scheduling with freezegun
  - `src/tests/e2e/conftest.py` - Shared fixtures (MongoDB, MCP mocks, bot mocks)
- Test fixtures and patterns:
  - Use pytest fixtures with proper scopes (function/module/session)
  - Database cleanup in autouse fixtures (before/after each test)
  - Mock external services (Telegram API, MCP HTTP calls)
  - Factory functions for creating test tasks/channels
- Test categories (use pytest markers):
  - `@pytest.mark.e2e` for end-to-end flows
  - `@pytest.mark.integration` for service integration
  - `@pytest.mark.slow` for tests that take >1 second
- Test isolation:
  - Each test must be independent (no shared state)
  - Use unique user_ids per test to avoid conflicts
  - Clean up database state after each test
- Error scenario coverage (write tests for each):
  - Network failures (ConnectionError, TimeoutError)
  - Invalid inputs (missing fields, wrong types, empty strings, max length exceeded)
  - Missing data (task not found, channel not found, empty lists)
  - Rate limiting (Telegram API limits simulated)
  - Database connection failures
- Edge cases:
  - Empty task lists, max limits (500 tasks, 100 channels)
  - Concurrent operations (race conditions if applicable)
  - Unicode/emoji in task titles
  - Very long text inputs (>4096 chars for Telegram)
- Mock strategies:
  - Mock Telegram Bot API calls (send_message failures, rate limits)
  - Mock MCP HTTP client responses (success/failure scenarios)
  - Use freezegun for time-dependent tests (scheduled notifications)
- Assertions:
  - Use descriptive assert messages
  - Test both positive and negative cases
  - Verify side effects (database state, log entries)
  - Follow AAA pattern (Arrange-Act-Assert)
- Coverage requirements:
  - ≥85% overall for Day 11 code
  - ≥90% for critical paths (bot handlers, worker, MCP tools)
  - Use `pytest-cov` with `--cov-report=term-missing` to identify gaps
- Test performance:
  - Mark slow tests with `@pytest.mark.slow`
  - Keep test execution time reasonable (<5 min total)
  - Use pytest-xdist for parallel execution if available

## Documentation

- User guide: setup, commands, examples, troubleshooting
- API docs: MCP tools reference with request/response examples
- README updates: overview, architecture, quick start
- Code comments: docstrings reviewed for completeness

## Docker & Deployment

- docker-compose.day11.yml includes all 4 services:
- mongodb, mcp-server, telegram-bot, summary-worker
- Services use same network; proper dependencies and healthchecks
- Environment variable documentation in compose file comments

## Monitoring & Production Readiness

- Structured logging across all services
- Health check endpoints for bot and worker (if feasible)
- Graceful shutdown handling in worker
- Resource limits in Docker compose

## Final Deliverables (save under tasks/day_11)

- Plan: `tasks/day_11/day_11-phase-05.plan.cursor.md`
- Summary: `tasks/day_11/day_11-phase-05-summary.md`

## To-dos

- [ ] Write E2E tests for bot flows (NL task creation → completion)
- [ ] Write E2E tests for scheduled notifications (worker)
- [ ] Improve error handling in bot handlers
- [ ] Add retry logic to summary worker
- [ ] Enhance MCP tools with validation and clear errors
- [ ] Update docker-compose.day11.yml (add bot + worker services)
- [ ] Create user guide (tasks/day_11/README.md)
- [ ] Create API documentation (docs/day11/api.md)
- [ ] Update root README with Day 11 section
- [ ] Review and improve docstrings
- [ ] Add structured logging configuration
- [ ] Produce Phase 5 summary file

### To-dos

- [ ] Write E2E tests for bot flows (NL task creation → completion)
- [ ] Write E2E tests for scheduled notifications (worker)
- [ ] Improve error handling in bot handlers
- [ ] Add retry logic to summary worker
- [ ] Enhance MCP tools with validation and clear errors
- [ ] Update docker-compose.day11.yml (add bot + worker services)
- [ ] Create user guide (tasks/day_11/README.md)
- [ ] Create API documentation (docs/day11/api.md)
- [ ] Update root README with Day 11 section
- [ ] Review and improve docstrings
- [ ] Add structured logging configuration
- [ ] Produce tasks/day_11/day_11-phase-05-summary.md
