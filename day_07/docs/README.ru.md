# Мульти-модельная мульти-агентная система

[English](README.md) | [Русский](README.ru.md)

Сложная мульти-агентная система с поддержкой нескольких языковых моделей (StarCoder, Mistral, Qwen, TinyLlama) для автоматической генерации Python кода и его ревью. Система состоит из двух специализированных AI агентов, которые работают вместе для генерации высококачественного Python кода и предоставления комплексных ревью кода.

## 🌟 Особенности

- **Поддержка множественных моделей**: Выбор из StarCoder, Mistral, Qwen или TinyLlama
- **Агент генерации кода**: Генерирует Python функции с комплексными тестами
- **Агент ревью кода**: Анализирует качество кода, соответствие PEP8 и предоставляет рекомендации
- **REST API коммуникация**: Агенты общаются через HTTP API для масштабируемости
- **Docker оркестрация**: Легкое развертывание с Docker Compose
- **Комплексное тестирование**: Unit и integration тесты включены
- **Сохранение результатов**: Все результаты workflow сохраняются для анализа
- **Мониторинг в реальном времени**: Health checks и статистические endpoints
- **Интеграция Shared SDK**: Унифицированный интерфейс для всех языковых моделей

## 🏗️ Архитектура

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

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- NVIDIA GPU (для StarCoder)
- Python 3.10+ (для локальной разработки)
- Poetry (для управления зависимостями)
- Hugging Face токен (для загрузки модели StarCoder)

### Переменные окружения

Перед запуском сервисов необходимо настроить переменные окружения:

1. Скопируйте файл примера окружения:
   ```bash
   cp .env.example .env
   ```

2. Отредактируйте файл `.env` и установите ваш Hugging Face токен и предпочтения моделей:
   ```
   HF_TOKEN=your_actual_huggingface_token_here
   MODEL_NAME=starcoder
   STARCODER_URL=http://localhost:8003/chat
   MISTRAL_URL=http://localhost:8001
   QWEN_URL=http://localhost:8000
   TINYLLAMA_URL=http://localhost:8002
   ```

3. Также настройте директорию local_models:
   ```bash
   cd ../local_models
   cp .env.example .env
   ```
   
   Отредактируйте файл `.env` в local_models:
   ```
   HF_TOKEN=your_actual_huggingface_token_here
   ```

### 1. Запуск сервиса StarCoder

Сначала запустите сервис модели StarCoder:

```bash
cd ../local_models
docker-compose up -d starcoder-chat
```

Дождитесь загрузки модели (это может занять несколько минут при первом запуске).

### 2. Запуск сервисов агентов

```bash
cd day_07
docker-compose up -d
```

Это запустит:
- Агент генератора кода на порту 9001
- Агент ревьюера кода на порту 9002
- Сервис StarCoder на порту 8003

### 3. Запуск демо

```bash
python demo.py
```

## 🤖 Поддержка множественных моделей

Система теперь поддерживает несколько языковых моделей:

- **StarCoder-7B** (по умолчанию): Специализирован для генерации кода
- **Mistral-7B**: Высококачественная универсальная модель
- **Qwen-4B**: Быстрые ответы, хорошее качество
- **TinyLlama-1.1B**: Компактная и быстрая

### Использование разных моделей

```python
# Использование Mistral для генерации
request = OrchestratorRequest(
    task_description="Create a REST API",
    model_name="mistral"
)

# Использование разных моделей для генерации и ревью
request = OrchestratorRequest(
    task_description="Create a REST API",
    model_name="starcoder",
    reviewer_model_name="mistral"
)
```

### Конфигурация моделей

Каждая модель имеет оптимизированные настройки:

```python
MODEL_SPECIFIC_SETTINGS = {
    "starcoder": {
        "generator_temperature": 0.3,
        "reviewer_temperature": 0.2,
        "generator_max_tokens": 1500,
        "reviewer_max_tokens": 1200
    },
    "mistral": {
        "generator_temperature": 0.4,
        "reviewer_temperature": 0.3,
        "generator_max_tokens": 1500,
        "reviewer_max_tokens": 1200
    },
    "qwen": {
        "generator_temperature": 0.3,
        "reviewer_temperature": 0.2,
        "generator_max_tokens": 1200,
        "reviewer_max_tokens": 1000
    },
    "tinyllama": {
        "generator_temperature": 0.2,
        "reviewer_temperature": 0.1,
        "generator_max_tokens": 1000,
        "reviewer_max_tokens": 800
    }
}
```

## 🛠️ Развертывание

### Вариант 1: Bridge Network (простой)

```bash
make start-bridge
```

Это запустит:
- Generator Agent: http://localhost:9001
- Reviewer Agent: http://localhost:9002

### Вариант 2: Traefik Reverse Proxy (продакшн)

```bash
make start-traefik
```

Это запустит:
- Generator Agent: http://generator.localhost
- Reviewer Agent: http://reviewer.localhost
- Traefik Dashboard: http://localhost:8080

### Проверка статуса

```bash
# Проверка здоровья агентов
curl http://localhost:9001/health
curl http://localhost:9002/health

# Статистика агентов
curl http://localhost:9001/stats
curl http://localhost:9002/stats
```

## 📖 Использование

### CLI интерфейс

```bash
# Простая генерация кода
python main.py "Create a function to calculate fibonacci numbers"

# Генерация с конкретной моделью
python main.py "Create a REST API endpoint" --model mistral

# Генерация с разными моделями для генерации и ревью
python main.py "Create a data processing pipeline" --model starcoder --reviewer-model mistral
```

### Python API

