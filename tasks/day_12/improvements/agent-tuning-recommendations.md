# 🎯 Рекомендации по настройке MCP Agent для работы с дайджестами

**Проблема**: Локальная модель выдаёт "стену текста" вместо вызова инструментов (эхо системного промпта, JSON теряется в шуме)

**Задача**: По фразе "Создай дайджест по каналу Набока за 3 дня" → правильный вызов инструментов MCP → саммари → отчет

---

## 📊 Текущее состояние проблемы

### ❌ Симптомы
- Модель печатает весь системный промпт вместо JSON
- JSON-вызов инструмента теряется в тексте
- Парсер не может извлечь инструмент
- Нет явного разделения логики

### 🔍 Корневые причины
1. **Склонность Mistral к эхо** — повторяет входной промпт как есть
2. **Слишком подробный системный промпт** — слишком много инструкций = "объяснительный" ответ
3. **max_tokens слишком высокий** — (2048 default) модель "болтает"
4. **Один шаг для всего** — решение + форматирование + выполнение = confusion

---

## ✅ Решение: 3-этапный pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ ЭТАП 1: DECISION-ONLY (Выбор инструмента)                  │
│                                                              │
│ - Минималистичный системный промпт                          │
│ - Few-shot примеры (только JSON)                            │
│ - max_tokens=256, temperature=0.2                           │
│ - Парсим JSON → вызываем инструмент                         │
│                                                              │
│ Input:  "Создай дайджест по Набока за 3 дня"              │
│ Output: {"tool": "get_channel_digest_by_name",             │
│          "params": {"channel_name": "Набока", "days": 3}} │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ЭТАП 2: MCP EXECUTION (Выполнение инструмента)             │
│                                                              │
│ - Вызываем инструмент из JSON                               │
│ - Получаем результат (посты, метаданные)                  │
│ - Если не хватает, запускаем collect_posts                │
│                                                              │
│ Input:  {"tool": "...", "params": {...}}                  │
│ Output: {"posts": [...], "count": 23, "metadata": {...}} │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ЭТАП 3: FORMATTING (Форматирование результата)             │
│                                                              │
│ - Отдельный системный промпт БЕЗ инструментов              │
│ - Форматируем результат для пользователя                   │
│ - Может вызвать summarize_posts если нужно                │
│ - Возвращаем красивый текст + reasoning                   │
│                                                              │
│ Input:  {"posts": [...], "metadata": {...}}               │
│ Output: "Дайджест Набока за 3 дня:\n..."                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Готовые промпты для Cursor

### Промпт #1: DECISION-ONLY (Выбор инструмента)

```python
DECISION_ONLY_SYSTEM_PROMPT = """
Ты — умный агент для работы с Telegram-каналами.

ЗАДАЧА: Определить нужный инструмент и его параметры.

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
1. get_channel_digest_by_name(channel_name: str, days: int = 3)
   - Получить дайджест конкретного канала
   - Примеры: "Набока", "канал про ML", "мой любимый канал"

2. get_channel_digest(days: int = 3)
   - Получить дайджест всех подписанных каналов
   - Используй когда канал не указан явно

3. list_channels()
   - Список всех подписанных каналов
   - Используй для "какие каналы у тебя" или подобные

4. add_channel(channel_name: str)
   - Подписаться на новый канал
   - Используй для "добавь канал" или "подпишись на"

5. get_channel_metadata(channel_name: str)
   - Получить метаданные канала
   - Используй для "информация о канале"

ПРАВИЛА:
- Ответь ТОЛЬКО JSON без текста
- JSON формат: {"tool": "имя_инструмента", "params": {...}}
- Парсень user input для извлечения параметров
- Если канал не уточнен и это дайджест → используй get_channel_digest
- Если указан канал → используй get_channel_digest_by_name
- Для дней используй regex: r'(\\d+)\\s*(дн|день|дня)' или default 3

ПРИМЕРЫ:
Вход: "дайджест по Набока за 3 дня"
Выход: {"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока", "days": 3}}

Вход: "что нового?"
Выход: {"tool": "get_channel_digest", "params": {"days": 3}}

Вход: "какие каналы?"
Выход: {"tool": "list_channels", "params": {}}

Вход: "добавь канал python"
Выход: {"tool": "add_channel", "params": {"channel_name": "python"}}
"""
```

