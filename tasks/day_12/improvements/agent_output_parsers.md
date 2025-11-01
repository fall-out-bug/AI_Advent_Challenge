# 🔧 Парсеры и обработчики для Agent Output

Практические примеры для извлечения JSON из "стены текста" модели.

---

## Проблема: Model Output Parsing

Mistral часто выдаёт такое:

```
Хорошо, я помогу тебе создать дайджест по каналу Набока.

Я использую инструмент для получения последних постов:
{
  "tool": "get_channel_digest_by_name",
  "params": {
    "channel_name": "Набока",
    "days": 3
  }
}

Это должно вернуть мне все посты из канала...
```

**Задача**: Извлечь JSON из этого текста.

---

## ✅ Решение 1: Robust JSON Parser

```python
"""
Надежный парсер JSON из текста модели
"""

import json
import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Извлечь JSON из текста модели.
    
    Пытается несколько стратегий в порядке приоритета:
    1. Прямой парсинг JSON (если весь ответ — JSON)
    2. JSON в тройных кавычках (```json ... ```)
    3. JSON-блок в фигурных скобках (от первой { до последней })
    4. Multiline JSON (с переносами)
    
    Args:
        text: Текст с потенциальным JSON
        
    Returns:
        Распарсенный JSON или None
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # ===== Стратегия 1: Прямой парсинг =====
    try:
        result = json.loads(text)
        logger.debug(f"✓ Direct JSON parse successful")
        return result
    except json.JSONDecodeError:
        pass
    
    # ===== Стратегия 2: JSON в тройных кавычках =====
    # Ищем ```json ... ``` или просто ``` ... ```
    patterns_triple = [
        r'```json\s*\n(.*?)\n```',   # ```json
        r'```\s*\n(.*?)\n```',        # просто ```
        r'```(.*?)```'                # без новых строк
    ]
    
    for pattern in patterns_triple:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            json_str = match.group(1).strip()
            try:
                result = json.loads(json_str)
                logger.debug(f"✓ JSON from triple-quotes parse successful")
                return result
            except json.JSONDecodeError:
                logger.debug(f"Failed to parse from triple-quotes: {json_str[:50]}")
                continue
    
    # ===== Стратегия 3: JSON-блок (от { до }) =====
    # Находим все {...} блоки и пробуем парсить
    brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.finditer(brace_pattern, text)
    
    for match in matches:
        json_str = match.group(0)
        try:
            result = json.loads(json_str)
            
            # Проверяем что это похоже на инструмент
            if "tool" in result or "params" in result:
                logger.debug(f"✓ JSON from braces parse successful")
                return result
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse from braces: {json_str[:50]}")
            continue
    
    # ===== Стратегия 4: Multiline JSON =====
    # Просто берем от первой { до последней }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        json_str = text[first_brace:last_brace + 1]
        try:
            result = json.loads(json_str)
            logger.debug(f"✓ JSON from multiline parse successful")
            return result
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse multiline JSON: {json_str[:50]}")
    
    logger.warning(f"Could not extract JSON from text: {text[:100]}")
    return None


def extract_and_validate(
    text: str,
    required_fields: List[str] = None,
    allow_empty_params: bool = False
) -> Optional[Dict[str, Any]]:
    """Извлечь JSON и проверить что он валиден.
    
    Args:
        text: Текст для парсинга
        required_fields: Обязательные поля в JSON
        allow_empty_params: Разрешить пустые параметры
        
    Returns:
        Валиданный JSON или None
    """
    required_fields = required_fields or ["tool", "params"]
    
    json_data = extract_json_from_text(text)
    
    if not json_data:
        return None
    
    # Проверяем обязательные поля
    for field in required_fields:
        if field not in json_data:
            logger.warning(f"Missing required field: {field}")
            return None
    
    # Проверяем что params не None
    if not allow_empty_params and json_data.get("params") is None:
        logger.warning("params field is None")
        return None
    
    return json_data


# ===== Тесты парсера =====

