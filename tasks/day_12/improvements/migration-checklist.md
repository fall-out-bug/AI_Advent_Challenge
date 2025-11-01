# ✅ Чеклист: Миграция с неправильной архитектуры на правильную

**Текущая проблема:** "Стена текста", путаница с языками, JSON теряется

**Цель:** Правильная архитектура с OpenAI Function Calling format

**Время:** 3-4 часа на реализацию + 1 час на тесты

---

## 📋 ПРЕ-РЕКВИЗИТЫ (проверить сейчас)

- [ ] У тебя есть локальная Mistral-7B (или совместимая)
- [ ] OpenAI-совместимый API `/v1/chat/completions` работает
- [ ] MCP сервер с инструментами доступен
- [ ] Telegram бот связан с агентом

---

## ЭТАП 1: Анализ текущего кода (30 мин)

### 1.1 Открыть `src/domain/agents/mcp_aware_agent.py`

- [ ] Найти где передаются инструменты моделе
  - Они в `system_prompt`? → **ПРОБЛЕМА**
  - Они отдельным параметром `tools=`? → **OK**

- [ ] Проверить язык:
  ```python
  # Если видишь это:
  system = "Ты агент. Используй эти инструменты: ..."
  # → ЭТО ПРОБЛЕМА (русский в системном промпте)
  
  # Должно быть:
  system = "You are a helpful assistant."  # EN только
  tools = [...]  # JSON отдельно
  ```

- [ ] Найти парсинг ответа модели
  - Ищешь JSON в "стене текста"? → **ПРОБЛЕМА**
  - Используешь `tool_calls` из ответа? → **OK**

### 1.2 Проверить MCP конфиг

- [ ] Где находится MCP сервер?
  ```bash
  curl http://localhost:8004/health
  # Должен вернуть 200
  ```

- [ ] Какие инструменты доступны?
  ```bash
  curl http://localhost:8004/tools
  # Должен вернуть список с описаниями
  ```

### 1.3 Создать список всех инструментов

```python
# Напиши на листочке/в файле:
AVAILABLE_TOOLS = [
    {
        "name": "get_channel_digest_by_name",
        "params": ["channel_name: str", "days: int"],
        "description": "Get digest for specific channel"
    },
    {
        "name": "list_channels",
        "params": [],
        "description": "List all subscribed channels"
    },
    # ... остальные
]
```

---

## ЭТАП 2: Создание новых файлов (1.5 часа)

### 2.1 Создать `src/domain/agents/tools_registry.py`

```python
# ФАЙЛ: src/domain/agents/tools_registry.py

"""MCP Tools Registry - JSON Schema for OpenAI Function Calling"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_channel_digest_by_name",
            "description": "Get digest of posts from specific Telegram channel for N days",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {
                        "type": "string",
                        "description": "Channel name (e.g., 'onaboka', 'pythonru')",
                        "minLength": 1,
                        "maxLength": 100
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (1-30)",
                        "minimum": 1,
                        "maximum": 30
                    }
                },
                "required": ["channel_name", "days"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_channels",
            "description": "List all subscribed Telegram channels",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_channel_metadata",
            "description": "Get information about a specific channel",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {
                        "type": "string",
                        "description": "Channel name"
                    }
                },
                "required": ["channel_name"]
            }
        }
    },
    # ... добавить остальные инструменты
]
```