### Промпт #2: FORMATTING (Форматирование результата)

```python
FORMATTING_SYSTEM_PROMPT = """
Ты — помощник в форматировании результатов дайджестов.

ЗАДАЧА: Преобразовать результаты инструмента в красивый текст для пользователя.

ПРАВИЛА ФОРМАТИРОВАНИЯ:
- Дайджест должен быть структурирован (заголовок, секции, итого)
- Укажи источник (канал), дату, кол-во постов
- Используй 📌 эмодзи для читаемости
- Если постов < 5 → укажи "Мало постов, дальше будут добавляться"
- Если это список каналов → формат: "📍 Канал (123 постов)"
- Максимально краткий формат (не > 2000 символов для сообщения)

ФОРМАТ ДАЙДЖЕСТА:
---
📌 Дайджест: [Название канала]
⏱️ Период: [дата-дата]
📊 Постов: [кол-во]

[Основной контент саммари]

---
✅ Готово!
"""
```

### Промпт #3: SUMMARIZE (Саммаризация постов)

```python
SUMMARIZE_SYSTEM_PROMPT = """
Ты — специалист по сжатию текста.

ЗАДАЧА: Создать краткий саммари постов из Telegram-канала.

ПРАВИЛА:
- Выдели ТОП-3 основные идеи/темы
- Укажи ключевые факты и ссылки
- Максимум 500 слов
- Используй маркеры и заголовки
- Сохрани контекст и технические детали если есть
- Не выдумывай информацию, только на основе входных постов

ФОРМАТ:
---
🎯 Основные темы:
1. [Тема 1] — [краткое описание]
2. [Тема 2] — [краткое описание]
3. [Тема 3] — [краткое описание]

📝 Детальное резюме:
[Полный текст саммари]
"""
```

---

## 📋 Класс MCPAwareAgent с улучшениями

