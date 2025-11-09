# MCP Tooling Changelog

## 2025-11-09 · Stage 02_01 — MCP Tool Catalogue Freeze

### Breaking Changes
- Reminder MCP tools (`add_task`, `list_tasks`, `update_task`, `delete_task`, `get_summary`) archived and скрываются из discovery по умолчанию.
- PDF digest MCP toolchain (`get_posts_from_db`, `summarize_posts`, `format_digest_markdown`, `combine_markdown_sections`, `convert_markdown_to_pdf`) помечены как deprecated; планируется замена CLI `digest:export` в Stage 02_02.
- Homework review MCP tool (`review_homework_archive`) помечен как deprecated; будет заменён новой интеграцией после завершения EP01.

### New Features
- Инструменты discovery теперь возвращают статус жизненного цикла (`supported`, `transition`, `deprecated`, `archived`) и поясняющую `note`.
- Добавлен флаг окружения `MCP_INCLUDE_DEPRECATED_TOOLS` для явного включения deprecated/archived инструментов.
- Обновлён MCP Tools Registry с фильтрацией по статусу и расширенным описанием.

### Migration Guidance
- Используйте `docs/specs/epic_02/mcp_migration_bulletin.md` для подробного плана миграций и сроков.
- План архивирования инструментов и связанных тестов см. в `docs/specs/epic_04/coordination_stage_02_01.md`.

## 2025-11-10 · Stage 02_02 — CLI Backoffice Delivery

### New Features
- Запущен backoffice CLI (`src/presentation/cli/backoffice/`) с командами:
  - `channels list|add|remove`
  - `digest run|last`
- Двойной вывод: табличный (по умолчанию) и JSON (`--json`).
- Prometheus метрики для CLI (`cli_command_total`, `cli_command_duration_seconds`, `cli_command_errors_total`).
- Документация обновлена (`docs/API_BOT_BACKOFFICE*.md`) с примерами использования.

### Migration Notes
- CLI использует существующие MCP-инструменты до полного переноса логики.
- `digest run --format json` предоставляет расширенные сведения для downstream-клиентов.
- Команды `channels refresh` и `digest export` остаются в бэклоге (см. handoff Stage 02_01 → 02_02).


