# Phase 3: Application Layer (Use Cases) - Документация

## ✅ Статус: ЗАВЕРШЕНА

**Дата завершения:** Phase 3 полностью реализована и протестирована.

---

## 📦 Созданные файлы

### Production Code
```
src/application/usecases/
├── __init__.py                    # Экспорты всех use cases
├── result_types.py               # Pydantic модели результатов (13 строк)
├── create_task_usecase.py        # Use case для создания задач (120 строк)
└── collect_data_usecase.py        # Use case для сбора данных (54 строки)
```

### Test Code
```
tests/unit/application/usecases/
├── __init__.py
├── test_result_types.py          # 9 тестов для result types
├── test_create_task_usecase.py   # 6 тестов для CreateTaskUseCase
└── test_collect_data_usecase.py  # 7 тестов для CollectDataUseCase
```

---

## 📊 Статистика

- **Файлов создано:** 8 файлов (4 production + 4 test)
- **Тестов написано:** 22 (все проходят ✅)
- **Покрытие кода:** 98.75% (требование ≥80% ✅)
- **Строк production кода:** ~120 строк
- **Строк test кода:** ~400 строк
- **Функций в коде:** Все функции ≤15 строк ✅

---

## 🎯 Реализованные компоненты

### 1. Result Types (`result_types.py`)

Типизированные результаты для всех use cases через Pydantic:

**TaskCreationResult:**
- `created: bool` - успешность создания
- `task_id: Optional[str]` - ID созданной задачи
- `clarification: Optional[str]` - вопрос для уточнения
- `error: Optional[str]` - сообщение об ошибке

**DigestResult:**
- `digests: List[Dict[str, Any]]` - список дайджестов
- `error: Optional[str]` - ошибка

**StatsResult:**
- `stats: Dict[str, Any]` - статистика
- `error: Optional[str]` - ошибка

Все модели имеют полные docstrings с примерами использования.

### 2. CreateTaskUseCase (`create_task_usecase.py`)

**Назначение:**
Инкапсулирует бизнес-логику создания задач: парсинг intent, валидацию, создание через MCP.

**Методы (все ≤15 строк):**
- `execute(user_id, message, context)` - главный метод use case
- `_parse_intent()` - парсинг намерения через IntentOrchestrator
- `_build_clarification_result()` - построение результата с уточнениями
- `_create_task_via_mcp()` - создание задачи через MCP tool `add_task`
- `_build_mcp_params()` - формирование параметров для MCP
- `_process_mcp_result()` - обработка ответа от MCP
- `_build_error_result()` - построение результата с ошибкой

**Зависимости:**
- `IntentOrchestrator` - для парсинга intent
- `ToolClientProtocol` - для вызова MCP tools
- `AsyncIOMotorDatabase` - для доступа к MongoDB (пока не используется, но готов)

**Особенности:**
- Обработка clarification flow (когда нужны уточнения)
- Полная обработка ошибок (парсинг, MCP, валидация)
- Типизированные результаты вместо raw dict

### 3. CollectDataUseCase (`collect_data_usecase.py`)

**Назначение:**
Инкапсулирует бизнес-логику сбора данных: дайджесты каналов и статистика студентов.

**Методы (все ≤15 строк):**
- `get_channels_digest(user_id)` - получение дайджестов через MCP `get_channel_digest`
- `get_student_stats(teacher_id)` - получение статистики через MCP `get_student_stats`

**Зависимости:**
- `ToolClientProtocol` - для вызова MCP tools

**Особенности:**
- Stateless design (нет внутреннего состояния)
- Полная обработка ошибок
- Типизированные результаты

---

## ✅ Соответствие требованиям

### Chief Architect
- ✅ **Use Case pattern** - реализован полностью
- ✅ **Command-Query separation** - соблюдено
- ✅ **Result объекты** - вместо raw dict используются Pydantic модели
- ✅ **Stateless use cases** - нет внутреннего состояния

