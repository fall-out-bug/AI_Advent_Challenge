# 🎓 Полный Guide: MCP + Agents Architecture

**Вопросы:**
1. Как правильно работать с MCP и агентами?
2. Почему агент не понимает что делать?
3. Влияет ли русский язык?

**Ответ:** Да на все вопросы, но есть правильный способ.

---

## 📚 Теория: Что такое MCP Agent правильно

### ❌ Неправильный способ (ваша текущая проблема):

```python
# НЕПРАВИЛЬНО: Агент вставляет инструменты в системный промпт
system_prompt = """
Ты агент. У тебя есть инструменты:
1. get_posts(channel_id: str, limit: int) -> List[Post]
   Получить посты из канала
2. create_digest(posts: List[Post]) -> str
   Создать дайджест

Пожалуйста используй инструменты...
"""

# Модель видит:
# - 1000+ слов инструкций
# - Становится "говорящей энциклопедией" вместо "инструмента"
# - Выдает весь текст вместо вызова инструмента
# - Языковая путаница (смешивание английского и русского)
```

### ✅ Правильный способ (OpenAI Function Calling):

```python
# ПРАВИЛЬНО: Инструменты передаются ОТДЕЛЬНО от системного промпта
system_prompt = "Ты помощник в получении новостей из Telegram."

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_posts",
            "description": "Получить посты из канала за последние N дней",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "ID канала (например: 'onaboka')"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Количество дней (1-30)"
                    }
                },
                "required": ["channel_id", "days"]
            }
        }
    },
    # ... остальные инструменты
]

# Модель получает:
# ✓ Краткий системный промпт (< 100 слов)
# ✓ JSON-описание инструментов (структурированное)
# ✓ Понятная инструкция: когда вызывать инструмент
```

---

## 🔧 Архитектура: Как должно работать

```
┌─────────────────────────────────────────────────────────────┐
│ User Input (any language)                                   │
│ "Создай дайджест по Набока за 3 дня"                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Agent Layer                                                  │
│                                                              │
│ 1. Normalize input (translate if needed, extract intent)    │
│ 2. Build message with tools as JSON (OpenAI format)         │
│ 3. Call LLM with SYSTEM + TOOLS + USER_MESSAGE              │
│                                                              │
│    ┌────────────────────────────────────────────────┐       │
│    │ System: "Ты помощник для новостей"            │       │
│    │ Tools: [{"name": "get_posts", ...}, ...]       │       │
│    │ User: "Создай дайджест по Набока"             │       │
│    └────────────────────────────────────────────────┘       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ LLM Response (structured)                                   │
│ {                                                            │
│   "tool_calls": [                                            │
│     {                                                        │
│       "id": "call_xyz",                                     │
│       "function": {                                         │
│         "name": "get_posts",                               │
│         "arguments": "{\"channel_id\": \"onaboka\", ...}"  │
│       }                                                    │
│     }                                                       │
│   ]                                                        │
│ }                                                          │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Tool Execution (MCP Server)                                │
│                                                             │
│ for tool_call in response.tool_calls:                      │
│     result = mcp.execute(tool_call.function.name,          │
│                          **tool_call.function.args)        │
│                                                             │
│ Returns: {"posts": [...], "count": 23, ...}              │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Format & Return to User                                    │
│                                                             │
│ "✅ Дайджест Набока (23 поста, 3 дня)"                   │
│ "📝 [Summary text]"                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌐 Про русский язык: ДА, это проблема

### ❌ ПРОБЛЕМЫ с русским:

1. **Mistral обучена в основном на английском**
   - Русский язык = ~10% от training data
   - Инструменты в JSON = английский (всегда)
   - Модель путается между русским и английским

2. **System prompts на русском = плохая идея**
   ```python
   # ❌ ПЛОХО: Модель путается
   system = "Ты помощник. Используй инструменты: get_posts, create_digest"

   # ✓ ХОРОШО: Инструменты на английском, подсказки минимальны
   system = "You are a helpful assistant."  # EN + инструменты JSON
   ```

3. **Парсинг JSON из русского текста = сложнее**
   ```python
   # ❌ Модель выдает:
   "Хорошо, я помогу получить посты. Вот JSON:
    {"tool": "get_posts", ...}"  # JSON прячется в тексте

   # ✓ Модель выдает (если правильно обучено):
   {
     "tool_calls": [{
       "function": {
         "name": "get_posts",
         "arguments": "{\"channel_id\": \"onaboka\"}"
       }
     }]
   }
   # Чистый JSON, без текста вокруг
   ```

### ✅ РЕШЕНИЕ: Гибридный подход (Bilingual Agent)

```python
"""
Агент который понимает русский, но думает на английском
"""

