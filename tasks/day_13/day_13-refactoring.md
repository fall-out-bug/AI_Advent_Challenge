# 🎯 Итоговый План для Cursor: Butler Agent полная переделка

На основе ваших Cursor правил (Python Zen, Chief Architect, AI Reviewer, QA/TDD, DevOps, Technical Writer, ML Engineer) составил комплексный план переделки для максимальной эффективности.

---

## 📋 PHASE 0: Pre-Implementation (1 день)

### Задачи
1. **Analize Current State** 
   - [ ] Cursor проанализирует существующий код через **AI Reviewer**
   - [ ] Выдаст отчёт по: token cost, функциям >30 строк, архитектурным проблемам
   - [ ] Определит "God Classes" и файлы для рефакторинга

2. **Architecture Review** 
   - [ ] **Chief Architect** проверит SOLID нарушения
   - [ ] Определит правильные слои: presentation, domain, infrastructure, application
   - [ ] Выявит циклические зависимости между MCP, LLM, MongoDB

3. **Test Coverage Baseline**
   - [ ] **QA/TDD Reviewer** выдаст отчёт по покрытию
   - [ ] Определит, какие модули нужны unit/integration/e2e тесты

### Cursor Rules to Apply
- **AI Reviewer**: статистика читаемости, token cost, рекомендации по рефакторингу
- **Chief Architect**: архитектурные проблемы, слои, модули

---

## 🏗️ PHASE 1: Domain Layer (FSM + Orchestration) — 2-3 дня

### 1.1 Dialog Orchestrator (новый файл)
**Файл:** `src/domain/agents/butler_orchestrator.py`

```python
class ButtlerOrchestrator:
    """Управляет режимами работы и маршрутизирует запросы.
    
    - Mode classification через Mistral-7B
    - Delegated handlers для 4 режимов
    - Graceful error handling
    """
    
    async def handle_user_message(user_id, message, session_id) -> str:
        # Режимы: TASK, DATA, REMINDERS, IDLE
        pass
```

**Требования Cursor:**
- [ ] **Python Zen**: Explicit, Simple, Single Responsibility
  - Каждый режим — отдельный метод `_handle_*`
  - No magic, явный контроль потока
- [ ] **Chief Architect**: SOLID
  - Абстрактные базовые классы для handler'ов
  - Инверсия зависимостей (DI через `__init__`)
- [ ] **AI Reviewer**: Читаемость
  - Функция max 40 строк
  - Имена методов осмысленные
- [ ] **Technical Writer**: Docstring
  - Google-style для каждого метода

### 1.2 Intent Handler с FSM
**Файл:** `src/domain/agents/state_machine.py`

```python
class DialogState(Enum):
    IDLE, TASK_CREATE_TITLE, TASK_CREATE_DESC, TASK_CONFIRM, ...

class DialogContext:
    """Контекст диалога с явным состоянием."""
    state: DialogState
    data: Dict[str, Any]
    step_count: int
```

**Требования:**
- [ ] **Python Zen**: Enum > string literals
- [ ] **QA/TDD**: Тесты для transitions
  - `test_idle_to_task_create`
  - `test_task_create_to_confirm`

### 1.3 Handlers для 4 режимов
**Файлы:**
- `src/domain/agents/handlers/task_handler.py`
- `src/domain/agents/handlers/data_handler.py`
- `src/domain/agents/handlers/reminders_handler.py`
- `src/domain/agents/handlers/chat_handler.py`

**Требования:**
- [ ] **Chief Architect**: 
  - Каждый handler имплементирует интерфейс `Handler`
  - Зависимости через DI
  - No circular imports
- [ ] **Python Zen**: Readability
  - Max 25 строк на handler-метод
- [ ] **QA/TDD**: Unit тесты для каждого handler

**Code structure:**
```python
# src/domain/agents/handlers/handler.py
from abc import ABC, abstractmethod

class Handler(ABC):
    @abstractmethod
    async def handle(self, context, message) -> str:
        pass

# src/domain/agents/handlers/task_handler.py
class TaskHandler(Handler):
    def __init__(self, intent_orch, mcp_client, mongodb):
        self.intent_orch = intent_orch
        self.mcp_client = mcp_client
        self.mongodb = mongodb
    
    async def handle(self, context, message) -> str:
        # Делегировать на intent_orch
        # Сохранить через MCP
        pass
```

---

