# API MCP-инструментов (RU)

Сервер MCP теперь по умолчанию публикует только поддерживаемые инструменты для
дайджестов, каналов и NLP. Устаревшие и архивируемые инструменты становятся
доступны лишь при установке флага `MCP_INCLUDE_DEPRECATED_TOOLS=1` как на
сервере, так и на клиентах. В метаданных каждого инструмента присутствует поле
`status`, отражающее жизненный цикл.

## 1. Обзор discovery

- Используйте `MCPToolsRegistry.discover_tools()` для получения актуального
  списка.
- Доступные статусы: `supported`, `transition`, `deprecated`, `archived`.
- Инструменты со статусом `deprecated` и `archived` скрываются, пока не
  активирован флаг совместимости.
- Поле `note` содержит краткое пояснение (например, целевой CLI-эквивалент).

```python
from src.presentation.mcp.client import MCPClient
from src.presentation.mcp.tools_registry import MCPToolsRegistry

client = MCPClient()
registry = MCPToolsRegistry(client)
tools = await registry.discover_tools()

for tool in tools:
    print(tool.name, tool.status, tool.note)
```

## 2. Поддерживаемые инструменты

| Имя | Модуль | Назначение | Примечание |
|-----|--------|------------|------------|
| `parse_digest_intent` | `nlp_tools.py` | NLP-анализ запроса на дайджест | Сохраняет русскую локализацию и подсказки. |
| `get_channel_digest_by_name` | `channels/channel_digest.py` | Дайджест по заданному каналу | Работает через модульную суммаризацию. |
| `get_channel_digest` | `channels/channel_digest.py` | Дайджест по всем активным подпискам | Поддерживает use-case `GenerateChannelDigest`. |
| `request_channel_digest_async` | `channels/channel_digest.py` | Постановка длительной задачи на дайджест | Возвращает идентификатор задания для воркера. |
| `get_channel_metadata` | `channels/channel_metadata.py` | Получение метаданных из Mongo/Telegram | Используется CLI и ботом. |
| `resolve_channel_name` | `channels/channel_resolution.py` | Распознавание канала по вводу пользователя | При необходимости обращается к Telegram-поиску. |

### 2.1 `get_channel_digest`

**Параметры**

```json
{
  "user_id": 12345,
  "hours": 24
}
```

**Ответ**

```json
{
  "digests": [
    {
      "channel": "tech_news",
      "summary": "Краткое содержание…",
      "post_count": 5,
      "tags": ["analytics"]
    }
  ],
  "generated_at": "2025-11-09T11:00:00Z"
}
```

### 2.2 `get_channel_metadata`

**Параметры**: `{ "channel_username": "tech_news", "user_id": 12345 }`

**Ответ**: `success`, `title`, `description`, сообщение о том, использовался ли
Telegram-поиск для уточнения данных.

### 2.3 `parse_digest_intent`

**Параметры**: `{ "text": "дайджест за последние 24 часа", "user_context": {} }`

**Ответ**: `intent_type`, вероятность, вычисленные `hours`, список рекомендуемых
инструментов MCP и вопросы для уточнения.

## 3. Инструменты со статусом `transition`

Инструменты сохраняются до выпуска CLI Stage 02_02. Рекомендуется заранее
перейти на соответствующие команды CLI.

| Имя | Назначение | Планируемая замена |
|-----|------------|--------------------|
| `add_channel` | Подписка на канал | `cli channels add` |
| `list_channels` | Список подписок | `cli channels list` |
| `delete_channel` | Удаление подписки | `cli channels remove` |
| `get_posts` | Получение постов из Mongo | `cli channels refresh --dry-run` |
| `collect_posts` | Сбор постов через Telegram | `cli channels refresh` |
| `save_posts_to_db` | Сохранение собранных постов | CLI-конвейер записи |

> **Важно:** Эти инструменты продолжают требовать Mongo и Telegram. Ответы не
> меняются до завершения Stage 02_02.

## 4. Инструменты со статусом `deprecated` (по флагу)

| Имя | Комментарий |
|-----|-------------|
| `review_homework_archive` | Будет заменён модульным ревьюером после EP01. |
| `get_posts_from_db` | PDF-дайджест переносится в CLI `digest:export`. |
| `summarize_posts` | Суммаризации выполняются в CLI-пайплайне. |
| `format_digest_markdown` | Форматирование переезжает в CLI-шаблоны. |
| `combine_markdown_sections` | Склейка секций будет выполняться CLI. |
| `convert_markdown_to_pdf` | Экспорт PDF выводится из MCP. |

Каждый вызов таких инструментов генерирует предупреждение уровня `WARNING`.

## 5. Инструменты со статусом `archived`

| Имя | Причина |
|-----|---------|
| `add_task`, `list_tasks`, `update_task`, `delete_task`, `get_summary` | Функциональность напоминаний закрыта. |
| `parse_task_intent` | NLP-интент для задач более не используется. |

Инструменты будут перенесены в `archive/` в ходе EP04.

## 6. Модель ошибок

```json
{
  "status": "error",
  "error": "описание проблемы",
  "details": {"context": "..."}
}
```

Типовые ошибки: `invalid_user_id`, `channel_not_found`, `digest_unavailable`,
`nlp_timeout`.

## 7. Здоровье и наблюдаемость

- `GET /health` → `{"status": "ok"}`
- Метрики Prometheus доступны при активной общей инфраструктуре.
- Вызовы устаревших инструментов логируются с уровнем `WARNING`.

## 8. Связанные документы

- `docs/specs/epic_02/mcp_tool_matrix.md` — итоговая матрица инструментов.
- `docs/specs/epic_02/mcp_migration_bulletin.md` — миграционный бюллетень.
- `docs/API_MCP.md` — англоязычная версия.
- `docs/API_BOT_BACKOFFICE.ru.md` — справочник по CLI (Stage 02_02).