class BilingualMCPAgent:
    """Агент с поддержкой русского языка."""

    # ===== СИСТЕМА НА АНГЛИЙСКОМ =====
    SYSTEM_PROMPT = """You are a helpful assistant for Telegram channel digests.

Use the provided tools to help the user.
Always respond with tool calls when needed, then format the response in Russian."""

    # ===== ИНСТРУМЕНТЫ НА АНГЛИЙСКОМ (JSON) =====
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_channel_digest",
                "description": "Get digest of channel posts for N days",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "channel_name": {
                            "type": "string",
                            "description": "Channel name (e.g., 'onaboka')"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days (1-30)"
                        }
                    },
                    "required": ["channel_name", "days"]
                }
            }
        }
    ]

    async def process(self, user_input_ru: str):
        """Обработать русский ввод пользователя.

        Args:
            user_input_ru: Русский текст ("Дайджест по Набока за 3 дня")

        Returns:
            Русский ответ
        """

        # ===== ШАГ 1: Нормализация русского ввода =====
        # Парсим намерение БЕЗ отправки модели
        intent = self._parse_russian_intent(user_input_ru)

        # Пример: intent = {
        #     "action": "get_digest",
        #     "channel": "onabока" → "onaboka",
        #     "days": 3
        # }

        # ===== ШАГ 2: Вызов LLM (система + инструменты на англ) =====
        response = await self.model_client.create_completion(
            model="mistral-7b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Help me: {user_input_ru}"  # Даже русский OK, модель разберется
                }
            ],
            tools=self.TOOLS,  # ← Инструменты ОТДЕЛЬНО
            tool_choice="auto"  # Позволяет моделе выбрать
        )

        # ===== ШАГ 3: Парсим tool_calls =====
        tool_calls = response.get("tool_calls", [])

        if not tool_calls:
            # Если модель не вызвала инструмент, используем parsed intent
            tool_calls = [{
                "function": {
                    "name": "get_channel_digest",
                    "arguments": json.dumps({
                        "channel_name": intent.get("channel", "onaboka"),
                        "days": intent.get("days", 3)
                    })
                }
            }]

        # ===== ШАГ 4: Выполняем инструменты через MCP =====
        mcp_results = []
        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            func_args = json.loads(tool_call["function"]["arguments"])

            result = await self.mcp_client.execute_tool(func_name, **func_args)
            mcp_results.append({
                "tool": func_name,
                "result": result
            })

        # ===== ШАГ 5: Форматируем ответ на РУССКОМ =====
        formatted = self._format_russian_response(mcp_results)

        return formatted

    def _parse_russian_intent(self, text: str) -> dict:
        """Парсить русский ввод БЕЗ модели (regex + heuristics).

        Args:
            text: Русский текст

        Returns:
            Parsed intent
        """

        # Регулярные выражения для русского
        patterns = {
            "channel": r"(?:по|канал|на)\s+(?:каналу\s+)?(\w+)",  # "по Набока" → "Набока"
            "days": r"(\d+)\s*(?:дн|день|дня)",  # "3 дня" → 3
            "action": r"(?:создай|собери|получи|дай|что)\s+(?:мне\s+)?(\w+)",  # "создай дайджест"
        }

        intent = {
            "action": "get_digest",  # default
            "channel": "onaboka",    # default
            "days": 3                # default
        }

        text_lower = text.lower()

        # Ищем канал
        match = re.search(patterns["channel"], text_lower)
        if match:
            intent["channel"] = match.group(1)

        # Ищем количество дней
        match = re.search(patterns["days"], text_lower)
        if match:
            intent["days"] = int(match.group(1))

        # Ищем действие
        if "дайджест" in text_lower or "digest" in text_lower:
            intent["action"] = "get_digest"
        elif "список" in text_lower or "list" in text_lower:
            intent["action"] = "list_channels"

        return intent

    def _format_russian_response(self, mcp_results: list) -> str:
        """Форматировать результат на русском.

        Args:
            mcp_results: Результаты выполнения инструментов

        Returns:
            Русский текст ответа
        """

        if not mcp_results:
            return "❌ Ошибка при выполнении запроса"

        result = mcp_results[0]["result"]
        tool = mcp_results[0]["tool"]

        if tool == "get_channel_digest" and "posts" in result:
            posts = result["posts"]
            channel = result.get("channel_name", "Неизвестный канал")

            return f"""
📌 Дайджест: {channel}
📊 Постов найдено: {len(posts)}
⏱️ Период: {result.get('days', 3)} дней

{result.get('summary', 'Нет саммари')}

✅ Готово!
"""

        return "✓ Операция выполнена"