## 🔌 PHASE 2: Infrastructure Layer (LLM + MCP) — 2 дня

### 2.1 LLM Client Wrapper
**Файл:** `src/infrastructure/llm/mistral_client.py`

```python
class MistralClient:
    """Асинхронная обёртка для Mistral-7B через chat_api.py"""
    
    async def make_request(prompt, max_tokens, temperature) -> dict:
        # HTTP call to localhost:8001/chat
        # Retry logic, timeout handling
        pass
    
    async def classify_mode(message) -> str:
        # Intent classification
        pass
```

**Требования:**
- [ ] **Python Zen**: Error handling
  - Явные исключения, no silent failures
  - Logging для each step
- [ ] **DevOps**: Healthcheck + monitoring
  - Timeout: 30s per request
  - Max retries: 3
  - Fallback mode if unavailable
- [ ] **QA/TDD**: Unit tests
  - Mock HTTP responses
  - Test timeouts, retries

### 2.2 MCP Tools Registry (upgrade)
**Файл:** `src/presentation/mcp/tools_registry_v2.py`

```python
class MCPToolsRegistry:
    """Unified schema validation для всех MCP tools"""
    
    @dataclass
    class ToolSchema:
        name: str
        category: ToolCategory
        parameters: List[ToolParameter]  # с типами и validation
        returns: Dict[str, str]
    
    async def validate_tool_call(tool_name, params) -> Tuple[bool, Optional[str]]:
        # Strict validation
        pass
    
    async def call_tool(tool_name, params, user_id) -> dict:
        # With retry logic (использовать ваш RobustMCPClient)
        pass
```

**Требования:**
- [ ] **Python Zen**: Schema-first design
  - Dataclass вместо dict
  - Type hints везде
- [ ] **Chief Architect**: Registry pattern
  - Self-registering tools
  - Clean contracts

---

## 📦 PHASE 3: Application Layer (Use Cases) — 2 дня

### 3.1 Task Creation Use Case
**Файл:** `src/application/usecases/create_task_usecase.py`

```python
class CreateTaskUseCase:
    """Бизнес-логика создания задачи.
    
    - Парсинг intent через IntentOrchestrator
    - Валидация данных
    - Сохранение через MCP
    - Возврат результата
    """
    
    def __init__(self, intent_orch, mcp_client, mongodb):
        self.intent_orch = intent_orch
        self.mcp_client = mcp_client
        self.mongodb = mongodb
    
    async def execute(self, user_id, message) -> TaskCreationResult:
        intent = await self.intent_orch.parse_task_intent(message)
        
        if intent.needs_clarification:
            return TaskCreationResult(clarification=intent.questions[0])
        
        # Сохранить через MCP
        result = await self.mcp_client.call_tool(
            "create_task",
            intent.to_mcp_params()
        )
        
        return TaskCreationResult(created=True, task_id=result['id'])
```

**Требования:**
- [ ] **Chief Architect**: Use Case pattern
  - Command-Query separation
  - Result объект вместо raw dict
- [ ] **QA/TDD**: Integration tests
  - Test with mock MCP
  - Test error cases
- [ ] **Technical Writer**: Docstring с примерами

### 3.2 Data Collection Use Case
**Файл:** `src/application/usecases/collect_data_usecase.py`

```python
class CollectDataUseCase:
    async def get_channels_digest(self, user_id) -> DigestResult:
        result = await self.mcp_client.call_tool(...)
        return DigestResult(digests=result['digests'])
    
    async def get_student_stats(self, teacher_id) -> StatsResult:
        result = await self.mcp_client.call_tool(...)
        return StatsResult(stats=result['stats'])
```

**Требования:**
- [ ] **Chief Architect**: Each use case is stateless
- [ ] **ML Engineer**: For stats, add drift detection prompts
- [ ] **Technical Writer**: Examples in docstring

---

## 🎯 PHASE 4: Presentation Layer (Telegram) — 1-2 дня

### 4.1 Butler Handler (новый)
**Файл:** `src/presentation/telegram/butler_handler.py`

```python
butler_router = Router()

@butler_router.message()
async def handle_any_message(message: Message) -> None:
    """Главный entry point для сообщений."""
    
    user_id = message.from_user.id
    session_id = f"{user_id}:{message.message_id}"
    
    butler = get_butler_orchestrator()
    response = await butler.handle_user_message(user_id, message.text, session_id)
    
    await message.answer(response, parse_mode="Markdown")
```

