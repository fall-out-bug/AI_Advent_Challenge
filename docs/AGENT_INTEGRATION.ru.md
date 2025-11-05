# Руководство по интеграции MCP-aware агента

[English](AGENT_INTEGRATION.md) | [Русский](AGENT_INTEGRATION.ru.md)

## Обзор

MCP-aware агент — интеллектуальный помощник, который автоматически обнаруживает и использует инструменты MCP (Model Context Protocol) для выполнения запросов пользователей. Интегрируется с локальной LLM (Mistral) для понимания намерений пользователя на естественном языке.

## Архитектура

```
┌─────────────────┐
│  Telegram Bot   │
│   (ButlerBot)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MCPAwareAgent   │
│                 │
│  - LLM Client   │
│  - Tools        │
│  - Registry     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│ Robust │ │   Dialog     │
│  MCP   │ │   Manager    │
│ Client │ │              │
└───┬────┘ └──────┬───────┘
    │             │
    ▼             ▼
┌────────┐   ┌──────────┐
│   MCP  │   │ MongoDB  │
│ Server │   │          │
└────────┘   └──────────┘
```

## Компоненты

### 1. MCPAwareAgent

Основной агент, обрабатывающий запросы пользователей с помощью LLM и инструментов MCP.

**Расположение:** `src/domain/agents/mcp_aware_agent.py`

**Возможности:**
- Автоматическое обнаружение инструментов через MCPToolsRegistry
- Выбор инструментов на основе LLM
- Валидация параметров
- Обработка ошибок с метриками

**Пример использования:**
```python
from src.domain.agents.mcp_aware_agent import MCPAwareAgent
from src.presentation.mcp.client import MCPClient
from shared_package.clients.unified_client import UnifiedModelClient

# Инициализация
mcp_client = MCPClient()
llm_client = UnifiedModelClient()
agent = MCPAwareAgent(mcp_client=mcp_client, llm_client=llm_client)

# Обработка запроса
request = AgentRequest(
    user_id=12345,
    message="Собери дайджест по каналу onaboka",
    session_id="session_123"
)
response = await agent.process(request)
```

### 2. MCPToolsRegistry

Кэширует и управляет метаданными инструментов MCP.

**Расположение:** `src/presentation/mcp/tools_registry.py`

**Возможности:**
- Кэширование обнаружения инструментов (TTL 5 минут)
- Построение промптов для LLM
- Парсинг метаданных инструментов

**Пример использования:**
```python
from src.presentation.mcp.tools_registry import MCPToolsRegistry

registry = MCPToolsRegistry(mcp_client=client)
tools = await registry.discover_tools()
prompt = registry.build_tools_prompt()
```

### 3. RobustMCPClient

Обертка над базовым MCP клиентом с логикой повторных попыток и обработкой ошибок.

**Расположение:** `src/infrastructure/clients/mcp_client_robust.py`

**Возможности:**
- Повторные попытки с экспоненциальной задержкой (максимум 3 попытки)
- Классификация ошибок (повторяемые vs неповторяемые)
- Интеграция метрик Prometheus

**Конфигурация:**
- `MAX_RETRIES = 3`
- `INITIAL_WAIT = 1.0` секунд
- `MAX_WAIT = 10.0` секунд
- `EXPONENTIAL_BASE = 2.0`

**Пример использования:**
```python
from src.infrastructure.clients.mcp_client_robust import RobustMCPClient
from src.presentation.mcp.client import MCPClient

base_client = MCPClient()
robust_client = RobustMCPClient(base_client=base_client)
result = await robust_client.call_tool("get_posts", {"channel_id": "test"})
```

### 4. DialogManager

Управляет историей диалогов в MongoDB с автоматическим сжатием.

**Расположение:** `src/infrastructure/dialogs/dialog_manager.py`

**Возможности:**
- Хранение сообщений в MongoDB
- Автоматическое сжатие при превышении лимита токенов (8000 токенов)
- Получение контекста с учетом лимитов токенов

**Конфигурация:**
- `COMPRESSION_THRESHOLD = 8000` токенов
- `MAX_CONTEXT_TOKENS = 8000`

**Пример использования:**
```python
from src.infrastructure.dialogs.dialog_manager import DialogManager
from src.infrastructure.database.mongo import get_db

mongodb = await get_db()
manager = DialogManager(mongodb=mongodb, llm_client=llm_client)

# Добавление сообщений
await manager.add_message("session_123", "user", "Привет!")
await manager.add_message("session_123", "assistant", "Привет!")

# Получение контекста
context = await manager.get_context("session_123", max_tokens=1000)
```

