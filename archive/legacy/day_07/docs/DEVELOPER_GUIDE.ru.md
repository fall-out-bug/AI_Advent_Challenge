# Руководство разработчика

[English](DEVELOPER_GUIDE.md) | [Русский](DEVELOPER_GUIDE.ru.md)

Это руководство предоставляет комплексную информацию для разработчиков, работающих с мульти-агентной системой StarCoder.

## Содержание

- [Настройка окружения разработки](#настройка-окружения-разработки)
- [Архитектура проекта](#архитектура-проекта)
- [Организация кода](#организация-кода)
- [Workflow разработки](#workflow-разработки)
- [Стратегия тестирования](#стратегия-тестирования)
- [Советы по отладке](#советы-по-отладке)
- [Руководящие принципы вклада](#руководящие-принципы-вклада)
- [Оптимизация производительности](#оптимизация-производительности)
- [Соображения безопасности](#соображения-безопасности)

## Настройка окружения разработки

### Предварительные требования

- Python 3.10+
- Docker и Docker Compose
- NVIDIA GPU (для модели StarCoder)
- Poetry (для управления зависимостями)
- Git

### Настройка локальной разработки

1. **Клонирование репозитория:**
   ```bash
   git clone <repository-url>
   cd AI_Challenge/day_07
   ```

2. **Установка Poetry:**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. **Установка зависимостей:**
   ```bash
   poetry install
   ```

4. **Настройка переменных окружения:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env с вашим HuggingFace токеном
   ```

5. **Запуск сервиса StarCoder:**
   ```bash
   cd ../local_models
   docker-compose up -d starcoder-chat
   ```

6. **Запуск сервисов агентов:**
   ```bash
   cd ../day_07
   make start
   ```

### Конфигурация IDE

#### VS Code

Рекомендуемые расширения:
- Python
- Pylance
- Black Formatter
- isort
- Docker
- GitLens

Настройки (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": ["--max-line-length=100"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## Архитектура проекта

### Высокоуровневая архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │    │  Code Generator │    │  Code Reviewer  │
│                 │    │     Agent       │    │     Agent       │
│  - Coordinates  │◄──►│  - Generates    │◄──►│  - Reviews      │
│  - Manages      │    │  - Creates      │    │  - Analyzes     │
│  - Saves        │    │  - Validates    │    │  - Scores       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Shared SDK     │
                    │  - StarCoder    │
                    │  - Mistral      │
                    │  - Qwen         │
                    │  - TinyLlama    │
                    └─────────────────┘
```

### Компоненты системы

#### 1. Orchestrator (orchestrator.py)
- **Назначение**: Координация workflow между агентами
- **Основные функции**:
  - Управление жизненным циклом задач
  - Координация между генератором и ревьюером
  - Сохранение результатов
  - Сбор статистики
  - Обработка ошибок

#### 2. Code Generator Agent (agents/core/code_generator.py)
- **Назначение**: Генерация Python кода и тестов
- **Основные функции**:
  - Создание функций по описанию
  - Генерация комплексных тестов
  - Валидация сгенерированного кода
  - Рефайнинг существующего кода

#### 3. Code Reviewer Agent (agents/core/code_reviewer.py)
- **Назначение**: Анализ качества кода
- **Основные функции**:
  - Анализ качества кода
  - Проверка соответствия PEP8
  - Оценка покрытия тестами
  - Расчет сложности кода

#### 4. Communication Layer (communication/)
- **Назначение**: HTTP коммуникация между агентами
- **Основные функции**:
  - HTTP клиент с retry логикой
  - Валидация запросов/ответов
  - Обработка ошибок сети

#### 5. API Services (agents/api/)
- **Назначение**: REST API для агентов
- **Основные функции**:
  - FastAPI endpoints
  - Health checks
  - Статистика производительности

## Организация кода

### Структура директорий

```
day_07/
├── agents/                 # Агенты системы
│   ├── api/              # FastAPI сервисы
│   │   ├── generator_api.py
│   │   └── reviewer_api.py
│   └── core/             # Ядро агентов
│       ├── base_agent.py
│       ├── code_generator.py
│       ├── code_reviewer.py
│       └── model_client_adapter.py
├── communication/         # Слой коммуникации
│   ├── agent_client.py
│   └── message_schema.py
├── prompts/              # Шаблоны промптов
│   ├── generator_prompts.py
│   └── reviewer_prompts.py
├── tests/                # Тесты
│   ├── test_generator.py
│   ├── test_reviewer.py
│   ├── test_orchestrator.py
│   └── integration/
├── examples/             # Примеры использования
├── orchestrator.py       # Оркестратор workflow
├── main.py              # CLI интерфейс
├── demo.py              # Демонстрационные примеры
├── Dockerfile           # Docker образ
├── docker-compose*.yml  # Конфигурации развертывания
├── pyproject.toml       # Зависимости Poetry
├── Makefile             # Команды разработки
└── constants.py         # Константы конфигурации
```

### Принципы организации

1. **Разделение ответственности**: Каждый модуль имеет четко определенную ответственность
2. **Инкапсуляция**: Внутренние детали скрыты за интерфейсами
3. **Композиция**: Компоненты собираются из более мелких частей
4. **Тестируемость**: Каждый компонент может быть протестирован изолированно

## Workflow разработки

### Ежедневный workflow

1. **Обновление кода:**
   ```bash
   git pull origin main
   ```

2. **Активация окружения:**
   ```bash
   poetry shell
   ```

3. **Запуск тестов:**
   ```bash
   make test
   ```

4. **Разработка функций:**
   - Создайте ветку для новой функции
   - Реализуйте изменения
   - Добавьте тесты
   - Запустите линтеры

5. **Коммит изменений:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature-branch
   ```

### Команды разработки

```bash
# Установка зависимостей
make install

# Запуск линтеров
make lint

# Форматирование кода
make format

# Проверка типов
make type-check

# Запуск тестов
make test

# Запуск тестов с покрытием
make test-coverage

# Запуск только unit тестов
make test-unit

# Запуск только integration тестов
make test-integration

# Запуск демо
make demo

# Запуск сервисов
make start

# Остановка сервисов
make stop

# Очистка
make clean
```

## Стратегия тестирования

### Типы тестов

#### 1. Unit тесты
- **Назначение**: Тестирование отдельных функций и классов
- **Расположение**: `tests/test_*.py`
- **Пример**:
  ```python
  def test_code_generator_generate():
      generator = CodeGeneratorAgent()
      result = generator.generate("Create a fibonacci function")
      assert result.code is not None
      assert "def fibonacci" in result.code
  ```

#### 2. Integration тесты
- **Назначение**: Тестирование взаимодействия между компонентами
- **Расположение**: `tests/integration/`
- **Пример**:
  ```python
  def test_orchestrator_workflow():
      orchestrator = MultiAgentOrchestrator()
      request = OrchestratorRequest(task_description="Create a calculator")
      result = await orchestrator.process_task(request)
      assert result.success
      assert result.generated_code is not None
  ```

#### 3. API тесты
- **Назначение**: Тестирование REST API endpoints
- **Расположение**: `tests/test_api.py`
- **Пример**:
  ```python
  def test_generator_api_generate():
      response = client.post("/generate", json={
          "task_description": "Create a fibonacci function"
      })
      assert response.status_code == 200
      assert "code" in response.json()
  ```

### Покрытие тестами

Цель: **80%+ покрытие кода**

```bash
# Запуск тестов с покрытием
make test-coverage

# Генерация HTML отчета
coverage html
open htmlcov/index.html
```

### Моки и фикстуры

```python
# Пример мока для тестирования
@pytest.fixture
def mock_model_client():
    with patch('agents.core.model_client_adapter.ModelClientAdapter') as mock:
        mock.return_value.generate.return_value = "def fibonacci(n): return n"
        yield mock
```

## Советы по отладке

### Логирование

```python
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Использование в коде
logger.info("Processing task: %s", task_description)
logger.error("Failed to generate code: %s", str(e))
```

### Отладка агентов

```bash
# Просмотр логов агентов
docker-compose logs -f generator-agent
docker-compose logs -f reviewer-agent

# Отладка с помощью pdb
python -m pdb main.py "Create a fibonacci function"
```

### Отладка API

```bash
# Тестирование endpoints
curl -X POST http://localhost:9001/generate \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Create a fibonacci function"}'

# Проверка health checks
curl http://localhost:9001/health
curl http://localhost:9002/health
```

### Общие проблемы

1. **Модель не загружается**:
   - Проверьте доступность GPU
   - Убедитесь в правильности HF_TOKEN
   - Проверьте свободное место на диске

2. **Агенты не отвечают**:
   - Проверьте статус Docker контейнеров
   - Убедитесь в доступности портов
   - Проверьте логи на ошибки

3. **Медленная генерация**:
   - Проверьте использование GPU
   - Убедитесь в достаточности RAM
   - Рассмотрите использование более быстрой модели

## Руководящие принципы вклада

### Процесс вклада

1. **Fork репозитория**
2. **Создайте ветку функции**:
   ```bash
   git checkout -b feature/new-feature
   ```

3. **Реализуйте изменения**:
   - Следуйте существующим паттернам кода
   - Добавьте тесты для новой функциональности
   - Обновите документацию при необходимости

4. **Запустите тесты**:
   ```bash
   make test
   make lint
   make type-check
   ```

5. **Создайте pull request**:
   - Опишите изменения
   - Укажите связанные issues
   - Добавьте скриншоты для UI изменений

### Стандарты кода

#### Python

```python
# Используйте type hints
def generate_code(task_description: str, model_name: str) -> GenerationResult:
    """Generate code based on task description.
    
    Args:
        task_description: Description of the task
        model_name: Name of the model to use
        
    Returns:
        GenerationResult with generated code and metadata
    """
    pass

# Следуйте PEP 8
def calculate_complexity(code: str) -> int:
    """Calculate cyclomatic complexity of code."""
    return len([line for line in code.split('\n') 
                if 'if ' in line or 'for ' in line or 'while ' in line])
```

#### Документация

```python
class CodeGeneratorAgent:
    """Agent responsible for generating Python code and tests.
    
    This agent uses language models to generate Python functions
    based on natural language descriptions. It also creates
    comprehensive tests for the generated code.
    
    Attributes:
        model_client: Client for interacting with language models
        prompt_templates: Templates for generating prompts
    """
    
    def __init__(self, model_client: ModelClientAdapter):
        """Initialize the code generator agent.
        
        Args:
            model_client: Client for model interaction
        """
        self.model_client = model_client
```

### Коммиты

Используйте conventional commits:

```bash
# Типы коммитов
feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting changes
refactor: code refactoring
test: add or update tests
chore: maintenance tasks

# Примеры
git commit -m "feat: add support for Mistral model"
git commit -m "fix: resolve memory leak in orchestrator"
git commit -m "docs: update API documentation"
```

## Оптимизация производительности

### Профилирование

```python
import cProfile
import pstats

# Профилирование функции
def profile_generation():
    generator = CodeGeneratorAgent()
    cProfile.run('generator.generate("Create a fibonacci function")', 'profile.stats')
    
    # Анализ результатов
    stats = pstats.Stats('profile.stats')
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

### Оптимизация памяти

```python
# Использование генераторов для больших данных
def process_large_dataset(data):
    for item in data:  # Вместо data[:1000]
        yield process_item(item)

# Очистка ресурсов
class ModelClient:
    def __del__(self):
        if hasattr(self, 'model'):
            del self.model
```

### Кэширование

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_complexity(code_hash: str) -> int:
    """Calculate code complexity with caching."""
    # Implementation here
    pass
```

### Асинхронное программирование

```python
import asyncio

async def process_multiple_tasks(tasks: List[str]) -> List[GenerationResult]:
    """Process multiple tasks concurrently."""
    results = await asyncio.gather(*[
        generate_code(task) for task in tasks
    ])
    return results
```

## Соображения безопасности

### Безопасность кода

1. **Валидация входных данных**:
   ```python
   def validate_task_description(description: str) -> bool:
       if not description or len(description) > 1000:
           return False
       # Проверка на вредоносный код
       dangerous_patterns = ['import os', 'subprocess', 'eval']
       return not any(pattern in description.lower() for pattern in dangerous_patterns)
   ```

2. **Санитизация вывода**:
   ```python
   def sanitize_generated_code(code: str) -> str:
       # Удаление потенциально опасных импортов
       lines = code.split('\n')
       safe_lines = [line for line in lines 
                     if not line.strip().startswith(('import os', 'import subprocess'))]
       return '\n'.join(safe_lines)
   ```

### Безопасность контейнеров

1. **Non-root пользователи**:
   ```dockerfile
   RUN adduser --disabled-password --gecos '' appuser
   USER appuser
   ```

2. **Минимальные образы**:
   ```dockerfile
   FROM python:3.10-slim as builder
   # Multi-stage build для минимального размера
   ```

3. **Resource limits**:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

### Безопасность API

1. **Rate limiting**:
   ```python
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/generate")
   @limiter.limit("10/minute")
   async def generate_code(request: Request, task: TaskRequest):
       pass
   ```

2. **Валидация запросов**:
   ```python
   from pydantic import BaseModel, validator
   
   class TaskRequest(BaseModel):
       task_description: str
       
       @validator('task_description')
       def validate_description(cls, v):
           if len(v) > 1000:
               raise ValueError('Task description too long')
           return v
   ```

### Мониторинг безопасности

```python
import logging

# Логирование подозрительной активности
def log_security_event(event_type: str, details: dict):
    logger.warning(f"Security event: {event_type}", extra=details)

# Проверка на аномалии
def detect_anomalies(request_count: int, time_window: int):
    if request_count > 100:  # Более 100 запросов в минуту
        log_security_event("high_request_rate", {
            "count": request_count,
            "window": time_window
        })
```

## Заключение

Это руководство предоставляет основу для эффективной разработки мульти-агентной системы StarCoder. Следуйте этим принципам и практикам для создания высококачественного, безопасного и поддерживаемого кода.

Для получения дополнительной информации обратитесь к:
- [Архитектурной документации](ARCHITECTURE.md)
- [Руководству по развертыванию](DEPLOYMENT.md)
- [Руководству по устранению неполадок](TROUBLESHOOTING.md)
