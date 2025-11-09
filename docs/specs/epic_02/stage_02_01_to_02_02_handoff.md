# Stage 02_01 → Stage 02_02 · Handoff Brief

## Snapshot
- **Stage 02_01 status:** Completed (2025-11-09). Matrix, registry, migration bulletin, API docs опубликованы.
- **Stage 02_02 focus:** Реализация CLI backoffice команд, покрывающих ключевые операции каналов и дайджестов.
- **Primary contacts:** Tech lead (Assistant), CLI developer agent (to be assigned), Ops stakeholder (TBD).

## Confirmed Decisions

| Тема | Решение | Комментарий |
|------|---------|-------------|
| Минимальный набор CLI команд | `channels:list`, `channels:add`, `channels:remove`, `digest:run`, `digest:last` | Обеспечить паритет с основными MCP-флоу digest/channel. |
| Расширение | `channels:refresh`, `digest:export`, `nlp:test` | Добавить в бэклог; реализовать после первой итерации. |
| Формат вывода | Табличный (по умолчанию) + JSON через `--json` | Закладываем сразу, чтобы избежать переработок сериализации. |
| Observability | Базовые Prometheus метрики (успех/ошибка, длительность) | Расширенную интеграцию перенести в EP03. |
| Режим | Детерминированный, без интерактивных промптов | При необходимости позже добавить `--force`. |
| Legacy MCP tools | Отключены по умолчанию; доступны с `MCP_INCLUDE_DEPRECATED_TOOLS` | Удалить после успешной поставки CLI Stage 02_02/02_03. |

## Technical Inputs for CLI

- **Repositories / Modules**
  - `src/presentation/cli/backoffice/` — место размещения новых команд.
  - Использовать существующие application services из `src/application/` и MCP tool adapters где возможно.
- **Dependencies**
  - MongoDB (подписки/посты), LLM API (summaries), Prometheus (метрики), feature flags из Stage 02_01.
- **Testing**
  - Юнит-тесты для логики команд (mock сервисов).
  - Интеграционные тесты с использованием тестовых Mongo/LLM фикстур (auth-ready).
  - Smoke тесты (manual) для typical workflows.
- **Docs**
  - Обновлять `docs/API_BOT_BACKOFFICE.md` (+ RU версия) с примерами команд и флагов.
  - Ссылаться на `docs/CHANGELOG_MCP.md` для коммуникации изменений.

## Risks & Mitigations

| Риск | Влияние | Митигация |
|------|---------|-----------|
| Недоступность Mongo/LLM в CI | Блокирует интеграционные тесты | Использовать моки или auth-ready контейнеры; документировать prereqs. |
| Несогласованность CLI и MCP API | Расхождение контрактов | Переиспользовать одни и те же application services; поддерживать миграционный бюллетень. |
| Отложенная observability | Потеря видимости по ошибкам CLI | Реализовать счетчики/таймеры сразу, расширение (tracing) оставить EP03. |

## Next Steps
1. Назначить CLI developer agent и подтвердить roadmap backlog.
2. Создать skeleton для `cli/backoffice` с общими util (output formatter, Prometheus hooks).
3. Реализовать минимальный набор команд + тесты.
4. Обновить документацию и changelog по мере релизов.
5. Подготовить демо/мануал для операторов (по возможности).

## References
- `docs/specs/epic_02/mcp_tool_matrix.md`
- `docs/specs/epic_02/mcp_migration_bulletin.md`
- `docs/specs/epic_04/coordination_stage_02_01.md`
- `docs/CHANGELOG_MCP.md`
- `docs/API_MCP.md`, `docs/API_BOT_BACKOFFICE.md`

