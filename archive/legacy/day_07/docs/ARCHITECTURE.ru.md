# Архитектурная документация

[English](ARCHITECTURE.md) | [Русский](ARCHITECTURE.ru.md)

Этот документ предоставляет комплексный обзор архитектуры мульти-агентной системы StarCoder.

## Содержание

- [Обзор системы](#обзор-системы)
- [Детали компонентов](#детали-компонентов)
- [Поток данных](#поток-данных)
- [Точки интеграции](#точки-интеграции)
- [Архитектурные решения](#архитектурные-решения)
- [Точки расширения](#точки-расширения)
- [Технологический стек](#технологический-стек)
- [Архитектура развертывания](#архитектура-развертывания)

## Обзор системы

Мульти-агентная система StarCoder - это распределенная микросервисная архитектура, предназначенная для автоматической генерации и ревью Python кода. Система состоит из специализированных AI агентов, которые работают вместе для создания высококачественного, протестированного Python кода.

### Ключевые принципы

1. **Разделение ответственности**: Каждый агент имеет единственную ответственность
2. **Слабая связанность**: Агенты общаются через HTTP API
3. **Масштабируемость**: Компоненты могут масштабироваться независимо
4. **Отказоустойчивость**: Система продолжает работать при отказе отдельных компонентов
5. **Наблюдаемость**: Комплексное логирование и мониторинг

### Высокоуровневая архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        Клиентский слой                           │
├─────────────────────────────────────────────────────────────────┤
│  CLI (main.py)  │  Demo (demo.py)  │  Web UI  │  API клиенты    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Слой оркестрации                           │
├─────────────────────────────────────────────────────────────────┤
│                    MultiAgentOrchestrator                       │
│  • Управление workflow  • Обработка ошибок  • Сохранение результатов │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Агент генератора│    │  Агент ревьюера │    │  Слой адаптера  │
│     кода         │    │     кода         │    │     моделей     │
│                  │    │                  │    │                  │
│ • Генерация кода │    │ • Ревью качества │    │ • StarCoder     │
│ • Создание тестов│    │ • Анализ PEP8    │    │ • Mistral       │
│ • Валидация      │    │ • Проверка покрытия│   │ • Qwen          │
│ • Рефайнинг      │    │ • Рекомендации   │    │ • TinyLlama     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Детали компонентов

### 1. Слой оркестрации

#### MultiAgentOrchestrator
- **Расположение**: `orchestrator.py`
- **Назначение**: Координирует весь workflow
- **Ответственности**:
  - Оркестрация workflow
  - Обработка ошибок и восстановление
  - Сохранение результатов
  - Сбор статистики
  - Мониторинг здоровья агентов

**Ключевые методы**:
- `process_task()`: Основное выполнение workflow
- `_generate_code_step()`: Фаза генерации кода
- `_review_code_step()`: Фаза ревью кода
- `_finalize_workflow()`: Обработка результатов

### 2. Слой агентов

#### Агент генератора кода
- **Расположение**: `agents/core/code_generator.py`
- **Назначение**: Генерирует Python код и тесты
- **Ответственности**:
  - Обработка запросов генерации
  - Извлечение кода из ответов модели
  - Генерация комплексных тестов
  - Валидация сгенерированного кода
  - Обработка запросов рефайнинга

**Ключевые методы**:
- `process()`: Основной метод обработки
- `_prepare_prompt()`: Подготовка промпта
- `_call_model_for_code()`: Взаимодействие с моделью
- `_extract_and_validate()`: Обработка ответа
- `validate_generated_code()`: Валидация кода

#### Агент ревьюера кода
- **Расположение**: `agents/core/code_reviewer.py`
- **Назначение**: Ревьюит и анализирует качество кода
- **Ответственности**:
  - Анализ качества кода
  - Проверка соответствия PEP8
  - Оценка покрытия тестами
  - Расчет сложности кода
  - Предоставление рекомендаций

**Ключевые методы**:
- `process()`: Основной метод обработки
- `_prepare_review_prompt()`: Подготовка промпта ревью
- `_call_model_for_review()`: Взаимодействие с моделью
- `_parse_review_response()`: Парсинг ответа ревью
- `_create_quality_metrics()`: Создание метрик качества

### 3. Слой коммуникации

#### AgentClient
- **Расположение**: `communication/agent_client.py`
- **Назначение**: HTTP клиент для меж-агентной коммуникации
- **Ответственности**:
  - HTTP запросы с retry логикой
  - Exponential backoff для устойчивости
  - Обработка таймаутов
  - Логирование запросов и ответов

**Ключевые методы**:
- `_make_request()`: Выполнение HTTP запросов
- `_handle_retry()`: Обработка повторных попыток
- `_log_request()`: Логирование запросов

#### Message Schema
- **Расположение**: `communication/message_schema.py`
- **Назначение**: Pydantic модели для валидации данных
- **Ответственности**:
  - Валидация запросов и ответов
  - Сериализация/десериализация данных
  - Типизация данных

### 4. Слой API

#### Generator API
- **Расположение**: `agents/api/generator_api.py`
- **Назначение**: FastAPI сервис для агента генератора
- **Endpoints**:
  - `POST /generate`: Генерация кода
  - `POST /refine`: Улучшение кода
  - `POST /validate`: Валидация кода
  - `GET /health`: Проверка здоровья
  - `GET /stats`: Статистика производительности

#### Reviewer API
- **Расположение**: `agents/api/reviewer_api.py`
- **Назначение**: FastAPI сервис для агента ревьюера
- **Endpoints**:
  - `POST /review`: Полный ревью кода
  - `POST /analyze-pep8`: Анализ PEP8
  - `POST /analyze-test-coverage`: Анализ покрытия
  - `POST /calculate-complexity`: Расчет сложности
  - `GET /health`: Проверка здоровья
  - `GET /stats`: Статистика производительности

### 5. Слой моделей

#### Model Client Adapter
- **Расположение**: `agents/core/model_client_adapter.py`
- **Назначение**: Адаптер для взаимодействия с языковыми моделями
- **Ответственности**:
  - Унифицированный интерфейс для всех моделей
  - Обработка специфичных для модели настроек
  - Кэширование ответов
  - Обработка ошибок модели

**Поддерживаемые модели**:
- **StarCoder-7B**: Специализирован для генерации кода
- **Mistral-7B**: Высококачественная универсальная модель
- **Qwen-4B**: Быстрые ответы, хорошее качество
- **TinyLlama-1.1B**: Компактная и быстрая

## Поток данных

### 1. Workflow генерации кода

```
1. Клиент → Orchestrator
   ├── TaskRequest (описание задачи)
   ├── model_name (выбранная модель)
   └── reviewer_model_name (модель для ревью)

2. Orchestrator → Generator Agent
   ├── GenerationRequest
   ├── task_description
   └── model_settings

3. Generator Agent → Model
   ├── Prompt (сгенерированный промпт)
   └── Model settings

4. Model → Generator Agent
   ├── Generated code
   ├── Generated tests
   └── Metadata

5. Generator Agent → Orchestrator
   ├── GenerationResult
   ├── code
   ├── tests
   └── validation_status

6. Orchestrator → Reviewer Agent
   ├── ReviewRequest
   ├── code
   └── tests

7. Reviewer Agent → Model
   ├── Review prompt
   └── Code to review

8. Model → Reviewer Agent
   ├── Review analysis
   ├── Quality metrics
   └── Recommendations

9. Reviewer Agent → Orchestrator
   ├── ReviewResult
   ├── quality_score
   ├── pep8_score
   ├── test_coverage
   └── complexity_score

10. Orchestrator → Client
    ├── WorkflowResult
    ├── generated_code
    ├── review_results
    └── statistics
```

### 2. Поток ошибок

```
1. Обнаружение ошибки
   ├── Model timeout
   ├── Network error
   ├── Validation error
   └── Agent failure

2. Обработка ошибки
   ├── Retry logic (exponential backoff)
   ├── Fallback strategies
   ├── Error logging
   └── Graceful degradation

3. Уведомление клиента
   ├── Error message
   ├── Error code
   ├── Suggested actions
   └── Partial results (если доступны)
```

## Точки интеграции

### 1. Интеграция с Shared SDK

```python
# Использование унифицированного интерфейса
from shared.clients.model_client import ModelClient

class ModelClientAdapter:
    def __init__(self, model_name: str):
        self.client = ModelClient(provider=model_name)
    
    async def generate(self, prompt: str) -> str:
        response = await self.client.chat(prompt)
        return response.content
```

### 2. Интеграция с Local Models

```yaml
# docker-compose.yml
services:
  starcoder-chat:
    image: starcoder:latest
    ports:
      - "8003:8000"
    environment:
      - MODEL_NAME=starcoder
      - HF_TOKEN=${HF_TOKEN}
```

### 3. Интеграция с Traefik

```yaml
# docker-compose.traefik.yml
services:
  generator-agent:
    labels:
      - "traefik.http.routers.generator.rule=Host(`generator.localhost`)"
      - "traefik.http.services.generator.loadbalancer.server.port=9001"
```

## Архитектурные решения

### 1. Микросервисная архитектура

**Решение**: Использование отдельных сервисов для каждого агента
**Обоснование**:
- Независимое масштабирование
- Изоляция отказов
- Технологическая гибкость
- Простота развертывания

### 2. HTTP API коммуникация

**Решение**: REST API для меж-агентной коммуникации
**Обоснование**:
- Простота отладки
- Стандартизация
- Поддержка различных языков
- Мониторинг и логирование

### 3. Асинхронная обработка

**Решение**: Использование asyncio для параллельной обработки
**Обоснование**:
- Улучшенная производительность
- Эффективное использование ресурсов
- Масштабируемость
- Отзывчивость системы

### 4. Pydantic валидация

**Решение**: Использование Pydantic для валидации данных
**Обоснование**:
- Автоматическая валидация
- Типизация данных
- Сериализация/десериализация
- Документация API

### 5. Retry логика с exponential backoff

**Решение**: Автоматические повторные попытки с увеличивающимися интервалами
**Обоснование**:
- Устойчивость к временным сбоям
- Предотвращение перегрузки
- Улучшенная надежность
- Graceful degradation

## Точки расширения

### 1. Новые агенты

```python
# Базовый класс для новых агентов
class BaseAgent:
    def __init__(self, model_client: ModelClientAdapter):
        self.model_client = model_client
    
    async def process(self, request: BaseRequest) -> BaseResponse:
        raise NotImplementedError
```

### 2. Новые модели

```python
# Добавление новой модели
MODEL_SPECIFIC_SETTINGS = {
    "new_model": {
        "generator_temperature": 0.3,
        "reviewer_temperature": 0.2,
        "generator_max_tokens": 1500,
        "reviewer_max_tokens": 1200
    }
}
```

### 3. Новые endpoints

```python
# Добавление нового endpoint
@app.post("/new-endpoint")
async def new_endpoint(request: NewRequest):
    # Implementation here
    pass
```

### 4. Новые метрики

```python
# Расширение метрик качества
class QualityMetrics:
    def __init__(self):
        self.pep8_score = 0
        self.test_coverage = 0
        self.complexity_score = 0
        self.new_metric = 0  # Новая метрика
```

## Технологический стек

### Backend

- **Python 3.10+**: Основной язык программирования
- **FastAPI**: Веб-фреймворк для API
- **Pydantic**: Валидация данных и сериализация
- **asyncio**: Асинхронное программирование
- **httpx**: HTTP клиент
- **Poetry**: Управление зависимостями

### AI/ML

- **HuggingFace Transformers**: Интеграция языковых моделей
- **StarCoder-7B**: Основная модель для генерации кода
- **Mistral-7B**: Альтернативная модель
- **Qwen-4B**: Быстрая модель
- **TinyLlama-1.1B**: Компактная модель

### Инфраструктура

- **Docker**: Контейнеризация
- **Docker Compose**: Оркестрация сервисов
- **Traefik**: Reverse proxy и load balancer
- **NVIDIA CUDA**: GPU ускорение
- **Multi-stage builds**: Оптимизация образов

### Тестирование

- **pytest**: Фреймворк тестирования
- **pytest-asyncio**: Асинхронное тестирование
- **pytest-cov**: Покрытие тестами
- **httpx**: HTTP тестирование

### Мониторинг

- **logging**: Структурированное логирование
- **Health checks**: Мониторинг здоровья
- **Statistics**: Сбор метрик производительности

## Архитектура развертывания

### 1. Development Environment

```yaml
# docker-compose.yml
services:
  generator-agent:
    build: .
    ports:
      - "9001:9001"
    environment:
      - MODEL_NAME=starcoder
  
  reviewer-agent:
    build: .
    ports:
      - "9002:9002"
    environment:
      - MODEL_NAME=starcoder
```

### 2. Production Environment

```yaml
# docker-compose.traefik.yml
services:
  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
  
  generator-agent:
    build: .
    labels:
      - "traefik.http.routers.generator.rule=Host(`generator.localhost`)"
      - "traefik.http.services.generator.loadbalancer.server.port=9001"
  
  reviewer-agent:
    build: .
    labels:
      - "traefik.http.routers.reviewer.rule=Host(`reviewer.localhost`)"
      - "traefik.http.services.reviewer.loadbalancer.server.port=9002"
```

### 3. Scaling Configuration

```yaml
# Горизонтальное масштабирование
services:
  generator-agent:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
  
  reviewer-agent:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### 4. Security Configuration

```dockerfile
# Multi-stage build для безопасности
FROM python:3.10-slim as builder
# Build stage

FROM python:3.10-slim as production
# Production stage with non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

## Заключение

Архитектура мульти-агентной системы StarCoder спроектирована для обеспечения высокой производительности, масштабируемости и надежности. Использование микросервисной архитектуры, асинхронной обработки и современных технологий позволяет системе эффективно обрабатывать запросы генерации и ревью кода.

Ключевые преимущества архитектуры:
- **Модульность**: Легкое добавление новых агентов и функций
- **Масштабируемость**: Независимое масштабирование компонентов
- **Надежность**: Отказоустойчивость и graceful degradation
- **Наблюдаемость**: Комплексное логирование и мониторинг
- **Безопасность**: Многоуровневая защита и валидация

Для получения дополнительной информации обратитесь к:
- [Руководству разработчика](DEVELOPER_GUIDE.md)
- [Руководству по развертыванию](DEPLOYMENT.md)
- [Руководству по устранению неполадок](TROUBLESHOOTING.md)