**Чек-лист:**
- [ ] JSON валиден (скопировать в https://jsonlint.com/)
- [ ] Все параметры описаны
- [ ] Есть `minLength`, `maximum` где нужно
- [ ] Примеры в `description` (e.g., ...)

### 2.2 Создать `src/domain/input_processing/russian_parser.py`

```python
# ФАЙЛ: src/domain/input_processing/russian_parser.py

"""Russian input parsing WITHOUT calling LLM"""

import re
from typing import Optional, Dict, Any

class RussianInputParser:
    """Parse Russian user input using regex + heuristics."""
    
    @staticmethod
    def parse_digest_request(text: str) -> Optional[Dict[str, Any]]:
        """Parse "дайджест по ХХ за N дней" format.
        
        Args:
            text: "Создай дайджест по Набока за 3 дня"
            
        Returns:
            {"channel": "onaboka", "days": 3, "action": "digest"}
        """
        text_lower = text.lower()
        
        # Ищем канал: "по Набока", "по каналу Набока", "Набока"
        channel_match = re.search(
            r'(?:по|канал)\s+(?:каналу\s+)?([а-яa-z0-9_]+)',
            text_lower
        )
        channel = channel_match.group(1) if channel_match else None
        
        # Ищем дни: "3 дня", "за 7 дней"
        days_match = re.search(r'(\d+)\s*(?:дн|день|дня)', text_lower)
        days = int(days_match.group(1)) if days_match else 3
        
        if not channel:
            return None
        
        return {
            "action": "digest",
            "channel": channel,
            "days": days
        }
    
    @staticmethod
    def parse_list_request(text: str) -> bool:
        """Проверить если это запрос на список каналов."""
        keywords = ["список", "какие", "каналы", "подписан", "all channels"]
        return any(kw in text.lower() for kw in keywords)
    
    @staticmethod
    def normalize_channel_name(channel: str) -> str:
        """Нормализовать название канала.
        
        "Набока" → "onaboka"
        "python" → "pythonru"
        """
        # Маппинг известных каналов
        channel_map = {
            "набока": "onaboka",
            "python": "pythonru",
            # ... добавить остальные
        }
        
        return channel_map.get(channel.lower(), channel)
```

**Чек-лист:**
- [ ] Regex правильный (тест на 5+ примерах)
- [ ] Fallback на defaults
- [ ] Канал нормализуется правильно

### 2.3 Обновить `src/domain/agents/mcp_aware_agent.py`

```python
# ИЗМЕНЕНИЯ В: src/domain/agents/mcp_aware_agent.py

from src.domain.agents.tools_registry import TOOLS_SCHEMA
from src.domain.input_processing.russian_parser import RussianInputParser

class MCPAwareAgent:
    """Правильный MCP Agent с OpenAI Function Calling."""
    
    # ===== СИСТЕМА ТОЛЬКО НА АНГЛИЙСКОМ! =====
    SYSTEM_PROMPT = """You are a helpful Telegram digest assistant.
Your role is to:
1. Understand user requests about Telegram channel digests
2. Use provided tools to fetch data
3. Format responses clearly

Always use tools when appropriate. Respond in the language of the user input."""
    
    def __init__(self, mcp_client, model_client):
        self.mcp_client = mcp_client
        self.model_client = model_client
    
    async def process(self, user_input: str) -> Dict[str, Any]:
        """Обработать запрос пользователя.
        
        Args:
            user_input: "Создай дайджест по Набока за 3 дня"
            
        Returns:
            {"response": "...", "reasoning": {...}}
        """
        
        # ===== УРОВЕНЬ 1: Парсинг русского БЕЗ модели =====
        # Это может помочь моделе если что-то пойдет не так
        parsed_intent = self._parse_user_intent(user_input)
        
        # ===== УРОВЕНЬ 2: Вызов LLM с инструментами =====
        response = await self.model_client.create_completion(
            model="mistral-7b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_input  # Русский или английский - модель разберется
                }
            ],
            tools=TOOLS_SCHEMA,  # ← ЭТО КЛЮЧЕВОЕ ОТЛИЧИЕ!
            tool_choice="auto"
        )
        
        # ===== УРОВЕНЬ 3: Парсим tool_calls =====
        tool_calls = response.get("tool_calls", [])
        
        if not tool_calls and parsed_intent:
            # Fallback: если модель не вызвала инструмент, используем parsed
            tool_calls = [
                self._create_tool_call(parsed_intent)
            ]
        
        # ===== УРОВЕНЬ 4: Выполняем инструменты =====
        mcp_results = []
        for tool_call in tool_calls:
            result = await self._execute_tool_call(tool_call)
            mcp_results.append(result)
        
        # ===== УРОВЕНЬ 5: Форматируем на РУССКОМ =====
        formatted_response = self._format_response_russian(mcp_results, user_input)
        
        return {
            "response": formatted_response,
            "reasoning": {
                "parsed_intent": parsed_intent,
                "tool_calls": tool_calls,
                "mcp_results_count": len(mcp_results)
            }
        }
    
    def _parse_user_intent(self, user_input: str) -> Optional[Dict]:
        """Парсить русский ввод БЕЗ модели."""
        if RussianInputParser.parse_list_request(user_input):
            return {"action": "list_channels"}
        
        digest = RussianInputParser.parse_digest_request(user_input)
        if digest:
            digest["channel"] = RussianInputParser.normalize_channel_name(digest["channel"])
            return digest
        
        return None
    
    def _create_tool_call(self, intent: Dict) -> Dict:
        """Создать tool_call из parsed intent."""
        if intent["action"] == "digest":
            return {
                "id": "fallback_1",
                "type": "function",
                "function": {
                    "name": "get_channel_digest_by_name",
                    "arguments": json.dumps({
                        "channel_name": intent["channel"],
                        "days": intent["days"]
                    })
                }
            }
        # ... остальные cases
    
    async def _execute_tool_call(self, tool_call: Dict) -> Dict:
        """Выполнить tool_call через MCP."""
        func_name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])
        
        result = await self.mcp_client.execute_tool(func_name, **args)
        
        return {
            "tool": func_name,
            "result": result,
            "success": True
        }
    
    def _format_response_russian(self, results: list, user_input: str) -> str:
        """Форматировать результат на РУССКОМ."""
        if not results:
            return "❌ Ошибка при выполнении запроса"
        
        result = results[0]["result"]
        
        if "posts" in result:
            posts = result["posts"]
            channel = result.get("channel_name", "Неизвестный канал")
            summary = result.get("summary", "Нет саммари")
            
            return f"""📌 Дайджест: {channel}
📊 Постов: {len(posts)}
⏱️ Период: {result.get('days', 3)} дней

{summary}

✅ Готово!"""
        
        return "✓ Операция выполнена успешно"
```

**Чек-лист:**
- [ ] SYSTEM_PROMPT на английском (максимум 200 слов)
- [ ] Используется `tools=TOOLS_SCHEMA`
- [ ] Парсинг русского БЕЗ вызова модели
- [ ] Fallback на parsed intent
- [ ] Форматирование результата на русском

---

## ЭТАП 3: Обновить конфигурацию (30 мин)

### 3.1 Обновить `.env` или `config.yml`

```env
# Agent settings
AGENT_SYSTEM_LANGUAGE=en          # ← Система на английском!
AGENT_OUTPUT_LANGUAGE=ru          # ← Вывод на русском
AGENT_TEMPERATURE=0.2             # ← Низкая (более детерминированно)
AGENT_MAX_TOKENS=256              # ← Низкий (не болтает)

# LLM
LLM_MODEL=mistral-7b-instruct
LLM_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=any_key

# MCP
MCP_BASE_URL=http://localhost:8004
MCP_TIMEOUT=30

# Parsing
PARSER_STRICT_MODE=False          # ← Использовать fallbacks
PARSER_MAX_ATTEMPTS=3
```

**Чек-лист:**
- [ ] Все значения корректные
- [ ] SYSTEM_LANGUAGE = "en" обязательно
- [ ] MCP доступен на указанном URL

---

## ЭТАП 4: Создать тесты (45 мин)

### 4.1 Файл `tests/test_russian_parser.py`

```python
import pytest
from src.domain.input_processing.russian_parser import RussianInputParser

class TestRussianParser:
    """Тесты для парсера русского ввода."""
    
    def test_digest_request_basic(self):
        result = RussianInputParser.parse_digest_request(
            "Создай дайджест по Набока за 3 дня"
        )
        assert result["channel"] == "onaboka"
        assert result["days"] == 3
    
    def test_digest_request_variants(self):
        variants = [
            "дайджест по Набока",
            "получи дайджест по Набока за 5 дней",
            "по каналу Набока за 2 дня",
        ]
        for variant in variants:
            result = RussianInputParser.parse_digest_request(variant)
            assert result is not None
            assert "channel" in result
    
    def test_list_channels_detection(self):
        variants = ["какие каналы", "список", "мои каналы"]
        for variant in variants:
            assert RussianInputParser.parse_list_request(variant)
    
    # ... 10+ еще тестов
```

**Чек-лист:**
- [ ] 15+ unit тестов написано
- [ ] Все варианты русского ввода покрыты
- [ ] Edge cases (пустой ввод, только цифры и т.д.)

### 4.2 Файл `tests/test_agent_integration.py`

```python
import pytest
from src.domain.agents.mcp_aware_agent import MCPAwareAgent

@pytest.mark.asyncio
async def test_agent_digest_workflow():
    """Full workflow: Russian input → Tools → Russian output."""
    
    agent = MCPAwareAgent(mock_mcp_client, mock_model_client)
    
    result = await agent.process("Создай дайджест по Набока за 3 дня")
    
    assert result["response"] is not None
    assert "Дайджест" in result["response"]
    assert "Готово" in result["response"]
    assert result["reasoning"]["tool_calls"] is not None

# ... 5+ integration тестов
```

**Чек-лист:**
- [ ] 5+ integration тестов
- [ ] Все critical workflows покрыты

---

## ЭТАП 5: Развертывание (1 час)

### 5.1 Перед запуском проверить

```bash
# ✓ Health checks
curl http://localhost:8000/health          # LLM API
curl http://localhost:8004/health          # MCP Server

# ✓ Tools available
curl http://localhost:8004/tools

# ✓ Запустить тесты
pytest tests/test_russian_parser.py -v
pytest tests/test_agent_integration.py -v
```

### 5.2 Запустить агента

```python
import asyncio
from src.domain.agents.mcp_aware_agent import MCPAwareAgent

async def main():
    agent = MCPAwareAgent(mcp_client, model_client)
    
    result = await agent.process("Создай дайджест по Набока за 3 дня")
    
    print(result["response"])
    print(f"\n📊 Reasoning: {result['reasoning']}")

asyncio.run(main())
```

### 5.3 Проверить результат

```
✓ Модель НЕ выдает системный промпт?
✓ JSON из tool_calls четкий?
✓ Нет "стены текста"?
✓ Русский ответ красивый?
✓ Инструменты вызваны правильно?
```

**Чек-лист:**
- [ ] Все checks пройдены
- [ ] Логи показывают правильное выполнение
- [ ] Временное решение на отладку включено (если нужно)

---

## ЭТАП 6: Мониторинг и улучшения (текущий)

### 6.1 Логирование для диагностики

```python
# Добавить это в agent.py
logger.debug(f"System prompt language: EN")
logger.debug(f"Tools schema: {len(TOOLS_SCHEMA)} tools")
logger.debug(f"Parsed intent: {parsed_intent}")
logger.debug(f"Tool calls count: {len(tool_calls)}")
logger.debug(f"LLM response time: {response_time}ms")
logger.debug(f"MCP execution time: {mcp_time}ms")
```

### 6.2 Метрики

- [ ] Success rate tool_calls: target > 95%
- [ ] Response time: target < 10 sec
- [ ] Error rate: target < 5%

---

## 🎯 ФИНАЛЬНЫЙ ЧЕКЛИСТ ПЕРЕД КОММИТОМ

- [ ] Все файлы созданы/обновлены
- [ ] Тесты > 90% pass
- [ ] Нет ошибок в логах
- [ ] Русский ввод обрабатывается
- [ ] JSON чистый (не в тексте)
- [ ] Форматирование на русском работает
- [ ] MCP инструменты вызываются
- [ ] Система НА АНГЛИЙСКОМ
- [ ] Нет эхо системного промпта
- [ ] Документация обновлена

---

## ⏱️ ИТОГО ВРЕМЯ

- Анализ: 30 мин
- Реализация: 1.5 часа
- Тесты: 45 мин
- Развертывание: 1 час
- Отладка/мониторинг: 30 мин

**ИТОГО: ~4 часа на полную миграцию**

---

## 📞 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

1. Проверить логи → `tail -f logs/agent.log`
2. Убедиться что SYSTEM_LANGUAGE="en"
3. Проверить что `tools=TOOLS_SCHEMA` передается
4. Запустить тесты → `pytest -v`
5. Отключить MCP, использовать mock → проверить парсер
6. Включить DEBUG логирование → смотреть каждый шаг

**Главное:** Русский язык ТОЛЬКО в вводе и выводе. Система, инструменты и логика = английский!