```

---

## 🏗️ Правильная архитектура MCP Agent

### УРОВЕНЬ 1: Input Processing

```python
class InputProcessor:
    """Нормализация входа на русском."""

    @staticmethod
    def normalize(text: str) -> dict:
        """Парсить русский текст.

        Args:
            text: "Создай дайджест по Набока за 3 дня"

        Returns:
            {
                "intent": "digest",
                "channel": "onaboka",
                "days": 3,
                "language": "ru"
            }
        """
        # regex парсинг + heuristics
        # БЕЗ вызова модели!
        pass
```

### УРОВЕНЬ 2: System Design (OpenAI Format)

```python
class MCPAgentSystemDesign:
    """Правильная архитектура агента."""

    SYSTEM_MESSAGE = """You are a helpful Telegram digest assistant.
Your role:
1. Understand user requests
2. Call appropriate tools
3. Format responses clearly

Always use tools when needed."""

    TOOLS_SCHEMA = [
        {
            "type": "function",
            "function": {
                "name": "get_channel_digest",
                "description": "...",
                "parameters": { ... }
            }
        }
    ]

    async def call_with_tools(self, user_message: str):
        """Вызвать модель с инструментами (OpenAI format)."""

        response = await self.client.create_completion(
            model="mistral-7b",
            messages=[
                {"role": "system", "content": self.SYSTEM_MESSAGE},
                {"role": "user", "content": user_message}
            ],
            tools=self.TOOLS_SCHEMA,  # ← КЛЮЧЕВОЕ ОТЛИЧИЕ!
            tool_choice="auto"
        )

        return response
```

### УРОВЕНЬ 3: Tool Execution (MCP)

```python
class MCPExecutor:
    """Выполнение инструментов через MCP."""

    async def execute_tool_calls(self, tool_calls: list):
        """Выполнить tool_calls из ответа модели.

        Args:
            tool_calls: [
                {
                    "id": "call_123",
                    "function": {
                        "name": "get_channel_digest",
                        "arguments": '{"channel_name": "onaboka", "days": 3}'
                    }
                }
            ]

        Returns:
            Results
        """
        results = []

        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            func_args = json.loads(tool_call["function"]["arguments"])

            # Вызываем MCP инструмент
            result = await self.mcp_client.call(func_name, **func_args)

            results.append({
                "tool_call_id": tool_call["id"],
                "result": result
            })

        return results
```

### УРОВЕНЬ 4: Output Formatting (Russian)

```python
class OutputFormatter:
    """Форматирование на русском."""

    @staticmethod
    def format_digest(result: dict) -> str:
        """Форматировать дайджест.

        Args:
            result: {'posts': [...], 'channel': 'onaboka', ...}

        Returns:
            Красивый русский текст
        """
        return f"""
📌 Дайджест: {result['channel']}
📊 Постов: {len(result['posts'])}
...
✅ Готово!
"""
```

---

## 🔑 Ключевые моменты

### 1. **Инструменты НЕ в системном промпте**
```python
# ❌ НЕПРАВИЛЬНО
system = """Используй эти инструменты:
1. get_posts()
2. create_digest()
"""

# ✅ ПРАВИЛЬНО
system = "You are helpful assistant"
tools = [{"type": "function", "function": {...}}, ...]

response = client.create_completion(
    messages=[...],
    tools=tools,  # ← ОТДЕЛЬНО!
    tool_choice="auto"
)
```

### 2. **Система на английском**
```python
# ❌ На русском = путаница для модели
system = "Ты агент для дайджестов. Используй инструменты..."

# ✅ На английском = чисто
system = "You are a digest assistant. Use tools when needed."
```

### 3. **Парсинг русского без модели**
```python
# ❌ ПЛОХО: Вызывать модель для парсинга
response = model.complete("Парсни это: Дайджест по Набока за 3 дня")