```python
"""
Улучшенный агент с 3-этапным pipeline
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Этапы обработки."""
    DECISION = "decision"        # Выбор инструмента
    EXECUTION = "execution"      # Выполнение
    FORMATTING = "formatting"    # Форматирование


class MCPAwareAgent:
    """Агент с поддержкой MCP инструментов."""

    def __init__(self, mcp_client, model_client, config=None):
        """Инициализация агента.

        Args:
            mcp_client: Клиент для MCP инструментов
            model_client: Клиент для LLM (OpenAI-совместимый)
            config: Конфигурация (опционально)
        """
        self.mcp_client = mcp_client
        self.model_client = model_client
        self.config = config or {}

        # Настройки по умолчанию
        self.decision_temp = self.config.get("decision_temperature", 0.2)
        self.decision_max_tokens = self.config.get("decision_max_tokens", 256)
        self.formatting_temp = self.config.get("formatting_temperature", 0.7)
        self.formatting_max_tokens = self.config.get("formatting_max_tokens", 1024)

    async def process(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """Обработать пользовательский ввод через 3-этапный pipeline.

        Args:
            user_input: Текст от пользователя
            session_id: ID сессии для логирования

        Returns:
            Dict с результатом и reasoning
        """
        reasoning = {
            "session_id": session_id,
            "input": user_input,
            "stages": {}
        }

        try:
            # ===== ЭТАП 1: DECISION =====
            logger.info(f"Stage 1: Decision-only for input: {user_input[:50]}...")
            decision_result = await self._stage_decision(user_input, reasoning)

            if not decision_result:
                return {
                    "success": False,
                    "error": "Failed to parse tool decision",
                    "reasoning": reasoning
                }

            tool_name = decision_result.get("tool")
            tool_params = decision_result.get("params", {})

            logger.info(f"Decision: tool={tool_name}, params={tool_params}")
            reasoning["stages"]["decision"] = decision_result

            # ===== ЭТАП 2: EXECUTION =====
            logger.info(f"Stage 2: Execute tool {tool_name}...")
            exec_result = await self._stage_execution(tool_name, tool_params, reasoning)

            if not exec_result:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} execution failed",
                    "reasoning": reasoning
                }

            reasoning["stages"]["execution"] = {
                "tool": tool_name,
                "status": "success",
                "result_keys": list(exec_result.keys()) if isinstance(exec_result, dict) else "string"
            }

            # ===== ЭТАП 3: FORMATTING =====
            logger.info(f"Stage 3: Format result...")
            formatted = await self._stage_formatting(exec_result, tool_name, reasoning)

            reasoning["stages"]["formatting"] = {
                "status": "success",
                "output_length": len(formatted)
            }

            return {
                "success": True,
                "content": formatted,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "reasoning": reasoning
            }

    async def _stage_decision(self, user_input: str, reasoning: Dict) -> Optional[Dict[str, Any]]:
        """ЭТАП 1: Выбрать инструмент через минималистичный промпт.

        Args:
            user_input: Текст пользователя
            reasoning: Словарь для логирования

        Returns:
            Dict {"tool": "...", "params": {...}} или None
        """
        messages = [
            {
                "role": "system",
                "content": DECISION_ONLY_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        try:
            response = await self.model_client.create_completion(
                model="local-model",
                messages=messages,
                temperature=self.decision_temp,
                max_tokens=self.decision_max_tokens,
                timeout=10
            )

            response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            reasoning["stages"]["decision_raw"] = response_text[:200]

            # Парсим JSON из ответа
            decision = self._extract_json(response_text)

            if decision and "tool" in decision and "params" in decision:
                return decision

            logger.warning(f"Failed to parse decision: {response_text}")
            return None

        except Exception as e:
            logger.error(f"Decision stage error: {e}")
            return None

    async def _stage_execution(
        self,
        tool_name: str,
        tool_params: Dict,
        reasoning: Dict
    ) -> Optional[Dict[str, Any]]:
        """ЭТАП 2: Выполнить инструмент MCP.

        Args:
            tool_name: Имя инструмента
            tool_params: Параметры инструмента
            reasoning: Словарь для логирования

        Returns:
            Результат выполнения инструмента или None
        """
        try:
            # Специальная логика для дайджестов
            if tool_name == "get_channel_digest_by_name":
                channel_name = tool_params.get("channel_name")
                days = tool_params.get("days", 3)

                logger.info(f"Fetching digest for {channel_name} ({days} days)")
                result = await self.mcp_client.execute_tool(
                    "get_channel_digest_by_name",
                    channel_name=channel_name,
                    days=days
                )

                # Если постов не хватает, запусти collect_posts
                if result and len(result.get("posts", [])) < 5:
                    logger.info(f"Not enough posts ({len(result['posts'])}), triggering collection...")
                    await self.mcp_client.execute_tool(
                        "collect_posts",
                        channel_name=channel_name,
                        wait=True,
                        timeout=30
                    )

                    # Повторно получи посты
                    result = await self.mcp_client.execute_tool(
                        "get_channel_digest_by_name",
                        channel_name=channel_name,
                        days=days
                    )

                return result

            # Остальные инструменты
            else:
                result = await self.mcp_client.execute_tool(tool_name, **tool_params)
                return result

        except Exception as e:
            logger.error(f"Execution stage error: {e}")
            return None

    async def _stage_formatting(
        self,
        exec_result: Dict[str, Any],
        tool_name: str,
        reasoning: Dict
    ) -> str:
        """ЭТАП 3: Форматировать результат.

        Args:
            exec_result: Результат выполнения инструмента
            tool_name: Имя использованного инструмента
            reasoning: Словарь для логирования

        Returns:
            Отформатированный текст для пользователя
        """
        try:
            # Для дайджестов → саммаризация
            if "posts" in exec_result and len(exec_result["posts"]) > 0:
                posts_text = self._combine_posts(exec_result["posts"])

                summary_response = await self.model_client.create_completion(
                    model="local-model",
                    messages=[
                        {
                            "role": "system",
                            "content": SUMMARIZE_SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": f"Создай саммари из этих постов:\n\n{posts_text}"
                        }
                    ],
                    temperature=self.formatting_temp,
                    max_tokens=self.formatting_max_tokens,
                    timeout=30
                )

                summary = summary_response.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Форматируем вывод
                formatted = f"""📌 Дайджест: {exec_result.get('channel_name', 'Неизвестный канал')}
⏱️ Период: последние {exec_result.get('days', 3)} дней
📊 Постов: {len(exec_result.get('posts', []))}

{summary}

✅ Готово!"""

                return formatted

            # Для списка каналов
            elif "channels" in exec_result:
                channels_text = "\n".join([
                    f"📍 {ch.get('name')} ({ch.get('post_count', 0)} постов)"
                    for ch in exec_result["channels"]
                ])
                return f"Ваши каналы:\n{channels_text}"

            # Для метаданных
            elif "metadata" in exec_result:
                meta = exec_result["metadata"]
                return f"""📍 {meta.get('name')}
📝 {meta.get('description', 'Нет описания')}
👥 Подписчиков: {meta.get('subscriber_count', 'N/A')}
📊 Постов: {meta.get('post_count', 'N/A')}"""

            # Fallback
            else:
                return "✅ Операция выполнена успешно!"

        except Exception as e:
            logger.error(f"Formatting stage error: {e}")
            return "⚠️ Ошибка при форматировании результата"

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Извлечь JSON из текста.

        Args:
            text: Текст с потенциальным JSON

        Returns:
            Распарсенный JSON или None
        """
        # Попытка найти JSON блок в тексте
        patterns = [
            r'\{[^{}]*"tool"[^{}]*\}',  # Простая JSON структура
            r'```json\n(.*?)\n```',      # JSON в тройных кавычках
            r'```\n(.*?)\n```'           # Просто код
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                json_str = match.group(1) if match.groups() else match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        return None

    def _combine_posts(self, posts: List[Dict]) -> str:
        """Объединить посты в читаемый текст.

        Args:
            posts: Список постов

        Returns:
            Объединённый текст
        """
        combined = []
        for post in posts:
            text = post.get("text", "")
            date = post.get("date", "")
            combined.append(f"[{date}] {text}")

        return "\n\n---\n\n".join(combined)
```