### 5. HistoryCompressor

Сжимает историю диалогов с помощью LLM при превышении лимита токенов.

**Расположение:** `src/infrastructure/dialogs/history_compressor.py`

**Возможности:**
- Суммаризация на основе LLM
- Сохранение ключевого контекста
- Настраиваемые параметры сжатия

**Пример использования:**
```python
from src.infrastructure.dialogs.history_compressor import HistoryCompressor

compressor = HistoryCompressor(llm_client=llm_client)
summary = await compressor.compress("session_123", messages)
```

## Интеграция с Telegram ботом

Агент интегрирован в ButlerBot для обработки естественного языка:

```python
# В butler_bot.py
async def handle_natural_language(self, message: Message) -> None:
    # Получение контекста диалога
    context = await self._dialog_manager.get_context(session_id)
    
    # Создание запроса агента
    request = AgentRequest(
        user_id=message.from_user.id,
        message=message.text,
        session_id=session_id,
        context={"dialog_context": context}
    )
    
    # Обработка агентом
    response = await self._agent.process(request)
    
    # Сохранение диалога
    await self._dialog_manager.add_message(session_id, "user", message.text)
    await self._dialog_manager.add_message(session_id, "assistant", response.text)
    
    # Отправка ответа
    await message.answer(response.text)
```

## Конфигурация

### Переменные окружения

- `TELEGRAM_BOT_TOKEN`: Токен Telegram бота (обязательно)
- `MCP_SERVER_URL`: URL MCP сервера (опционально, по умолчанию stdio)
- `MONGODB_URL`: Строка подключения к MongoDB (обязательно)
- `DB_NAME`: Имя базы данных (по умолчанию: `ai_challenge`)

### Константы по умолчанию

- **Агент:**
  - `DEFAULT_MODEL_NAME = "mistral"`
  - `DEFAULT_MAX_TOKENS = 2048`
  - `DEFAULT_TEMPERATURE = 0.7`

- **Dialog Manager:**
  - `COMPRESSION_THRESHOLD = 8000` токенов
  - `MAX_CONTEXT_TOKENS = 8000`

- **Логика повторных попыток:**
  - `MAX_RETRIES = 3`
  - `INITIAL_WAIT = 1.0` секунд
  - `MAX_WAIT = 10.0` секунд

## Мониторинг

Метрики Prometheus собираются автоматически:

- `agent_requests_total`: Всего запросов агента
- `agent_tokens_used_total`: Всего использовано токенов
- `agent_request_duration_seconds`: Гистограмма длительности запросов
- `agent_tools_used_total`: Счетчик использования инструментов
- `mcp_client_retries_total`: Счетчик повторных попыток
- `llm_requests_total`: Счетчик запросов LLM

## Обработка ошибок

Агент обрабатывает ошибки gracefully:

1. **Ошибки LLM:** Возвращает ответ с ошибкой и деталями
2. **Невалидные инструменты:** Проверяет существование инструмента перед выполнением
3. **Ошибки MCP:** Повторяет попытки с экспоненциальной задержкой
4. **Ошибки MongoDB:** Логирует и продолжает работу (graceful degradation)

## Тестирование

Запуск тестов:

```bash
# Модульные тесты
pytest tests/domain/agents/
pytest tests/infrastructure/clients/test_mcp_client_robust.py
pytest tests/infrastructure/dialogs/

# Интеграционные тесты
pytest tests/integration/
```

## Лучшие практики

1. **Управление сессиями:** Используйте уникальные ID сессий для каждого пользователя
2. **Лимиты токенов:** Отслеживайте использование токенов для избежания переполнения контекста
3. **Мониторинг ошибок:** Проверяйте метрики Prometheus на частоту ошибок
4. **Обнаружение инструментов:** Реестр кэширует инструменты на 5 минут
5. **Graceful Shutdown:** Используйте менеджер GracefulShutdown для корректного завершения

## Решение проблем

### Агент не выбирает инструменты

- Проверьте обнаружение инструментов: `await registry.discover_tools()`
- Убедитесь, что промпт LLM включает описания инструментов
- Проверьте формат ответа LLM (должен быть JSON для вызовов инструментов)

### Высокая частота повторных попыток

- Проверьте доступность MCP сервера
- Убедитесь в сетевом подключении
- Изучите логи ошибок для поиска причины

### Проблемы со сжатием диалогов

- Убедитесь, что LLM клиент настроен
- Проверьте подключение к MongoDB
- Проверьте точность оценки токенов