```python
import asyncio
from orchestrator import MultiAgentOrchestrator
from communication.message_schema import OrchestratorRequest

async def main():
    orchestrator = MultiAgentOrchestrator()
    
    # Простая генерация
    request = OrchestratorRequest(
        task_description="Create a REST API endpoint",
        model_name="starcoder"
    )
    
    result = await orchestrator.process_task(request)
    print(f"Generated code: {result.generated_code}")
    print(f"Review score: {result.review_score}")
    
    # Разные модели для генерации и ревью
    request = OrchestratorRequest(
        task_description="Create a data processing pipeline",
        model_name="starcoder",
        reviewer_model_name="mistral"
    )
    
    result = await orchestrator.process_task(request)
    print(f"Generated code: {result.generated_code}")
    print(f"Review score: {result.review_score}")

if __name__ == "__main__":
    asyncio.run(main())
```

### HTTP API

#### Генератор агента (порт 9001)

```bash
# Генерация кода
curl -X POST http://localhost:9001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a function to calculate fibonacci numbers",
    "model_name": "starcoder"
  }'

# Улучшение кода
curl -X POST http://localhost:9001/refine \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)",
    "improvement_suggestion": "Add memoization for better performance"
  }'

# Валидация кода
curl -X POST http://localhost:9001/validate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
  }'
```

#### Ревьюер агента (порт 9002)

```bash
# Полный ревью кода
curl -X POST http://localhost:9002/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
    "tests": "def test_fibonacci(): assert fibonacci(5) == 5"
  }'

# Анализ PEP8
curl -X POST http://localhost:9002/analyze-pep8 \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n):return n if n<=1 else fibonacci(n-1)+fibonacci(n-2)"
  }'

# Анализ покрытия тестами
curl -X POST http://localhost:9002/analyze-test-coverage \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
    "tests": "def test_fibonacci(): assert fibonacci(5) == 5"
  }'

# Расчет сложности
curl -X POST http://localhost:9002/calculate-complexity \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
  }'
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
make test

# С покрытием
make test-coverage

# Только unit тесты
make test-unit

# Только integration тесты
make test-integration

# Тесты производительности
make test-performance
```

### Структура тестов

```
tests/
├── test_generator.py      # Тесты агента генератора
├── test_reviewer.py       # Тесты агента ревьюера
├── test_orchestrator.py   # Тесты оркестратора
├── test_communication.py # Тесты коммуникации
└── integration/           # Integration тесты
    ├── test_workflow.py   # Тесты полного workflow
    └── test_api.py        # Тесты API endpoints
```

## 📊 Мониторинг и метрики

### Health Checks

```bash
# Проверка здоровья генератора
curl http://localhost:9001/health

# Проверка здоровья ревьюера
curl http://localhost:9002/health
```

### Статистика

```bash
# Статистика генератора
curl http://localhost:9001/stats

# Статистика ревьюера
curl http://localhost:9002/stats
```

### Логи

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f generator-agent
docker-compose logs -f reviewer-agent
```

## 🔧 Разработка

### Настройка окружения разработки

```bash
# Установка зависимостей
poetry install

# Активация виртуального окружения
poetry shell

# Запуск линтеров
make lint

# Форматирование кода
make format

# Проверка типов
make type-check
```

### Структура проекта

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

## 📚 Документация

Проект включает полный набор документации:

- **README.md** - Основная документация и быстрый старт
- **DEVELOPER_GUIDE.md** - Руководство для разработчиков
- **ARCHITECTURE.md** - Детальная архитектура системы
- **DEPLOYMENT.md** - Руководство по развертыванию
- **TROUBLESHOOTING.md** - Руководство по устранению неполадок
- **API.md** - Документация API endpoints

## 🚀 Производительность

### Типичное время генерации

- **StarCoder**: 5-10 секунд
- **Mistral**: 6-12 секунд
- **Qwen**: 3-8 секунд
- **TinyLlama**: 2-5 секунд

### Требования к ресурсам

- **CPU**: 4+ cores (рекомендуется)
- **RAM**: 16GB+ (32GB для StarCoder)
- **GPU**: NVIDIA с 12GB+ VRAM (для StarCoder)
- **Disk**: 20GB+ (для моделей)

### Масштабирование

```bash
# Горизонтальное масштабирование
docker-compose up -d --scale generator-agent=3 --scale reviewer-agent=2
```

## 🔒 Безопасность

### Особенности безопасности

- Multi-stage Docker builds для минимального размера
- Non-root пользователи в контейнерах
- Health checks для мониторинга
- Resource limits для всех сервисов
- Traefik для защищенного routing

### Рекомендации

- Регулярно обновляйте базовые образы
- Используйте секреты для чувствительных данных
- Мониторьте логи на подозрительную активность
- Реализуйте rate limiting для production

## 🤝 Вклад в проект

Мы приветствуем вклад в проект! Пожалуйста, ознакомьтесь с руководящими принципами:

1. Форкните репозиторий
2. Создайте ветку функции
3. Внесите изменения
4. Добавьте тесты
5. Отправьте pull request

### Стандарты кода

- Следуйте PEP 8 для Python кода
- Используйте type hints
- Пишите комплексные тесты
- Документируйте изменения
- Следуйте существующим паттернам

## 📄 Лицензия

Этот проект лицензирован под лицензией MIT - см. файл LICENSE для деталей.

## 🙏 Благодарности

- HuggingFace за хостинг моделей и библиотеку transformers
- OpenAI за вдохновение API
- Сообщество open-source за инструменты и библиотеки
- Участники и пользователи этого проекта

---

**Примечание**: Это обучающий проект для изучения AI и мульти-агентных систем. Используйте ответственно и в соответствии с применимыми условиями обслуживания.