### Python Zen
- ✅ **Функции ≤15 строк** - все функции проверены и соответствуют
- ✅ **Explicit over implicit** - явные типы, явная обработка ошибок
- ✅ **Simple and readable** - код простой и читаемый
- ✅ **Single responsibility** - каждый метод делает одну вещь

### QA/TDD
- ✅ **Unit tests с mock'ами** - 22 теста, все используют mock'и
- ✅ **Coverage ≥80%** - достигнуто 98.75%
- ✅ **Happy path** - все успешные сценарии протестированы
- ✅ **Error cases** - все ошибки обработаны и протестированы
- ⚠️ **Integration tests** - не созданы (опционально для Phase 3)

### Technical Writer
- ✅ **Docstrings с примерами** - все use cases имеют примеры
- ✅ **Google-style docstrings** - используется везде
- ✅ **Purpose, Args, Returns, Exceptions** - все секции заполнены

### ML Engineer
- ⚠️ **Drift detection prompts** - не реализовано (опционально, специфично для ML)

---

## 🧪 Тестирование

### Покрытие тестами

```
Name                                               Stmts   Miss   Cover
---------------------------------------------------------------------------------
src/application/usecases/__init__.py                   4      0 100.00%
src/application/usecases/collect_data_usecase.py      22      0 100.00%
src/application/usecases/create_task_usecase.py       41      1  97.56%
src/application/usecases/result_types.py              13      0 100.00%
---------------------------------------------------------------------------------
TOTAL                                                 80      1  98.75%
```

### Тестовые сценарии

**test_result_types.py (9 тестов):**
- ✅ Successful creation result
- ✅ Clarification result
- ✅ Error result
- ✅ Successful digest
- ✅ Empty digests
- ✅ Error digest
- ✅ Successful stats
- ✅ Empty stats
- ✅ Error stats

**test_create_task_usecase.py (6 тестов):**
- ✅ Successful task creation (happy path)
- ✅ Clarification needed flow
- ✅ Intent parsing error
- ✅ MCP tool error
- ✅ MCP tool error response
- ✅ Context passed to intent orchestrator

**test_collect_data_usecase.py (7 тестов):**
- ✅ Get channels digest success
- ✅ Get channels digest empty
- ✅ Get channels digest error
- ✅ Get student stats success
- ✅ Get student stats empty
- ✅ Get student stats error
- ✅ Get student stats tool not found

### Запуск тестов

```bash
# Все тесты Phase 3
pytest tests/unit/application/usecases/ -v

# С покрытием
pytest tests/unit/application/usecases/ --cov=src/application/usecases --cov-report=term-missing

# Быстрый запуск
pytest tests/unit/application/usecases/ -q
```

---

## 🔗 Интеграция и готовность к Phase 4

### Use Cases готовы к использованию

**CreateTaskUseCase:**
```python
from src.application.usecases import CreateTaskUseCase
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.domain.interfaces.tool_client import ToolClientProtocol
from motor.motor_asyncio import AsyncIOMotorDatabase

# Создание
use_case = CreateTaskUseCase(
    intent_orch=intent_orchestrator,
    tool_client=mcp_client,
    mongodb=mongodb_db
)

# Использование
result = await use_case.execute(
    user_id=123,
    message="Buy milk tomorrow",
    context={"previous_message": "..."}
)

if result.created:
    print(f"Task created: {result.task_id}")
elif result.clarification:
    print(f"Need clarification: {result.clarification}")
elif result.error:
    print(f"Error: {result.error}")
```

**CollectDataUseCase:**
```python
from src.application.usecases import CollectDataUseCase

# Создание
use_case = CollectDataUseCase(tool_client=mcp_client)

# Использование
digest_result = await use_case.get_channels_digest(user_id=123)
stats_result = await use_case.get_student_stats(teacher_id=456)
```

### Текущее состояние handlers