def test_json_extraction():
    """Тест парсера на реальных примерах."""
    
    test_cases = [
        # Прямой JSON
        (
            '{"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока"}}',
            {"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока"}}
        ),
        # JSON в тройных кавычках
        (
            '''Хорошо, вот JSON:
```json
{"tool": "list_channels", "params": {}}
```
Это поможет...''',
            {"tool": "list_channels", "params": {}}
        ),
        # JSON в тексте
        (
            '''Я используя инструмент:
{"tool": "add_channel", "params": {"channel_name": "python"}}
Это подпишет вас на канал...''',
            {"tool": "add_channel", "params": {"channel_name": "python"}}
        ),
        # Multiline JSON
        (
            '''{
  "tool": "get_channel_digest_by_name",
  "params": {
    "channel_name": "Набока",
    "days": 3
  }
}''',
            {"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока", "days": 3}}
        ),
    ]
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = extract_json_from_text(input_text)
        assert result == expected, f"Test {i} failed: {result} != {expected}"
        print(f"✓ Test {i} passed")
    
    print(f"\n✅ All {len(test_cases)} tests passed!")
```

---

## ✅ Решение 2: Fallback Parser (когда JSON не находится)

```python
"""
Fallback парсер: если JSON не найден, использовать regex + heuristics
"""

import re
from typing import Optional, Dict, Any


def extract_tool_from_text_heuristic(text: str) -> Optional[Dict[str, Any]]:
    """Попытка извлечь инструмент из текста используя heuristics.
    
    Если JSON парсинг не сработал, используем регулярные выражения
    для извлечения инструмента и параметров.
    
    Args:
        text: Текст модели
        
    Returns:
        Dict с tool и params или None
    """
    
    # ===== Список известных инструментов =====
    tools_map = {
        "get_channel_digest_by_name": ["digest.*channel", "дайджест.*канала?"],
        "get_channel_digest": ["digest.*all", "дайджест.*все"],
        "list_channels": ["list.*channel", "список.*каналов?"],
        "add_channel": ["add.*channel", "добавить.*канал"],
        "get_channel_metadata": ["metadata.*channel", "информация.*канала?"],
    }
    
    text_lower = text.lower()
    detected_tool = None
    
    # Пробуем найти инструмент
    for tool_name, patterns in tools_map.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                detected_tool = tool_name
                break
        if detected_tool:
            break
    
    if not detected_tool:
        return None
    
    # ===== Извлекаем параметры =====
    params = {}
    
    # Ищем название канала
    channel_patterns = [
        r'canal[" ]*:?\s*["\']?([^"\'}\n]+)',  # "canal": "name"
        r'канал\s*["\']?([^"\'}\n]+)',          # канал "name"
        r'["\']?channel_name["\']?\s*:\s*["\']?([^"\'}\n]+)',  # channel_name: name
    ]
    
    for pattern in channel_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            channel_name = match.group(1).strip().strip('"\'')
            params["channel_name"] = channel_name
            break
    
    # Ищем количество дней
    days_patterns = [
        r'(\d+)\s*(?:дн|день|дня)',        # 3 дня
        r'days?["\']?\s*:\s*(\d+)',        # days: 3
    ]
    
    for pattern in days_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            params["days"] = int(match.group(1))
            break
    
    if not params and detected_tool not in ["list_channels"]:
        return None
    
    return {
        "tool": detected_tool,
        "params": params
    }


# Пример использования
if __name__ == "__main__":
    # Случай когда JSON не найден
    messy_output = """
    Хорошо, я помогу получить дайджест по каналу Набока за 3 дня.
    Это займет некоторое время...
    """
    
    result = extract_tool_from_text_heuristic(messy_output)
    print(f"Extracted: {result}")
    # Output: {'tool': 'get_channel_digest_by_name', 'params': {'channel_name': 'Набока', 'days': 3}}