**Требования:**
- [ ] **Python Zen**: Simple, readable, one responsibility
- [ ] **DevOps**: Error handling + logging
  - Catch exceptions, send error message
  - Log all requests for monitoring
- [ ] **QA/TDD**: E2E tests through aiogram test client

### 4.2 Updated Main
**Файл:** `src/presentation/telegram/main.py`

```python
async def main():
    # 1. Initialize MongoDB
    mongodb = AsyncClient(MONGODB_URL).butler_db
    
    # 2. Initialize services
    mcp_client = RobustMCPClient()
    mistral_client = MistralClient(MISTRAL_API_URL)
    intent_orch = IntentOrchestrator()
    
    # 3. Initialize use cases
    create_task_uc = CreateTaskUseCase(intent_orch, mcp_client, mongodb)
    collect_data_uc = CollectDataUseCase(mcp_client)
    
    # 4. Initialize orchestrator
    butler = ButtlerOrchestrator(
        mongodb, mistral_client, mcp_client, intent_orch,
        create_task_uc, collect_data_uc
    )
    set_butler_orchestrator(butler)
    
    # 5. Setup Telegram
    bot = Bot(TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(butler_router)
    
    await dp.start_polling(bot)
```

**Требования:**
- [ ] **Chief Architect**: Dependency Injection (явный, не через globals)
- [ ] **DevOps**: Graceful shutdown
  - Cleanup resources
  - Stop polling cleanly

---

## 🧪 PHASE 5: Testing & Quality (Parallel to all phases)

### 5.1 Unit Tests
**Файлы:** `tests/unit/`

```
tests/unit/
├── test_butler_orchestrator.py
├── test_dialog_state_machine.py
├── test_handlers/
│   ├── test_task_handler.py
│   ├── test_data_handler.py
│   └── test_reminders_handler.py
├── test_mistral_client.py
└── test_tools_registry.py
```

**Requirements:**
- [ ] **QA/TDD**: pytest with mocking
  - Mock MCP, MongoDB, LLM
  - Test happy path + error cases
  - Target: >80% coverage

### 5.2 Integration Tests
**Файлы:** `tests/integration/`

```
tests/integration/
├── test_butler_e2e.py  # Full flow with MongoDB + MCP mocks
├── test_task_creation_flow.py
├── test_data_collection_flow.py
└── conftest.py  # Fixtures: test DB, test MCP
```

**Requirements:**
- [ ] **DevOps**: Use docker-compose for integration tests
- [ ] **QA/TDD**: Test realistic scenarios

### 5.3 E2E Tests
**Файлы:** `tests/e2e/`

```
tests/e2e/
├── test_telegram_butler.py
└── fixtures/  # Test messages, expected responses
```

**Requirements:**
- [ ] **QA/TDD**: aiogram test client
- [ ] Test full Telegram flow

---

## 📊 PHASE 6: Documentation (Parallel)

### 6.1 Architecture Documentation
**Файл:** `docs/ARCHITECTURE.md`

```markdown
# Butler Agent Architecture

## Layers
- Presentation: Telegram handler
- Application: Use cases (CreateTask, CollectData)
- Domain: Orchestrator, Handlers, FSM
- Infrastructure: LLM, MCP, MongoDB

## Data Flow
User message → Handler → Orchestrator → Use Case → MCP/DB → Response

## Sequence Diagrams
[mermaid diagrams for each flow]
```

**Requirements:**
- [ ] **Technical Writer**: ASCII/mermaid diagrams
- [ ] **Chief Architect**: UML class diagrams

### 6.2 API Documentation
**Файл:** `docs/API.md`

```markdown
# Butler API

## Modes
- TASK: Create/manage tasks
- DATA: Get channel digests, student stats
- REMINDERS: List active reminders
- IDLE: General conversation
```

**Requirements:**
- [ ] **Technical Writer**: Examples for each endpoint

### 6.3 Deployment Guide
**Файл:** `docs/DEPLOYMENT.md`

**Requirements:**
- [ ] **DevOps**: Step-by-step deployment
- [ ] Docker, environment variables, monitoring setup

---

## 🔧 PHASE 7: DevOps & Monitoring (Parallel to phase 4-5)

### 7.1 Docker Compose
**Файл:** `docker-compose.yml`

