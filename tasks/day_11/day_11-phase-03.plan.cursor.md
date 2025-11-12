<!-- 86473cf7-3a7d-44c3-8ebe-ddcffc5e019a 69a7a034-f44a-4a91-8bc8-4b94ed4bd28c -->
# Phase 3 Plan — Bot Interface, UX, and Date Parsing

## Scope
- Bot UI: main/menu, tasks UI (list/view/complete/delete), channels UI (subscribe/list/unsubscribe)
- Enhance date parsing for natural language (locale-aware)
- End-to-end flows: NL → intent → task creation → list/complete

## Architecture Decisions (chief-architect)
- Keep aiogram handlers modular under `src/presentation/bot/handlers/`
  - `tasks.py`, `channels.py`, `menu.py`
- Introduce `DateParser` service under `src/application/services/date_parser.py`
  - Wrap `dateparser` with explicit locale/timezone, deterministic options
- Reuse MCP reminder tools; bot calls MCP via `MCPClient`
- Limit message length; chunk long lists; consistent emoji/status icons

## Files to Add/Change
- Add: `src/application/services/date_parser.py`
  - `parse_datetime(text: str, tz: str) -> str | None` (ISO-8601)
- Change: `src/presentation/bot/butler_bot.py`
  - Wire menu command `/menu`, register routers
- Add: `src/presentation/bot/handlers/menu.py`
  - Build main menu, navigate to tasks/channels/summary/digest placeholders
- Add: `src/presentation/bot/handlers/tasks.py`
  - List tasks (pagination), view details, complete, delete
- Add: `src/presentation/bot/handlers/channels.py`
  - Add subscription, list subscriptions, remove subscription (MCP stubs OK)
- Change: `src/infrastructure/config/settings.py`
  - `default_timezone`, `default_locale`

## ML Engineering (ml-engineer)
- For free-form deadlines in NL, call `DateParser` in orchestrator refinement step (Phase 2 models already accept ISO)
- If parse fails, add clarification question for date format

## Testing Strategy (TDD)
- Unit tests:
  - `src/tests/application/test_date_parser.py`
  - `src/tests/presentation/bot/test_tasks_handlers.py`
  - `src/tests/presentation/bot/test_channels_handlers.py`
- Integration test:
  - `src/tests/presentation/bot/test_menu_navigation.py`
- Coverage ≥80% for new code

## UX (python-zen-writer)
- Consistent English docstrings, concise inline comments for non-obvious logic
- Buttons: short labels; paginate 10 items/page; back buttons
- Avoid magic numbers; constants at top of file

## Config & Env
- `DEFAULT_TZ=UTC`, `DEFAULT_LOCALE=en`
- Feature flags: `ENABLE_CHANNELS_UI=true` (if needed)

## Final Deliverable
- Exactly one summary file at `tasks/day_11/day_11-phase-03-summary.md` containing:
  - Completed items and architecture decisions
  - How to run the bot locally (env var for token) and how to test
  - Known limitations and Phase 4 pointers

## To-dos
- [ ] Add DateParser service and tests
- [ ] Extend settings with timezone/locale defaults
- [ ] Implement menu handlers and navigation
- [ ] Implement tasks handlers (list/detail/complete/delete)
- [ ] Implement channels handlers (subscribe/list/unsubscribe)
- [ ] Wire bot to use handlers and menu
- [ ] Add unit tests for handlers and date parser
- [ ] Add integration tests for menu navigation and pagination
- [ ] Produce Phase 3 summary file

### To-dos

- [ ] Add DateParser service and tests
- [ ] Extend settings with timezone/locale defaults
- [ ] Implement menu handlers and navigation
- [ ] Implement tasks handlers (list/detail/complete/delete)
- [ ] Implement channels handlers (subscribe/list/unsubscribe)
- [ ] Wire bot to use handlers and menu
- [ ] Add unit tests for handlers and date parser
- [ ] Add integration tests for menu navigation and pagination
- [ ] Produce tasks/day_11/day_11-phase-03-summary.md
