# Channel Resolution: Как работает поиск канала по подпискам

## Обзор

Когда пользователь запрашивает дайджест для канала "Набока", система должна найти правильный username канала (например, "onaboka") из подписок пользователя. Это делается через **Channel Resolution** - процесс сопоставления пользовательского ввода с реальными каналами.

## Цепочка работы

### Шаг 1: Извлечение имени канала из запроса

**Файл**: `src/presentation/bot/handlers/butler_handler.py`

Функция `_extract_digest_request_info()` использует regex-паттерны для извлечения:
- Имени канала: "Набоки"
- Периода времени: "5 дней" → 120 часов

```python
# Пример: "Дай дайджет Набоки за 5 дней"
channel_name, hours = _extract_digest_request_info(text)
# Результат: channel_name="Набоки", hours=120
```

Если regex не сработал, используется LLM fallback (`_parse_digest_request_with_llm`).

### Шаг 2: Получение подписок пользователя

**Файл**: `src/application/use_cases/resolve_channel_name.py`

```python
# Запрос к базе данных
db.channels.find({"user_id": user_id, "active": True})
```

Получаем список каналов пользователя:
```python
[
    {"channel_username": "onaboka", "title": "Набока"},
    {"channel_username": "xor_journal", "title": "XOR Journal"},
    {"channel_username": "alexgladkovblog", "title": "Alex Gladkov Blog"}
]
```

### Шаг 3: LLM-сопоставление

**Файл**: `src/domain/services/channel_resolver.py`

#### 3.1. Формирование промпта

**Файл**: `src/infrastructure/llm/prompts/channel_matching_prompts.py`

Промпт для LLM содержит:
- Ввод пользователя: "Набоки"
- Список подписанных каналов с username и title

Пример промпта (русская версия):
```
Ты - помощник для сопоставления названий каналов. Получив пользовательский ввод и список подписанных каналов,
найди наилучшее совпадение.

Ввод пользователя: "Набоки"

Подписанные каналы:
1. Username: @onaboka, Название: Набока
2. Username: @xor_journal, Название: XOR Journal
3. Username: @alexgladkovblog, Название: Alex Gladkov Blog

Инструкции:
- Сопоставь ввод пользователя с username или названием канала (без учета регистра)
- Обрабатывай кириллические/латинские варианты (например, "Набока" соответствует "onaboka")
- Обрабатывай частичные совпадения (например, "python" соответствует "python_daily")
- Учитывай распространенные сокращения и вариации
- Верни оценку уверенности на основе качества совпадения:
  * 0.9-1.0: Точное совпадение или очень близкий вариант
  * 0.7-0.9: Четкое совпадение с незначительными вариациями
  * 0.5-0.7: Частичное совпадение или разумное предположение
  * Ниже 0.5: Слабое совпадение, не должно использоваться

Верни ТОЛЬКО валидный JSON в этом точном формате:
{
  "matched": true/false,
  "channel_username": "username" или null,
  "confidence": 0.0-1.0,
  "reason": "краткое объяснение"
}
```

#### 3.2. Вызов LLM

```python
response = await llm_client.generate(
    prompt=prompt,
    temperature=0.2,  # Низкая температура для детерминированности
    max_tokens=256
)
```

#### 3.3. Парсинг ответа LLM

**Пример ответа LLM**:
```json
{
  "matched": true,
  "channel_username": "onaboka",
  "confidence": 0.95,
  "reason": "Точное совпадение: ввод 'Набоки' соответствует названию канала 'Набока' (username: onaboka)"
}
```

**Парсинг**:
- Извлекается JSON из ответа (может быть в markdown code blocks)
- Проверяется confidence >= 0.5
- Если confidence достаточен, возвращается `ChannelResolutionResult`

### Шаг 4: Обогащение результата

**Файл**: `src/application/use_cases/resolve_channel_name.py`

После получения результата от LLM, система:
1. Находит title канала из списка подписок
2. Обогащает `ChannelResolutionResult` с `channel_title`

```python
if result.found and result.channel_username:
    for ch in channels_list:
        if ch.get("channel_username") == result.channel_username:
            result.channel_title = ch.get("title")
            break
```

### Шаг 5: Fallback - поиск в Telegram

**Файл**: `src/application/use_cases/resolve_channel_name.py`

Если канал не найден в подписках и `allow_telegram_search=True`:

1. Вызывается `search_channels_by_name()` через Pyrogram
2. Ищется в dialogs пользователя по title/username
3. Возвращается top-1 результат с confidence=0.8

**Файл**: `src/infrastructure/clients/telegram_utils.py`

```python
async def search_channels_by_name(query: str, limit: int = 5) -> List[dict]:
    # Ищет в dialogs пользователя
    # Сопоставляет по title или username (case-insensitive, partial match)
    # Возвращает результаты с username, title, description, chat_id
```

## Пример полного процесса

### Входные данные
- Пользователь: "Дай дайджет Набоки за 5 дней"
- user_id: 204047849

### Шаг 1: Извлечение
```
channel_name = "Набоки"
hours = 120
```

### Шаг 2: Подписки
```python
channels = [
    {"channel_username": "onaboka", "title": "Набока"},
    {"channel_username": "xor_journal", "title": "XOR Journal"},
    ...
]
```

### Шаг 3: LLM промпт
```
Ввод пользователя: "Набоки"
Подписанные каналы:
1. Username: @onaboka, Название: Набока
...
```

### Шаг 4: LLM ответ
```json
{
  "matched": true,
  "channel_username": "onaboka",
  "confidence": 0.95,
  "reason": "Точное совпадение: ввод 'Набоки' соответствует названию канала 'Набока'"
}
```

### Шаг 5: Результат
```python
ChannelResolutionResult(
    found=True,
    channel_username="onaboka",
    channel_title="Набока",
    confidence_score=0.95,
    source="subscription",
    reason="Точное совпадение..."
)
```

### Шаг 6: Использование результата

**Файл**: `src/presentation/bot/handlers/butler_handler.py`

```python
# Заменяем название на username в запросе
text = "дайджест по onaboka за 5 дней"

# Передаем в orchestrator
# Orchestrator вызывает MCP tool get_channel_digest_by_name
# с параметром channel_username="onaboka"
```

## Преимущества LLM-подхода

1. **Понимание контекста**: LLM понимает, что "Набока" и "Набоки" - это одно и то же
2. **Транслитерация**: Может сопоставить кириллицу с латиницей
3. **Частичные совпадения**: Может найти "python" в "python_daily"
4. **Оценка уверенности**: Возвращает confidence score для фильтрации слабых совпадений

## Настройки

- **Temperature**: 0.2 (низкая для детерминированности)
- **Max tokens**: 256 (достаточно для JSON ответа)
- **Min confidence**: 0.5 (фильтр слабых совпадений)

## Обработка ошибок

1. **LLM не вернул JSON**: Возвращается `found=False`
2. **Low confidence**: Если confidence < 0.5, результат игнорируется
3. **Fallback на Telegram search**: Если не найдено в подписках и разрешен поиск

## Интеграция с другими компонентами

- **Butler Handler**: Использует resolution для замены названия на username
- **Channel Digest**: Использует resolved username для поиска постов
- **Post Repository**: Ищет посты по `channel_username` в базе
- **Telegram Search**: Fallback если не найдено в подписках