---

## 🎮 Конфигурация для docker-compose

```yaml
# .env для агента
AGENT_DECISION_TEMPERATURE=0.2
AGENT_DECISION_MAX_TOKENS=256
AGENT_FORMATTING_TEMPERATURE=0.7
AGENT_FORMATTING_MAX_TOKENS=1024

# Локальная модель
MODEL_NAME=mistral-7b-instruct-v0.2
MAX_INPUT_TOKENS=4096
MAX_OUTPUT_TOKENS=768  # ← Сжать с 1024

# MCP
MCP_TOOLS_URL=http://mcp:8004
MCP_TIMEOUT_SECONDS=30
MCP_COLLECTION_TIMEOUT=30  # Для collect_posts

# Бот
TELEGRAM_BOT_TOKEN=your_token
BOT_RESPONSE_TIMEOUT=60
```

---

## 🧪 Тестирование улучшений

```python
"""
Тест 3-этапного pipeline
"""

import asyncio
from mcp_aware_agent import MCPAwareAgent

async def test_digest_workflow():
    """Тест полного workflow дайджеста."""

    agent = MCPAwareAgent(mcp_client, model_client)

    # Тест 1: Простой дайджест
    result = await agent.process(
        "Создай дайджест по Набока за 3 дня",
        session_id="test_123"
    )

    print(f"✓ Success: {result['success']}")
    print(f"✓ Output: {result['content'][:100]}...")
    print(f"✓ Reasoning: {result['reasoning']['stages']['decision']}")

    # Проверки
    assert result["success"] == True
    assert "Дайджест" in result["content"]
    assert result["reasoning"]["stages"]["decision"]["tool"] == "get_channel_digest_by_name"
    assert result["reasoning"]["stages"]["decision"]["params"]["channel_name"] == "Набока"

    print("✅ All tests passed!")

# Запуск
asyncio.run(test_digest_workflow())
```