**Domain handlers (существующие):**
- `TaskHandler` (src/domain/agents/handlers/task_handler.py) - использует `IntentOrchestrator` + `ToolClientProtocol` напрямую
- `DataHandler` (src/domain/agents/handlers/data_handler.py) - использует `ToolClientProtocol` напрямую

**Telegram handlers (существующие):**
- `src/presentation/bot/handlers/tasks.py` - использует MCP напрямую
- `src/presentation/bot/handlers/channels.py` - использует MCP напрямую

**ButlerOrchestrator:**
- Существует в `src/domain/agents/butler_orchestrator.py`
- Использует domain handlers напрямую
- Готов к интеграции use cases

### Что нужно в Phase 4

**Вариант A (Рекомендуемый):**
1. Обновить domain handlers (`TaskHandler`, `DataHandler`) для использования use cases
2. Создать новый Telegram handler или обновить существующий для использования `ButlerOrchestrator`
3. Обновить `main.py` для DI всех компонентов с use cases

**Вариант B (Минимальный):**
1. Создать новый Telegram handler с прямым использованием use cases
2. Обновить `main.py` для DI

---

## 📝 Заметки для Phase 4

### Зависимости Use Cases

**CreateTaskUseCase требует:**
- `IntentOrchestrator` (существует в `src/application/orchestration/intent_orchestrator.py`)
- `ToolClientProtocol` (интерфейс в `src/domain/interfaces/tool_client.py`)
- `AsyncIOMotorDatabase` (MongoDB, уже используется в проекте)

**CollectDataUseCase требует:**
- `ToolClientProtocol` (интерфейс в `src/domain/interfaces/tool_client.py`)

### Пример интеграции в main.py

```python
from motor.motor_asyncio import AsyncIOMotorClient
from src.infrastructure.clients.mcp_client_robust import RobustMCPClient
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.application.usecases import CreateTaskUseCase, CollectDataUseCase

# 1. Initialize MongoDB
mongodb = AsyncIOMotorClient(MONGODB_URL).butler_db

# 2. Initialize services
base_mcp_client = get_mcp_client()  # или создать новый
mcp_client = RobustMCPClient(base_client=base_mcp_client)
intent_orch = IntentOrchestrator()

# 3. Initialize use cases
create_task_uc = CreateTaskUseCase(
    intent_orch=intent_orch,
    tool_client=mcp_client,
    mongodb=mongodb
)
collect_data_uc = CollectDataUseCase(tool_client=mcp_client)

# 4. Use cases готовы к использованию
```

---

## ⚠️ Не выполнено (опционально)

### 1. Integration Tests
- В плане упоминаются "Integration tests with mock MCP"
- Можно добавить позже в `tests/integration/application/usecases/`
- Unit tests уже покрывают все сценарии с mock'ами

### 2. Drift Detection Prompts
- ML-специфичная функциональность для student stats
- Упомянуто в плане как опциональное для ML Engineer
- Не критично для базовой функциональности Phase 3

### 3. Интеграция с существующими handlers
- Текущие handlers используют MCP напрямую
- Интеграция use cases в handlers будет в Phase 4 (опционально)

---

## 🚀 Следующие шаги

См. `../PHASE4_CHECKLIST.md` для детального плана Phase 4.

**Ключевые вопросы для Phase 4:**
1. Обновлять ли domain handlers для использования use cases?
2. Создавать ли новый `src/presentation/telegram/butler_handler.py` или обновить `butler_bot.py`?
3. Как интегрировать use cases в `ButlerOrchestrator`?

---

## 📚 Ссылки

- **План рефакторинга:** `../day_13-refactoring.md`
- **Phase 4 Checklist:** `../PHASE4_CHECKLIST.md` (будет создан)
- **Production код:** `src/application/usecases/`
- **Тесты:** `tests/unit/application/usecases/`

---

**Статус:** ✅ Phase 3 завершена и готова к интеграции в Phase 4

