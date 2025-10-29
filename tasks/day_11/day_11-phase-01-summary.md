# Day 11 — Phase 1 Summary (Core Infrastructure)

## Scope delivered
- MongoDB async stack with Motor: `src/infrastructure/database/mongo.py`
- Centralized config: `src/infrastructure/config/settings.py`
- Task domain models (Pydantic): `src/domain/entities/task.py`
- Task repository (CRUD + queries): `src/infrastructure/repositories/task_repository.py`
- MCP Reminder tools (registered on shared server): `src/presentation/mcp/tools/reminder_tools.py`
- Server import for tools: `src/presentation/mcp/server.py`
- Minimal aiogram bot skeleton: `src/presentation/bot/butler_bot.py`
- Docker Compose for MongoDB + MCP HTTP: `docker-compose.day11.yml`
- Tests (TDD):
  - Repo: `src/tests/infrastructure/test_task_repository.py`
  - Tools: `src/tests/presentation/mcp/test_reminder_tools.py`

## Key decisions
- Motor (async) with singleton client and per-DB accessor
- Pydantic models for validation (`TaskIn`, `TaskUpdate`); ISO-8601 for datetimes
- MCP tools live under `src/presentation/mcp/tools/` and register via importing shared `mcp` from `server.py`
- Environment-driven config via `pydantic-settings`

## How to run
1) Install dependencies (poetry):
   - motor, aiogram, freezegun added to `pyproject.toml`
2) Start services:
```bash
docker compose -f docker-compose.day11.yml up --build -d
```
3) Health:
```bash
curl http://localhost:8004/health
```

## How to test (pytest, coverage ≥80%)
```bash
pytest --maxfail=1 --disable-warnings -q --cov=src --cov-report=term-missing
```
Notes:
- Tests use `DB_NAME=butler_test` and `MONGODB_URL` (defaults to `mongodb://localhost:27017`).
- Ensure MongoDB is running locally or via the compose file.

## Next steps (Phase 2+ preview)
- NLP orchestrator integration for intent parsing and clarifications
- Expand bot handlers (menu, tasks UI, channels UI)
- Scheduled workers for summaries and digests

## Known limitations
- No channel digest tools yet
- Bot is minimal (only /start and /help)
- Date parsing/formatting kept simple (expects ISO-8601)