```yaml
version: '3.9'

services:
  mongodb:
    image: mongo:7.0
    
  mistral-api:
    build: ./services/mistral
    environment:
      MODEL_NAME: mistralai/Mistral-7B-Instruct-v0.2
      
  butler-bot:
    build: ./services/butler
    environment:
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      MONGODB_URL: mongodb://mongodb:27017
      MISTRAL_API_URL: http://mistral-api:8000
```

**Requirements:**
- [ ] **DevOps**: Minimal, secure, reproducible
- [ ] Secrets через .env (не в git)

### 7.2 CI/CD Pipeline
**Файл:** `.github/workflows/test-deploy.yml` или `.gitlab-ci.yml`

```yaml
stages:
  - lint
  - test
  - build
  - deploy

lint:
  script:
    - black --check src/
    - flake8 src/
    - mypy src/

test:
  script:
    - pytest tests/ --cov=src/
  coverage: '/\d+%/'

build:
  script:
    - docker build -t butler:latest .

deploy:
  script:
    - docker-compose up -d
```

**Requirements:**
- [ ] **DevOps**: Автоматизация всего
- [ ] GitLab CI / GitHub Actions

### 7.3 Monitoring
**Файл:** `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'butler'
    static_configs:
      - targets: ['localhost:8000']
```

**Requirements:**
- [ ] **DevOps**: Metrics, alerts, dashboards
- [ ] Prometheus + Grafana templates

---

## 📝 File Structure (Final)

```
src/
├── domain/
│   ├── agents/
│   │   ├── butler_orchestrator.py      ⭐ главный orchestrator
│   │   ├── state_machine.py            ⭐ FSM с состояниями
│   │   └── handlers/
│   │       ├── handler.py              ⭐ базовый интерфейс
│   │       ├── task_handler.py         ⭐ создание задач
│   │       ├── data_handler.py         ⭐ сбор данных
│   │       ├── reminders_handler.py    ⭐ напоминания
│   │       └── chat_handler.py         ⭐ общий чат
│   └── models/
│       ├── task.py
│       ├── reminder.py
│       └── user.py
│
├── application/
│   └── usecases/
│       ├── create_task_usecase.py      ⭐ бизнес-логика
│       ├── collect_data_usecase.py     ⭐ сбор данных
│       └── result_types.py             ⭐ результаты
│
├── infrastructure/
│   ├── llm/
│   │   ├── mistral_client.py           ⭐ LLM обёртка
│   │   └── mcp_wrapper.py
│   ├── database/
│   │   ├── mongodb.py                  ✅ существует
│   │   ├── schemas.py                  ✅ существует
│   │   └── repositories.py             ⭐ новый (для CQRS)
│   └── mcp/
│       ├── client_robust.py            ✅ существует
│       └── tools_registry_v2.py        ⭐ upgrade
│
├── presentation/
│   └── telegram/
│       ├── main.py                     ✏️ обновить
│       ├── butler_handler.py           ⭐ новый handler
│       └── existing_handlers/
│           ├── tasks.py                ✏️ упростить
│           └── channels.py             ✏️ упростить
│
└── config/
    ├── settings.py
    ├── logging_config.py
    └── constants.py

tests/
├── unit/
│   ├── test_butler_orchestrator.py
│   ├── test_handlers/
│   ├── test_mistral_client.py
│   └── test_tools_registry.py
├── integration/
│   ├── test_butler_e2e.py
│   ├── test_task_creation_flow.py
│   └── conftest.py
└── e2e/
    └── test_telegram_butler.py

docs/
├── ARCHITECTURE.md
├── API.md
├── DEPLOYMENT.md
├── CONTRIBUTING.md
└── CHANGELOG.md

monitoring/
├── prometheus.yml
└── grafana/
    └── dashboards/
        └── butler_dashboard.json

infra/
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

---

## 🎯 Cursor Instructions (для .cursorrules)

Создайте `.cursorrules` файл в корне проекта:

```yaml
# .cursorrules

