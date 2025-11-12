# Stage 02_02 · Worklog (MVP)

## Snapshot
- **Scope:** CLI backoffice минимальный набор (channels list/add/remove, digest run/last)
- **Date:** 2025-11-10
- **Tech lead:** Assistant (user oversight)
- **Status:** MVP commands реализованы, тесты зелёные, документация обновлена

## Summary

| Категория | Состояние |
|-----------|-----------|
| Команды | `channels list/add/remove`, `digest run/last` реализованы |
| Форматы вывода | Таблица (по умолчанию), JSON (`--json`) |
| Observability | Prometheus метрики (`cli_command_total`, `cli_command_duration_seconds`, `cli_command_errors_total`) |
| Документация | `docs/reference/en/API_BOT_BACKOFFICE.md` / `docs/reference/ru/API_BOT_BACKOFFICE.ru.md`, `docs/archive/release_notes/CHANGELOG_MCP.md` |
| Тесты | Юнит + интеграционные (см. раздел ниже) |

## Timeline
1. **Структура CLI** — `src/presentation/cli/backoffice/` (main, commands, formatters, metrics)
2. **Formatter & Metrics** — двойной вывод, декоратор `track_command`
3. **Channels** — list пользователями, add/remove через MCP инструменты
4. **Digest** — run (use cases), last (Mongo metadata)
5. **Документация** — обновлены EN/RU гайды, changelog
6. **Тесты** — unit (formatters/commands), интеграция (`test_cli_flow`)

## Tests

```bash
poetry run pytest src/tests/presentation/cli/backoffice -q
# 16 passed
```

## Dependencies & Notes
- Команды `channels add/remove` пока используют существующие MCP инструменты (Stage 02_01). План: мигрировать на чистые application services после удаления legacy.
- `digest run --format json` возвращает расширенный payload, совместимый с downstream потребителями.
- `channels refresh`, `digest export`, `nlp test` остаются в бэклоге (см. stage spec).
- Требуются переменные окружения (Mongo, LLM) как для основной системы.

## Next Steps
- Реализовать команды бэклога (`channels refresh`, `digest export`, `nlp test`)
- Добавить поддержу batch операций/CSV (EP03/EP04)
- Расширить тесты для реальной БД (auth-ready fixtures) и e2e CLI сценариев
