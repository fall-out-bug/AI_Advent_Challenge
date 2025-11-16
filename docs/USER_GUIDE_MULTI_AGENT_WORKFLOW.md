# User Guide: Multi-Agent Workflow with Cursor

Полная инструкция по использованию улучшенных Cursor агентов для разработки новых Epics/Days.

---

## Таблица содержания

1. [Обзор](#обзор)
2. [Инициализация агентов](#инициализация-агентов)
3. [Полный цикл разработки Epic](#полный-цикл-разработки-epic)
4. [Handoff между агентами](#handoff-между-агентами)
5. [Управление контекстом](#управление-контекстом)
6. [Примеры реальных сеансов](#примеры-реальных-сеансов)
7. [Troubleshooting](#troubleshooting)

---

## Обзор

Ты управляешь 5 Cursor агентами, которые работают в последовательности:

```
[ANALYST] → [ARCHITECT] → [TECH LEAD] → [DEVELOPER] → [REVIEWER]
   ↓            ↓             ↓            ↓            ↓
 Требования  Архитектура  План       Код & Тесты   Проверка
```

Каждый агент:
- Знает свою роль и ответственность
- Имеет доступ к **day_capabilities.md** (знает, какие техники он может использовать)
- Использует **rag_queries.md** для поиска аналогичных решений из прошлого
- Следует **handoff_contracts.md** для формата input/output
- Управляет контекстом через **context_limits.md**

---

## Инициализация агентов

### Требуемая структура документации

Перед стартом убедись, что у тебя есть в проекте:

```
docs/
├── roles/
│   ├── CURSOR_INITIALIZATION.md       # Entry point для всех агентов
│   ├── analyst/
│   │   ├── role_definition.md
│   │   ├── day_capabilities.md        # Обновляется при новых Days
│   │   ├── rag_queries.md
│   │   └── examples/
│   ├── architect/
│   ├── tech_lead/
│   ├── developer/
│   └── reviewer/
├── operational/
│   ├── context_limits.md
│   ├── handoff_contracts.md
│   └── shared_infra.md
└── epics/
    ├── ep_23/                         # Новый epic
    │   ├── requirements.md
    │   ├── architecture.md
    │   ├── plan.md
    │   └── reviews/
    └── ...
```

---

### Инициализация каждого агента

#### Шаг 1: Создай новое agentное окно в Cursor

1. Открой Cursor IDE
2. Нажми кнопку "Agent" (верхняя часть интерфейса)
3. Выбери роль из списка (Analyst, Architect, Tech Lead, Developer, Reviewer)

#### Шаг 2: Загрузи спецификацию роли

Скопируй и вставь этот инициализирующий промпт:

```plaintext
I am an [ROLE] agent. Please load:

1. docs/roles/CURSOR_INITIALIZATION.md - Understand the initialization process
2. docs/roles/[ROLE]/role_definition.md - My core role and responsibilities
3. docs/roles/[ROLE]/day_capabilities.md - Techniques I've mastered from Days 1-22
4. docs/roles/[ROLE]/rag_queries.md - How I search for past solutions
5. docs/operational/context_limits.md - My token budget and compression strategy
6. docs/operational/handoff_contracts.md - Input/output formats
7. docs/operational/shared_infra.md - Infrastructure and connections
8. docs/roles/[ROLE]/examples/ - Recent examples of similar work

After loading, summarize:
- Your purpose and responsibilities
- Which Days you've mastered
- Your token budget and management strategy
- Example input/output formats
- Ready to accept Epic assignment
```

**Замени [ROLE] на:**
- `analyst`
- `architect`
- `tech_lead`
- `developer`
- `reviewer`

#### Шаг 3: Агент готов к работе

Агент выведет краткое резюме своих возможностей и ждёт инструкции.

---

## Полный цикл разработки Epic

### День разработки нового Epic (например, EP23 / EP24)

#### Фаза 1: Analyst — Сбор требований (2-3 часа)

**Промпт:**
```plaintext
We are starting Epic 23: "Observability & Benchmark Enablement" (or Epic 24: "Repository Hygiene & De-Legacy").

Your task (as Analyst):
1. Gather requirements from stakeholders (simulated: answer my questions or use provided context)
2. Document 10-15 functional and non-functional requirements
3. Ensure clarity_score >= 0.80 using Day 3 conversation stopping pattern
4. Use Day 22 RAG queries to find similar requirements from EP15, EP19
5. Include rag_citations in your output
6. Output JSON in handoff_contracts.md format: Analyst → Architect

Requirements context:
- Domain: Payment processing
- Constraints: PCI compliance, PostgreSQL mandatory
- Timeline: 3-month MVP

Begin requirement gathering.
```

**Что ты делаешь:**
- Задаёшь вопросы, которые хочешь уточнить
- Агент применяет Day 3 stopping conditions (знает, когда остановиться)
- Агент применяет Day 8 token management (отслеживает размер контекста)
- Агент применяет Day 15 compression (сжимает диалог если нужно)
- Агент применяет Day 22 RAG (ищет аналогичные требования)

**Выход:**
```json
{
  "epic_id": "EP23",
  "requirements": [
    {
      "id": "REQ-001",
      "text": "System must process credit card payments",
      "type": "functional",
      "priority": "high",
      "acceptance_criteria": [...]
    },
    ...
  ],
  "clarity_score": 0.85,
  "rag_citations": ["EP15_req#42", "EP19_req#78"],
  "notes": "..."
}
```

**Ты:**
- Проверяешь clarity_score (должен быть >= 0.80)
- Проверяешь наличие rag_citations
- Сохраняешь JSON в `docs/epics/ep_23/requirements.md`
- Переходишь к Architect

---

#### Фаза 2: Architect — Проектирование архитектуры (2-3 часа)

**Подготовка:**
1. Скопируй JSON output от Analyst в буфер обмена
2. Открой новое agentное окно для Architect

**Промпт:**
```plaintext
I am an Architect agent. Requirements have been gathered for EP23.

Your task:
1. Load the Analyst's output (I'll provide below):
[Вставь JSON from Analyst]

2. Design architecture following Clean Architecture principles
3. Use Day 4-5 temperature strategies (0.0 for deterministic components, 0.7 for exploratory)
4. Use Day 12 composition pattern to structure components
5. Use Day 22 RAG to find similar architecture decisions from EP15, EP19
6. Create MADR (Architecture Decision Records) for key trade-offs
7. Output JSON in handoff_contracts.md format: Architect → Tech Lead
8. If requirements unclear, ask Analyst for clarification (loop back)

Begin architecture design.
```

**Что агент делает:**
- Анализирует требования
- Проектирует архитектуру (компоненты, слои, потоки данных)
- Ищет в RAG похожие решения
- Документирует trade-offs
- Выводит JSON с архитектурой

**Выход:**
```json
{
  "epic_id": "EP23",
  "architecture": {
    "pattern": "Clean Architecture with REST API",
    "components": [...],
    "database": "PostgreSQL with encryption",
    "rag_citations": ["EP15_arch#decision-003"]
  },
  "questions_for_analyst": [] // if empty, ready for Tech Lead
}
```

**Ты:**
- Сохраняешь JSON в `docs/epics/ep_23/architecture.md`
- Проверяешь, нет ли questions_for_analyst (если есть, вернись к Analyst)
- Переходишь к Tech Lead

---

#### Фаза 3: Tech Lead — Создание плана (1-2 часа)

**Промпт:**
```plaintext
I am a Tech Lead agent. Architecture is ready for EP23.

Your task:
1. Load Analyst requirements and Architect design (I'll provide):
   - Requirements: [JSON from Analyst]
   - Architecture: [JSON from Architect]

2. Create staged implementation plan
3. Use Day 8 token awareness to break large tasks into Developer-sized chunks
4. Use Day 15 compression: summarize complex requirements for each stage
5. Use Day 17 pipeline pattern: separate stages by concerns (DB → API → Frontend)
6. Define CI/CD gates and test requirements
7. Use Day 22 RAG to find similar plans from EP15, EP19
8. Output JSON in handoff_contracts.md format: Tech Lead → Developer

Include:
- Stages (3-5 stages typically)
- Definition of Done per stage
- CI gates (linting, testing, coverage)
- Risk mitigation
- Time estimates

Begin planning.
```

**Выход:**
```json
{
  "epic_id": "EP23",
  "plan": {
    "stages": [
      {
        "stage": 1,
        "name": "Database & API Foundation",
        "tasks": ["Create schema", "Setup ORM", "Implement endpoints"],
        "definition_of_done": ["Schema created", "API tests pass", "Coverage >= 80%"],
        "time_estimate": "2 days"
      },
      ...
    ],
    "ci_gates": ["flake8", "pytest", "coverage >= 80%"],
    "rag_citations": ["EP15_plan#stage-1"]
  }
}
```

**Ты:**
- Сохраняешь JSON в `docs/epics/ep_23/plan.md`
- Проверяешь реалистичность оценок
- Переходишь к Developer

---

#### Фаза 4: Developer — Написание кода (3-5 часов)

**Промпт:**
```plaintext
I am a Developer agent. Plan is ready for EP23 Stage 1.

Your task:
1. Load plan from Tech Lead:
   [JSON from Tech Lead]

2. Implement Stage 1: Database & API Foundation
3. Write tests first (TDD pattern from Day 2)
4. Use Day 2 structured output: provide code in JSON format with filename, language, content
5. Use Day 8 token management: if context gets large, summarize previous progress
6. Use Day 13 & Day 23 environment integration: assume shared infra (Mongo, Prometheus, Loki) managed via `scripts/ci/bootstrap_shared_infra.py` and `make day-23-up/down`, Python, pytest
7. For Epic 24, follow cluster plans (A–E) and DI patterns:
   - Mongo & async infra via `MongoClientFactory` and `mongodb_database` fixtures
   - Summarization via `SummarizerService` (`AdaptiveSummarizer`, `MapReduceSummarizer` + `ChunkSummarizationParams`)
   - Butler/MCP orchestration via public APIs only
   - LLM clients via `LLMClient` Protocol and config‑driven URLs
   - Telegram workers via `TelegramAdapter` and `ChannelNormalizer.to_canonical_form()`
7. Output code artifacts + tests following Developer output format

Include:
- Python files (schema.py, models.py, handlers.py)
- Test files (test_schema.py, test_handlers.py)
- All code with type hints
- Documentation strings

Begin implementation.
```

**Выход:**
```json
{
  "epic_id": "EP23",
  "stage": 1,
  "artifacts": [
    {
      "filename": "src/models/payment.py",
      "language": "python",
      "content": "..."
    },
    ...
  ],
  "tests": [
    {
      "filename": "tests/test_payment.py",
      "content": "..."
    },
    ...
  ],
  "coverage": 0.85,
  "ci_gates_passed": ["flake8", "pytest", "coverage"],
  "decisions": [
    {
      "decision": "Used Stripe as payment provider",
      "reason": "PCI compliance out of the box"
    }
  ]
}
```

**Ты:**
- Сохраняешь код в соответствующих файлах проекта
- Проверяешь тесты проходят локально
- Сохраняешь JSON в `docs/epics/ep_23/code_artifacts.md`
- Переходишь к Reviewer

---

#### Фаза 5: Reviewer — Проверка и валидация (1-2 часа)

**Промпт:**
```plaintext
I am a Reviewer agent. Code is ready for EP23 Stage 1.

Your task:
1. Load all artifacts:
   - Requirements: [from Analyst]
   - Architecture: [from Architect]
   - Plan: [from Tech Lead]
   - Code: [from Developer]

2. Validate:
   - Are requirements met? (map each requirement to code)
   - Does code follow architecture?
   - Are tests adequate (>80% coverage)?
   - Are acceptance criteria satisfied?

3. Use Day 22 RAG: find similar issues from EP15, EP19 reviews
4. Use Day 23 observability: log quality metrics
5. Output review findings: approve or request changes

Output format:
- review_findings: [list of issues/strengths]
- approval: true/false
- requirements_coverage: 0.95 (percentage of requirements met)
- architecture_compliance: 0.95
- test_coverage: 0.85
- rag_citations: [similar issues from past]
- recommendations: [improvements]
```

**Выход:**
```json
{
  "epic_id": "EP23",
  "approval": true,
  "requirements_coverage": 0.95,
  "architecture_compliance": 0.95,
  "test_coverage": 0.85,
  "review_findings": [
    {
      "type": "strength",
      "message": "Great use of type hints and docstrings"
    },
    {
      "type": "issue",
      "severity": "warning",
      "message": "Missing error handling for payment API failures"
    }
  ],
  "recommendations": [...]
}
```

**Ты:**
- Читаешь review findings
- Если approval: true → Stage 1 готов к продакшену
- Если approval: false → вернись к Developer для доработок
- Сохраняешь review в `docs/epics/ep_23/reviews/`

---

## Handoff между агентами

### Как передавать данные между агентами

#### Формат передачи

Каждый агент **выводит JSON**, который становится входом для следующего.

**Структура handoff JSON:**

```json
{
  "metadata": {
    "epic_id": "EP23",
    "from_agent": "analyst",
    "to_agent": "architect",
    "timestamp": "2025-11-15T14:30:00Z",
    "version": "1.0"
  },
  "payload": {
    // Основной контент (requirements, architecture, plan, code)
  },
  "validation": {
    "status": "ready",  // "ready" или "needs_revision"
    "issues": [],       // Если есть
    "clarity_score": 0.85  // Если applicable
  },
  "citations": {
    "rag_sources": ["EP15_req#42", "EP19_arch#decision-003"],
    "confidence": 0.95
  }
}
```

#### Практический способ передачи

1. **Копирование в буфер обмена:**
   - Агент выводит JSON (обычно много строк)
   - Ты выделяешь весь JSON
   - Копируешь (Ctrl+C / Cmd+C)

2. **Вставка в следующий агент:**
   - Открываешь окно следующего агента
   - Вставляешь JSON (Ctrl+V / Cmd+V)
   - В промпте: "Here's the input from previous agent:" [вставка JSON]

3. **Альтернатива — сохранение в файл:**
   ```bash
   # Копируешь JSON в файл
   docs/epics/ep_23/requirements.json
   docs/epics/ep_23/architecture.json
   docs/epics/ep_23/plan.json

   # Агент загружает: "Load requirements from docs/epics/ep_23/requirements.json"
   ```

---

## Управление контекстом

### Context Limits по ролям

| Роль | Окно | Для работы | RAG | Буфер | Стратегия сжатия |
|------|------|-----------|-----|-------|------------------|
| **Analyst** | 12K | 10K | 2K | - | Day 15 map-reduce |
| **Architect** | 12K | 8K | 3K | 1K | Summarize components |
| **Tech Lead** | 12K | 6K | 4K | 2K | Compress stages |
| **Developer** | 12K | 10K | 1K | 1K | Split into tasks |
| **Reviewer** | 12K | 8K | 3K | 1K | Parallel checks |

### Когда сжимать контекст

Если агент говорит: **"Context approaching limit"** или **"Token usage: 85%+"**

**Действия:**

1. **Попроси сжатие:**
   ```plaintext
   Your context is getting large. Please:
   1. Compress your previous work using Day 15 pattern (map-reduce)
   2. Keep only essential information: decisions, open questions, next steps
   3. Remove intermediate details
   4. Save compressed summary
   ```

2. **Если не помогло:**
   - Сохрани текущий прогресс в файл
   - Перезагрузи агента (новое окно)
   - Загрузи сохранённый прогресс
   - Продолжай с этого места

---

## Примеры реальных сеансов

### Пример 1: Analyst собирает требования для Payment Module

**Ты (в Cursor Analyst agent):**
```
We're building a payment module. Key requirements:
- Support credit cards, PayPal, bank transfers
- PCI compliance required
- Response time < 2 seconds
- 3-month MVP timeline

Please gather additional functional and non-functional requirements.
Use Day 3 stopping pattern: when clarity_score >= 0.80, compile requirements.
```

**Analyst (после 8-10 exchanges):**
```json
{
  "epic_id": "EP23",
  "requirements": [
    {"id": "R-001", "text": "Process credit card payments", "clarity": 0.9},
    {"id": "R-002", "text": "PCI compliance", "clarity": 0.95},
    ...
  ],
  "clarity_score": 0.87,
  "ready_for_handoff": true,
  "rag_citations": ["EP15_req#42", "EP19_req#78"]
}
```

---

### Пример 2: Architect проектирует архитектуру

**Ты (в Cursor Architect agent):**
```
Here are the requirements from Analyst:
[Вставляешь JSON от Analyst]

Design the architecture. Use Day 12 composition to structure components.
```

**Architect (после анализа):**
```json
{
  "architecture": {
    "components": [
      {"name": "PaymentGateway", "responsibility": "Stripe integration"},
      {"name": "TransactionService", "responsibility": "Business logic"},
      {"name": "AuditLogger", "responsibility": "PCI compliance logging"}
    ],
    "layers": ["Presentation", "Application", "Infrastructure"],
    "rag_citations": ["EP15_arch#pattern-payment-gateway"]
  },
  "ready_for_handoff": true
}
```

---

## Troubleshooting

### Проблема 1: Агент "зависла" / не отвечает

**Решение:**
- Нажми Escape или Ctrl+C в Cursor
- Закрой это agentное окно
- Открой новое, перезагрузи контекст

### Проблема 2: Контекст закончился, агент не может продолжить

**Решение:**
- Попроси агента: "Compress all work so far using Day 15 pattern"
- Сохрани сжатое резюме в файл
- Перезагрузи агента с этим резюме

### Проблема 3: Агент выдаёт неправильный JSON

**Решение:**
- Попроси: "Output in valid JSON format only. No markdown, no extra text"
- Если не помогает, скопируй неправильный JSON, исправь вручную

### Проблема 4: RAG query не возвращает результаты

**Решение:**
- Проверь, что MongoDB запущена (`docs/operational/shared_infra.md`)
- Проверь query синтаксис в `rag_queries.md`
- Попроси агента использовать более общую query

### Проблема 5: Агент не знает про новый Day (день)

**Решение:**
- Обновил ли ты `day_capabilities.md` для этой роли?
- Перезагрузи агента (новое окно)
- Вставь обновленный `day_capabilities.md` в промпт вручную

---

## Чеклист: Полный цикл EP23

- [ ] **Day 1:** Analyst собирает требования
  - [ ] clarity_score >= 0.80
  - [ ] rag_citations включены
  - [ ] JSON сохранён в `docs/epics/ep_23/requirements.md`

- [ ] **Day 2:** Architect проектирует архитектуру
  - [ ] Компоненты defined
  - [ ] Decisions документированы
  - [ ] JSON сохранён в `docs/epics/ep_23/architecture.md`

- [ ] **Day 3:** Tech Lead создаёт план
  - [ ] Stages defined (3-5)
  - [ ] CI gates specified
  - [ ] JSON сохранён в `docs/epics/ep_23/plan.md`

- [ ] **Days 4-5:** Developer реализует Stage 1
  - [ ] Code написан (TDD)
  - [ ] Tests passed
  - [ ] Coverage >= 80%
  - [ ] JSON сохранён в `docs/epics/ep_23/code_artifacts.md`

- [ ] **Day 6:** Reviewer валидирует
  - [ ] Requirements covered
  - [ ] Architecture compliance checked
  - [ ] Tests coverage verified
  - [ ] Approval granted
  - [ ] Review сохранён в `docs/epics/ep_23/reviews/`

- [ ] **Final:** Update progress tracking
  - [ ] `docs/progress.md` обновлён (EP23 completed)
  - [ ] Git commit: "EP23: Payment module implementation complete"

---

**Готово! Ты готов использовать многоагентную систему в Cursor.** 🚀