rules:
  - name: Python Zen Writer
    files: ["src/**/*.py", "tests/**/*.py"]
    priority: high
    triggers:
      - "def "
      - "class "
      - "async "
    instructions: |
      Все функции должны быть explicit, simple, readable.
      - Макс 40 строк на функцию
      - Имена переменных осмысленные
      - Docstring по Google-стилю
      - Обработка ошибок явная

  - name: Chief Architect
    files: ["src/**/*.py"]
    priority: high
    triggers:
      - "class "
      - "import "
    instructions: |
      Соблюдай SOLID, DRY, слоистую архитектуру.
      - Каждый класс = одна ответственность
      - Зависимости через DI
      - Контракты через интерфейсы

  - name: AI Reviewer
    files: ["src/**", "docs/**"]
    priority: medium
    triggers:
      - any file change
    instructions: |
      Проверь:
      - Функции не длиннее 40 строк
      - Token cost <2048 на функцию
      - Нет God Methods

  - name: QA/TDD Reviewer
    files: ["tests/**"]
    priority: high
    triggers:
      - "def test_"
      - "import pytest"
    instructions: |
      - Unit tests с mock'ами
      - Integration tests с docker
      - E2E tests через aiogram
      - Coverage >80%

  - name: DevOps Engineer
    files: ["docker-compose.yml", "Dockerfile", ".github/**", ".gitlab-ci.yml"]
    priority: high
    triggers:
      - "FROM "
      - "pipeline"
      - "deploy"
    instructions: |
      - Dockerfile минимальный, безопасный
      - CI/CD автоматизирован
      - Мониторинг настроен (Prometheus/Grafana)
      - Secrets только через env

  - name: Technical Writer
    files: ["docs/**", "README.md", "src/**"]
    priority: medium
    triggers:
      - "docstring"
      - "README"
      - "API"
    instructions: |
      - Docstring в Google-стиле
      - README с примерами
      - API документация актуальна

  - name: ML Engineer
    files: ["src/ml/**", "src/infrastructure/llm/**"]
    priority: medium
    triggers:
      - "import torch"
      - "import transformers"
      - "mistral"
    instructions: |
      - Reproducibility (seeds)
      - Versioning моделей
      - Мониторинг метрик

globalRules:
  - "PEP8 везде"
  - "Type hints обязательны"
  - "Нет глобальных переменных"
  - "Graceful error handling"
  - "Логирование на каждом шаге"
```

---

## 📅 Timeline (Итого ~2-3 недели)

| Phase | Task | Дни | Cursor Rules | 
|-------|------|------|-------------|
| 0 | Analysis | 1 | AI Reviewer, Chief Architect |
| 1 | Domain Layer | 2-3 | Python Zen, Chief Architect, Technical Writer |
| 2 | Infrastructure | 2 | Python Zen, DevOps |
| 3 | Application | 2 | Python Zen, Chief Architect |
| 4 | Presentation | 1-2 | Python Zen, QA/TDD |
| 5 | Testing | 2-3 | QA/TDD (parallel) |
| 6 | Documentation | 2 | Technical Writer (parallel) |
| 7 | DevOps | 2 | DevOps Engineer (parallel) |

**Total:** ~14-18 дней с Cursor

---

## ✅ Success Criteria

После завершения у вас должно быть:

- ✅ Butler Agent работает со всеми 3 use case
- ✅ 80%+ test coverage
- ✅ Code качество: PEP8, type hints, docstrings
- ✅ Architecture: SOLID, слои, DI
- ✅ Документация полная (архитектура, API, deployment)
- ✅ DevOps: Docker, CI/CD, мониторинг
- ✅ No technical debt (AI Reviewer согласен)

---

## 🚀 Quick Start для Cursor

```bash
# 1. Copy this plan to .md file
cp butler_cursor_plan.md docs/CURSOR_PLAN.md

# 2. Create .cursorrules
cat > .cursorrules << 'EOF'
[вставить содержимое .cursorrules выше]
EOF

# 3. Дать Cursor инструкцию
"Выполни PHASE 1: Domain Layer следуя butler_cursor_plan.md и правилам из .cursorrules"

# 4. Cursor создаст код, ты review + merge
```

---

## 📌 Key Points

1. **ФАЗОВОСТЬ** — Cursor работает на одну phase за раз
2. **CURSOR RULES** — Все rules автоматически проверяют код
3. **TESTING** — Параллельно с каждой фазой (QA/TDD rule)
4. **DOCUMENTATION** — Вместе с кодом (Technical Writer rule)
5. **DEVOPS** — С самого начала (DevOps rule для каждого Dockerfile)

Cursor будет автоматически:
- ✅ Проверять PEP8, type hints
- ✅ Требовать docstring'и
- ✅ Валидировать архитектуру (SOLID)
- ✅ Создавать тесты
- ✅ Генерировать документацию

**Готово к использованию! 🎉**