```

---

## ✅ Решение 3: Complete Parser Pipeline

```python
"""
Полный pipeline парсинга с fallback-ами
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ToolCallParser:
    """Полный парсер для вызовов инструментов."""
    
    @staticmethod
    def parse(text: str, strict: bool = False) -> Optional[Dict[str, Any]]:
        """Парсить вызов инструмента из текста.
        
        Args:
            text: Текст модели
            strict: Если True, использовать только JSON парсер (без heuristics)
            
        Returns:
            Dict {"tool": "...", "params": {...}} или None
        """
        
        # ===== Попытка 1: JSON парсер =====
        json_result = extract_json_from_text(text)
        if json_result:
            if ToolCallParser._validate_tool_call(json_result):
                logger.info(f"✓ JSON parse successful: {json_result['tool']}")
                return json_result
            else:
                logger.warning(f"JSON validation failed: {json_result}")
        
        # ===== Если strict mode или JSON не найден =====
        if strict:
            return None
        
        # ===== Попытка 2: Heuristic парсер =====
        heuristic_result = extract_tool_from_text_heuristic(text)
        if heuristic_result:
            logger.info(f"✓ Heuristic parse successful: {heuristic_result['tool']}")
            return heuristic_result
        
        logger.warning("Could not parse tool call from text")
        return None
    
    @staticmethod
    def _validate_tool_call(tool_call: Dict[str, Any]) -> bool:
        """Проверить что tool_call валиден.
        
        Args:
            tool_call: Распарсенный инструмент
            
        Returns:
            True если валиден
        """
        # Должны быть поля tool и params
        if "tool" not in tool_call or "params" not in tool_call:
            return False
        
        # Инструмент должен быть строкой
        if not isinstance(tool_call["tool"], str):
            return False
        
        # Параметры должны быть словарём или пустым
        if tool_call["params"] is not None and not isinstance(tool_call["params"], dict):
            return False
        
        return True
    
    @staticmethod
    def parse_with_fallback(
        text: str,
        max_attempts: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Парсить с несколькими попытками и fallback-ами.
        
        Args:
            text: Текст модели
            max_attempts: Макс попытки
            
        Returns:
            Распарсенный инструмент или None
        """
        
        # Очищаем текст
        text = ToolCallParser._clean_text(text)
        
        # Попытка 1: Строгий парсинг
        result = ToolCallParser.parse(text, strict=True)
        if result:
            return result
        
        # Попытка 2: Парсинг с heuristics
        result = ToolCallParser.parse(text, strict=False)
        if result:
            return result
        
        # Попытка 3: Парсинг фрагментов текста
        # Может помочь если модель выдала несколько попыток
        fragments = text.split("\n\n")
        for fragment in fragments:
            result = ToolCallParser.parse(fragment, strict=False)
            if result:
                logger.debug(f"Parsed from fragment: {result}")
                return result
        
        return None
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Очистить текст перед парсингом.
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный текст
        """
        # Удаляем системные сообщения
        remove_patterns = [
            r"Available tools:.*?(?=\n\n|\Z)",
            r"<\|im_start\|>.*?<\|im_end\|>",
            r"\[INST\].*?\[/INST\]",
            r">>>.*?<<<",
        ]
        
        for pattern in remove_patterns:
            text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
        
        return text.strip()


# ===== Использование =====

if __name__ == "__main__":
    # Пример 1: JSON есть
    output1 = '{"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока", "days": 3}}'
    result1 = ToolCallParser.parse_with_fallback(output1)
    print(f"Result 1: {result1}")
    
    # Пример 2: JSON в тексте
    output2 = """
    Хорошо, я помогу.
    {"tool": "list_channels", "params": {}}
    Давайте посмотрим каналы...
    """
    result2 = ToolCallParser.parse_with_fallback(output2)
    print(f"Result 2: {result2}")
    
    # Пример 3: Нет JSON, только текст
    output3 = """
    Я получу дайджест по каналу Набока за 3 дня.
    """
    result3 = ToolCallParser.parse_with_fallback(output3)
    print(f"Result 3: {result3}")
```

---

## 🧪 Integration Test

```python
"""
Полный тест парсера в контексте агента
"""

import asyncio
from typing import Optional, Dict, Any


class AgentWithRobustParsing:
    """Агент с robust парсингом."""
    
    def __init__(self, mcp_client, model_client):
        self.mcp_client = mcp_client
        self.model_client = model_client
    
    async def process(self, user_input: str) -> Dict[str, Any]:
        """Обработать входной текст с robust парсингом.
        
        Args:
            user_input: Текст от пользователя
            
        Returns:
            Результат обработки
        """
        
        # Получаем ответ от модели
        response = await self.model_client.create_completion(
            messages=[
                {"role": "system", "content": DECISION_ONLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.2,
            max_tokens=256
        )
        
        model_output = response["choices"][0]["message"]["content"]
        
        # ===== Robust парсинг =====
        tool_call = ToolCallParser.parse_with_fallback(model_output)
        
        if not tool_call:
            logger.error(f"Failed to parse tool call from: {model_output}")
            return {
                "success": False,
                "error": "Could not understand request",
                "debug": model_output[:200]
            }
        
        # Выполняем инструмент
        tool_name = tool_call["tool"]
        tool_params = tool_call["params"]
        
        try:
            result = await self.mcp_client.execute_tool(tool_name, **tool_params)
            
            return {
                "success": True,
                "tool": tool_name,
                "params": tool_params,
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }


# ===== Test Suite =====

async def test_agent_parsing():
    """Тест агента с различными выходами модели."""
    
    agent = AgentWithRobustParsing(mock_mcp_client, mock_model_client)
    
    test_cases = [
        {
            "input": "Дайджест по Набока за 3 дня",
            "model_output": '{"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока", "days": 3}}',
            "expected_tool": "get_channel_digest_by_name"
        },
        {
            "input": "Какие каналы?",
            "model_output": """
            Сейчас я получу список ваших каналов...
            
            ```json
            {"tool": "list_channels", "params": {}}
            ```
            
            Это поможет...
            """,
            "expected_tool": "list_channels"
        },
        {
            "input": "Добавь канал python",
            "model_output": """
            Окей, я подпишу вас на канал python.
            
            {
              "tool": "add_channel",
              "params": {
                "channel_name": "python"
              }
            }
            """,
            "expected_tool": "add_channel"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['input']}")
        
        # Мокируем ответ модели
        mock_model_client.model_output = test_case["model_output"]
        
        result = await agent.process(test_case["input"])
        
        assert result["success"], f"Test {i} failed: {result.get('error')}"
        assert result["tool"] == test_case["expected_tool"], f"Wrong tool: {result['tool']}"
        
        print(f"  ✓ Passed")
    
    print(f"\n✅ All {len(test_cases)} tests passed!")


# Запуск тестов
if __name__ == "__main__":
    asyncio.run(test_agent_parsing())
```

---

## 📝 Рекомендации по интеграции в Cursor

Попроси Cursor:

```
Используя примеры парсеров из agent_output_parsers.md:

1. Создай файл src/domain/parsers/tool_call_parser.py
   - ToolCallParser с методами parse(), _validate_tool_call(), _clean_text()
   - Функции extract_json_from_text() и extract_tool_from_text_heuristic()

2. Обнови MCPAwareAgent.process():
   - Используй ToolCallParser.parse_with_fallback() после получения ответа модели
   - Добавь логирование на каждом шаге парсинга

3. Создай tests/test_parser.py:
   - Unit тесты для extract_json_from_text() (10+ cases)
   - Integration тесты для полного pipeline
   - Edge cases: пустой текст, некорректный JSON, multiline и т.д.

4. Обновляемы конфигурацию:
   - PARSER_STRICT_MODE (bool) для режима парсинга
   - PARSER_MAX_ATTEMPTS (int) для fallback-ов

Требования:
- Type hints везде
- Обработка всех edge cases
- Логирование на DEBUG уровне для каждой попытки
- Покрытие тестами > 90%
```

Это решит проблему "стены текста" и даст надежный парсинг! ✅
