# Stage 02_01 · Worklog

## Overview

- **Stage:** 02_01 – MCP Tool Catalogue Freeze
- **Date:** 2025-11-09
- **Tech lead:** Assistant (with user oversight)
- **Developers:** Assistant agents (implementation), user (approvals, guidance)

## Summary

| Category | Notes |
|----------|-------|
| Scope | Freeze актуального набора MCP-инструментов, ввести статусы жизненного цикла, подготовить миграции и уведомления. |
| Key Outputs | `mcp_tool_matrix.md`, обновлённый `tools_registry.py`, `mcp_migration_bulletin.md`, `API_MCP.md` (EN/RU), EP04 координация. |
| Result | Supported инструменты доступны по умолчанию; deprecated/archived скрыты за флагом `MCP_INCLUDE_DEPRECATED_TOOLS`; документация и тесты синхронизированы. |

## Timeline

1. **Инвентаризация** – сверка Stage 00 каталога, подтверждение статусов keep/rework/archive.
2. **Кодовые правки** – регистрация инструментов с учётом статусов, флаг для legacy, предупреждения в deprecated модулях.
3. **Документация** – матрица, миграционный бюллетень, обновление API/операционных заметок, подготовка EP04.
4. **Тесты** – пометка устаревших тестов (xfail/skip), сохранение активных проверок digest/channel/NLP.
5. **Финализация** – подготовка worklog, smoke test, CHANGELOG, handoff для Stage 02_02 (текущий шаг).

## Roles & Responsibilities

| Роль | Ответственность | Исполнитель |
|------|-----------------|-------------|
| Tech Lead | Планирование Stage 02_01, согласование решений | Assistant |
| Developer Agent | Обновление кода MCP server/registry, инструментов | Assistant |
| Documentation | Матрица, бюллетень, API обновления | Assistant |
| QA | Актуализация тестов, подготовка smoke test | Assistant |
| Stakeholder | Утверждение подхода, уточнения по CLI Stage 02_02 | User |

## Decisions & Deltas

| Тема | Решение | Дельта/Комментарий |
|------|---------|--------------------|
| Deprecated инструменты | Скрывать по умолчанию, доступ через `MCP_INCLUDE_DEPRECATED_TOOLS` | Флаг документирован, фоллбэк для совместимости. |
| Reminder flows | Переведены в архив, интеграции будут сняты в EP04 | Требуется зачистка бот/CLI после Stage 02_03. |
| PDF digest | Деприкейтить, заменить CLI `digest:export` (Stage 02_02) | Временно доступен под флагом с предупреждениями. |
| Homework review | Деприкейтить, ждать рефактор EP01 | Тесты переведены в xfail, обязательное обновление после EP01. |
| Tool metadata | Ввести статусы (`supported`, `transition`, `deprecated`, `archived`) + `note` | Discovery теперь возвращает больше данных; клиентам нужно обновление. |
| EP04 подготовка | Список файлов и зависимостей передан в `coordination_stage_02_01.md` | Архивировать после завершения Stage 02_03/Stage 02_02. |
| Public CHANGELOG | Требуется отдельная запись | Выполняется как часть closing steps. |

## Metrics & Evidence

| Метрика | Значение |
|---------|----------|
| Инструменты в матрице | 12 (6 supported, 4 transition, 2 deprecated, 5 archived; пересечения по статусам, см. документ) |
| Обновлённые документы | 6 (матрица, бюллетень, координация EP04, API EN/RU, план Stage) |
| Тесты | 4 файла скорректированы (PDF, homework, reminder tools/tests) |
| Флаги/конфигурации | 1 новый флаг (`MCP_INCLUDE_DEPRECATED_TOOLS`) |

### Smoke Test Status
- `poetry run pytest src/tests/presentation/mcp/test_digest_tools.py -v` — **не выполнено** (Mongo требует аутентификации; окружение без `MONGODB_URL` с кредами).
- Рекомендация: повторить на окружении с `TEST_MONGODB_URL`/`MONGODB_URL` из shared infra либо добавить фикстуру с моками.

## Open Questions

| Вопрос | Статус |
|--------|--------|
| Поддержание deprecated инструментов под флагом до Stage 02_02 | Решён: оставляем до поставки CLI, затем удаляем |
| Public CHANGELOG | Решить в рамках closing steps (добавить запись) |
| Smoke test retained tools | Запланировано в closing steps |

## References

- `docs/specs/epic_02/mcp_tool_matrix.md`
- `docs/specs/epic_02/mcp_migration_bulletin.md`
- `docs/specs/epic_04/coordination_stage_02_01.md`
- `docs/reference/en/API_MCP.md`, `docs/reference/ru/API_MCP.ru.md`
- `src/presentation/mcp/tools_registry.py`
- `tests/` (PDF/homework/reminder suites)
