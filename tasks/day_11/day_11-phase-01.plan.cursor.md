<!-- 86473cf7-3a7d-44c3-8ebe-ddcffc5e019a 54611f32-82b2-4f64-859a-995d83463297 -->
# Phase 1 Plan — Core Infrastructure

## Scope

- MongoDB schemas and async repositories (Motor)
- MCP reminder tools: add_task, list_tasks, update_task, delete_task, get_summary
- Minimal aiogram bot skeleton (start/help + health)
- Docker Compose services for MongoDB and MCP HTTP server
- TDD: pytest-asyncio unit/integration tests, ≥80% coverage for new code

## Architecture Decisions

- Use Motor (async) with a singleton client and per-collection accessors
- Define Pydantic models for `Task` and validation in `src/domain/entities`
- Keep MCP tools in `src/presentation/mcp/tools/` importing the shared `mcp` instance from `src/presentation/mcp/server.py` to avoid multiple MCP instances
- Configuration via env vars with sensible defaults; centralized in `src/infrastructure/config/settings.py`

## Files to Add/Change

- Add: `src/infrastructure/database/mongo.py`
- Create global Motor client, `get_db()`, graceful shutdown hooks
- Add: `src/infrastructure/repositories/task_repository.py`
- CRUD methods with strong typing; date handling in ISO 8601
- Add: `src/domain/entities/task.py`
- Pydantic model `TaskIn`, `Task`, `TaskUpdate` with validation (priority enum, deadline ISO optional)
- Add: `src/presentation/mcp/tools/reminder_tools.py`
- Implement `add_task`, `list_tasks`, `update_task`, `delete_task`, `get_summary` with repository
- Change: `src/presentation/mcp/server.py`
- Import `src/presentation/mcp/tools/reminder_tools` so tools register on the shared `mcp`
- Add: `src/presentation/bot/butler_bot.py`
- Minimal aiogram 3.x `ButlerBot` with `/start`, `/help`, `.run()`
- Add: `docker-compose.day11.yml`
- Services: `mongodb`, `mcp-server` (HTTP on 8004); persistent volume and healthchecks
- Add: `src/tests/infrastructure/test_task_repository.py` (async)
- Add: `src/tests/presentation/mcp/test_reminder_tools.py` (async)
- Add: `src/infrastructure/config/settings.py`
- Read `MONGODB_URL`, `DB_NAME`, timeouts; defaults for local dev
- Final artifact: `reports/day11-phase1-summary.md`
- Single file summarizing Phase 1: scope, decisions, commands to run, test coverage, and next steps.

## Testing Strategy (TDD)

- Repository tests using a test database (suffix `_test`), clean fixtures
- MCP tool tests call functions directly (bypassing HTTP), asserting validation and DB effects
- Use `pytest-asyncio` and `freezegun` for deterministic time in `get_summary`

## Docker

- `mongodb` with volume, healthcheck
- `mcp-server` built from existing `Dockerfile.mcp`, exposing 8004, depends_on mongo (for tests of tools via repo when run in container)

## Config & Env

- Env vars: `MONGODB_URL` (default `mongodb://localhost:27017`), `DB_NAME` (default `butler`)
- Ensure graceful client close on pytest session end

## Final Deliverable

- Exactly one summary file at `reports/day11-phase1-summary.md` containing:
- Phase 1 completed items checklist
- How to run (docker-compose, env vars)
- Test results (coverage ≥80%)
- Known limitations and Phase 2 pointers

## Non-Goals in Phase 1

- Full bot handlers, summaries scheduling, channel digests (Phase 3-4)

### To-dos

- [ ] Create centralized settings for Mongo env vars in settings.py
- [ ] Implement Motor client and get_db() in database/mongo.py
- [ ] Add Pydantic Task models with validation
- [ ] Implement TaskRepository CRUD and queries
- [ ] Add reminder MCP tools and register with server
- [ ] Scaffold minimal aiogram ButlerBot with start/help
- [ ] Write async tests for TaskRepository (TDD)
- [ ] Write async tests for MCP tools (TDD)
- [ ] Add docker-compose.day11.yml for mongodb + mcp-server
