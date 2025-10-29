# Debug Issues Summary

## Проблемы найдены:

### 1. `get_summary` возвращает 0 задач
- В БД есть 4 активные задачи для user_id=204047849
- Прямой запрос MongoDB возвращает 4 задачи
- Python фильтрация возвращает 4 активные задачи
- НО `get_summary(user_id, "last_24h")` возвращает 0 задач

**Возможная причина**: Переменная `tasks` обнуляется где-то после фильтрации или код не попадает в ветку `if timeframe == "last_24h"`.

**Что проверить**:
- Логи MCP сервера на наличие "Fetching all tasks for last_24h debug mode"
- Логи "Found all tasks" и "Filtered active tasks"
- Не происходит ли исключение, которое перехватывается и возвращает пустой список

### 2. `get_channel_digest` возвращает 0 дайджестов
- В БД есть 3 активных канала: xor_journal, mobiledevnews, onaboka
- Каналы доступны через Bot API (bot.get_chat работает)
- НО `fetch_channel_posts` возвращает 0 постов
- НО `get_channel_digest` возвращает 0 дайджестов

**Возможная причина**: 
- `fetch_channel_posts` не возвращает placeholder посты (логи "Channel accessible" и "Returning posts" не появляются)
- Возможно, происходит исключение, которое не логируется
- Или `TELEGRAM_BOT_TOKEN` не доступен в контексте MCP сервера

**Что проверить**:
- Логи MCP сервера при вызове `get_channel_digest`
- Логи "Channel accessible" и "Returning posts" в `fetch_channel_posts`
- Доступность `TELEGRAM_BOT_TOKEN` в контейнере mcp-server

## Следующие шаги:

1. Проверить логи MCP сервера с уровнем INFO
2. Убедиться, что `TELEGRAM_BOT_TOKEN` доступен в mcp-server контейнере
3. Добавить прямой тест вызова `get_summary` из MCP сервера с выводом всех промежуточных значений
4. Проверить, не перехватывается ли исключение в try/except блоках

