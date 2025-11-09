# CLI Backoffice бота (RU)

Детерминированный интерфейс командной строки, повторяющий сценарии Telegram
бота (подписки/дайджесты) без распознавания интентов. Предназначен только для
владельца.

## 1. Запуск CLI

```bash
poetry run python -m src.presentation.cli.backoffice.main <группа> <команда> [опции]
```

- Стандартный вывод — табличный.
- Флаг `--json` включает машинно-читаемый JSON.
- Все команды требуют `--user-id` (идентификатор пользователя в системе).

## 2. Обзор команд (Stage 02_02)

| Команда | Назначение | Статус |
|---------|------------|--------|
| `channels list` | Показать активные подписки пользователя | Готово |
| `channels add` | Подписать пользователя на канал (с валидацией) | Готово |
| `channels remove` | Деактивировать подписку | Готово |
| `digest run` | Сформировать дайджест по каналу/каналам | Готово |
| `digest last` | Показать время последнего дайджеста и метаданные | Готово |
| `channels refresh` | Принудительный сбор постов | Бэклог |
| `digest export` | Экспорт дайджеста (Markdown/PDF) | Бэклог |
| `nlp test` | Проверка NLP-классификатора | Опционально |

## 3. Команды для каналов

### 3.1 `channels list`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    channels list --user-id 12345 [--limit 100] [--json]
```

- Таблица содержит `id`, `channel`, `title`, `tags`, `active`, `subscribed_at`.
- В JSON режиме возвращается список объектов.
- `--limit` ограничивает количество записей (по умолчанию 100, максимум 500).

### 3.2 `channels add`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    channels add --user-id 12345 --channel tech_news [--tag аналитика] [--json]
```

- Выполняется проверка канала через Telegram metadata API.
- Теги передаются повторяющимися флагами `--tag`.
- Коды возврата: `0` — успех/уже подписан, `1` — ошибка валидации.

### 3.3 `channels remove`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    channels remove --user-id 12345 --channel-id 507f1f77bcf86cd799439011 [--json]
```

- Возвращает статус `deleted` / `not_found`.

### 3.4 `channels refresh`

> Функциональность запланирована после MVP.

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    channels refresh --user-id 12345 --channel-id 507f... [--hours 72]
```

Запускает сбор постов (worker/MCP) и выводит идентификатор задания.

## 4. Команды дайджестов

### 4.1 `digest run`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    digest run --user-id 12345 [--channel tech_news] [--hours 24] \
    [--format markdown|json] [--json]
```

- Без `--channel` генерирует дайджесты по всем активным подпискам.
- `--format markdown` — выводит текст дайджеста, `json` — структуру с метаданными.
- JSON режим возвращает список объектов с полями `channel`, `summary`, `post_count` и т.д.

### 4.2 `digest last`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    digest last --user-id 12345 --channel tech_news [--json]
```

- Показывает `last_digest`, `title`, `tags`, признак `active`.
- Если канал не найден — код возврата `1` и сообщение об ошибке.

## 5. NLP-команда (опционально)

```
poetry run python -m src.presentation.cli.backoffice.main \
    nlp test --user-id 12345 --text "покажи дайджест tech news"
```

Используется для проверки классификатора и регрессионных тестов.

## 6. Примечания к реализации

- Команды переиспользуют текущие MCP-инструменты (Stage 02_01) для подписок.
- Экспортируются метрики Prometheus: `cli_command_total`, `cli_command_duration_seconds`,
  `cli_command_errors_total`.
- Аутентификация: режим владельца, параметры подключения — через переменные окружения.
- Бэклог: массовые операции, CSV импорт/экспорт, расписания дайджестов, PDF экспорт.

## 7. Локализация

- Маркдаун-версия команд доступна в EN/ RU (`docs/API_BOT_BACKOFFICE.md` / `.ru.md`).
- Результаты дайджестов выводятся на русском (в зависимости от настроек summarizer).