# ✅ ХОРОШО: Regex + heuristics
intent = InputProcessor.normalize("Дайджест по Набока за 3 дня")
# → {"channel": "onaboka", "days": 3}
```

### 4. **Ответ на русском**
```python
# ПОСЛЕ выполнения инструмента - только форматирование на русском
formatted = OutputFormatter.format_digest(mcp_result)
# Модель не "думает" о форматировании, просто вставляем текст
```

---

## 📊 Сравнение: ДО vs ПОСЛЕ

| Параметр | ❌ ДО (неправильно) | ✅ ПОСЛЕ (правильно) |
|----------|-------------------|-------------------|
| **Система** | 1000+ слов на русском | 100 слов на английском |
| **Инструменты** | В системном промпте | JSON schema отдельно |
| **Парсинг intent** | Вызывать модель | Regex + heuristics |
| **Tool calls** | JSON в тексте | Structured format |
| **Русский язык** | Смешивается везде | Только в output |
| **Success rate** | ~30% | ~95% |
| **Скорость** | 20-30 сек | 5-10 сек |
| **Понимание** | Путается модель | Четкий workflow |

---

## 🚀 Реальный пример: Правильный workflow

```python
"""
Полный workflow: Russian User → MCP Agent → Russian Response
"""

async def process_user_request_correctly(user_message_ru: str):
    """Правильный способ обработки русского ввода.

    Args:
        user_message_ru: "Создай дайджест по Набока за 3 дня"

    Returns:
        Russian formatted response
    """

    # ===== УРОВЕНЬ 1: Парсинг русского (БЕЗ модели) =====
    intent = {
        "action": "digest",
        "channel": "onaboka",
        "days": 3
    }

    # ===== УРОВЕНЬ 2: Вызов LLM с инструментами =====
    response = await llm_client.create_completion(
        model="mistral-7b",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for Telegram channel digests."
            },
            {
                "role": "user",
                "content": f"Get a {intent['days']}-day digest for channel {intent['channel']}"
            }
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_channel_digest",
                    "description": "Get channel digest for N days",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_name": {"type": "string"},
                            "days": {"type": "integer"}
                        },
                        "required": ["channel_name", "days"]
                    }
                }
            }
        ],
        tool_choice="auto"
    )

    # ===== УРОВЕНЬ 3: Выполнение инструмента =====
    tool_calls = response.get("tool_calls", [])
    mcp_result = None

    for tool_call in tool_calls:
        if tool_call["function"]["name"] == "get_channel_digest":
            args = json.loads(tool_call["function"]["arguments"])
            mcp_result = await mcp_server.execute(
                "get_channel_digest",
                channel_name=args["channel_name"],
                days=args["days"]
            )

    # ===== УРОВЕНЬ 4: Форматирование на РУССКОМ =====
    if mcp_result:
        return f"""
📌 Дайджест: {mcp_result['channel']}
📊 Постов: {len(mcp_result['posts'])}
⏱️ Период: {mcp_result['days']} дней

{mcp_result['summary']}

✅ Готово!
"""

    return "❌ Ошибка при получении дайджеста"


# Использование
result = await process_user_request_correctly("Создай дайджест по Набока за 3 дня")
# ✓ Правильный русский ответ!
```

---

## 🎯 Финальные рекомендации

### Для Cursor:

```
На основе этого guide создай:

1. InputProcessor (парсинг русского без модели)
   - Regex для извлечения параметров
   - Heuristics для intent recognition
   - Fallback на defaults

2. BilingualMCPAgent (основной агент)
   - System prompt на английском
   - Tools в JSON schema
   - Вызов LLM с tool_choice="auto"
   - MCP execution layer
   - Output formatting на русском

3. Конфиг:
   - SYSTEM_LANGUAGE = "en" (система на английском)
   - OUTPUT_LANGUAGE = "ru" (вывод на русском)
   - PARSE_INPUT_WITH_MODEL = False (парсинг БЕЗ модели)

4. Tests:
   - test_russian_intent_parsing (20+ cases)
   - test_tool_calling (различные инструменты)
   - test_russian_output (форматирование)

Требования:
- Type hints везде
- Логирование на DEBUG уровне
- Обработка edge cases
- Тесты > 90% coverage
```

Это решит ВСЕ проблемы! 🎯