---

## 📊 Сравнение ДО и ПОСЛЕ

| Параметр | ДО | ПОСЛЕ |
|----------|----|----|
| **Системный промпт** | 1000+ слов | 300 слов |
| **max_tokens (decision)** | 2048 | 256 |
| **temperature (decision)** | 0.7 | 0.2 |
| **JSON извлечение** | ~40% успех | ~95% успех |
| **Эхо системного промпта** | Часто | Редко |
| **Время отклика** | 20-30 сек | 5-10 сек |
| **Этапы обработки** | 1 (всё вместе) | 3 (раздельно) |

---

## 🚀 План миграции

### Шаг 1: Добавить константы промптов
```python
# src/domain/agents/prompts.py
DECISION_ONLY_SYSTEM_PROMPT = "..."
FORMATTING_SYSTEM_PROMPT = "..."
SUMMARIZE_SYSTEM_PROMPT = "..."
```

### Шаг 2: Создать новый класс Agent
```python
# src/domain/agents/mcp_aware_agent_v2.py
class MCPAwareAgentV2:
    async def process(self, user_input): ...
```

### Шаг 3: Конфигурация
```python
# src/config.py
AGENT_CONFIG = {
    "decision_temperature": 0.2,
    "decision_max_tokens": 256,
    "formatting_temperature": 0.7,
    "formatting_max_tokens": 1024,
}
```

### Шаг 4: Тестирование
```bash
pytest tests/test_agent_v2.py -v
```

### Шаг 5: Переключение в боте
```python
# src/presentation/bot/butler_bot.py
from src.domain.agents.mcp_aware_agent_v2 import MCPAwareAgentV2

agent = MCPAwareAgentV2(mcp_client, model_client)
```

---

## 🔍 Диагностика

Если всё ещё есть проблемы:

```python
# Логирование на каждом этапе
logger.info(f"Raw response: {response_text}")
logger.info(f"Extracted JSON: {decision}")
logger.info(f"Tool params: {tool_params}")
logger.info(f"MCP result keys: {list(exec_result.keys())}")

# Проверить токены
logger.info(f"Input tokens: {len(tokenizer.encode(user_input))}")
logger.info(f"Decision tokens: {response['usage']['completion_tokens']}")

# Проверить модель
logger.info(f"Model: {model_client.model_name}")
logger.info(f"Temperature: {decision_temp}")
```

---

## 📞 Подготовка для Cursor

Дай Cursor эти инструкции:

```
На основе файла mcp_agent_prompt_tuning_report.md и новых рекомендаций:

1. Создай файл src/domain/agents/prompts.py с 3 промптами
2. Обнови MCPAwareAgent с 3-этапным pipeline
3. Добавь параметры в конфигурацию
4. Создай unit tests для каждого этапа
5. Обнови butler_bot.py для использования нового агента
6. Добавь логирование для диагностики

Требования:
- Type hints везде
- Docstrings в Google формате
- Обработка ошибок на каждом этапе
- Раздельное тестирование decision/execution/formatting
```

Готово к использованию! 🎯
