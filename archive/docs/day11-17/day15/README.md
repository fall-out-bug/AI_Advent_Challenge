# День 15: Система автоматической оценки качества и файнтюнинга

## Обзор

День 15 фокусируется на создании **self-improving системы** суммаризации с автоматической оценкой качества и файнтюнингом локальной LLM модели на собственных данных.

## Ключевые достижения

### 1. Автоматическая оценка качества (LLM-as-Judge)

Реализована система оценки качества суммаризации на базе того же Mistral, который выполняет суммаризацию:

**Метрики оценки:**
- **Coverage** (Полнота) - все ли ключевые темы покрыты
- **Accuracy** (Точность) - отсутствие галлюцинаций и искажений
- **Coherence** (Связность) - читабельность и логичность текста
- **Informativeness** (Информативность) - плотность полезной информации
- **Overall** (Общая оценка) - итоговая оценка качества

Каждая метрика оценивается по шкале от 0.0 до 1.0.

### 2. Асинхронная архитектура

Оценка качества выполняется **fire-and-forget** после генерации суммаризации:
- Не блокирует основной поток
- Не замедляет работу пользователя
- Накапливает данные для обучения в фоне

### 3. Автоматический файнтюнинг

При накоплении достаточного количества качественных образцов (по умолчанию 100+ с оценкой ≥ 0.7):
- Автоматически создается датасет в формате JSONL
- Запускается full fine-tuning модели через Hugging Face Transformers
- Дообученная модель сохраняется в Docker volume

### 4. Расширяемая архитектура файнтюнинга

Спроектирована для поддержки разных типов задач:
- `FineTuningTask` - конфигурация для любого типа задачи
- Поддержка различных методов обучения (full fine-tuning, LoRA, QLoRA)
- Готовность к дообучению не только для суммаризации, но и для классификации, Q&A и других задач

## Архитектура

### Domain Layer

**Value Objects:**
```
src/domain/value_objects/
├── summarization_evaluation.py    # Оценка качества суммаризации
└── finetuning/
    ├── finetuning_task.py         # Конфигурация задачи файнтюнинга
    └── finetuning_result.py       # Результаты файнтюнинга
```

### Infrastructure Layer

**Evaluation & Fine-tuning:**
```
src/infrastructure/
├── llm/
│   ├── evaluation/
│   │   └── summarization_evaluator.py   # Сервис оценки через LLM
│   └── prompts/
│       └── evaluation_prompts.py        # Промпты для оценки
├── finetuning/
│   └── finetuning_service.py           # Сервис файнтюнинга
└── repositories/
    └── summarization_evaluation_repository.py  # Хранение оценок
```

### Workers

```
src/workers/
└── finetuning_worker.py   # Фоновый воркер для автоматического файнтюна
```

## Использование

### Запуск системы

```bash
# Сборка образов (с зависимостями для файнтюнинга)
make butler-build

# Запуск всех сервисов
make butler-up

# Проверка статуса
make butler-ps

# Логи оценки качества
make butler-logs | grep -i evaluation
```

### Конфигурация

Добавьте в `.env`:

```bash
# Автоматическая оценка качества
ENABLE_QUALITY_EVALUATION=true
EVALUATION_MIN_SCORE_FOR_DATASET=0.7

# Автоматический файнтюнинг
ENABLE_AUTO_FINETUNING=true
FINETUNING_MIN_SAMPLES=100
FINETUNING_BASE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
FINETUNING_NUM_EPOCHS=3
FINETUNING_BATCH_SIZE=4
FINETUNING_LEARNING_RATE=2e-5
FINETUNING_MODEL_OUTPUT_DIR=/models/fine_tuned
```

### Ручной экспорт датасета

```bash
# Экспорт высококачественных образцов
docker-compose -f docker-compose.butler.yml exec mcp-server \
  python scripts/export_fine_tuning_dataset.py \
  --min-score 0.8 \
  --limit 500 \
  --output /app/data/fine_tuning_dataset.jsonl
```

### Мониторинг оценок

```bash
# Подключение к MongoDB
docker-compose -f docker-compose.butler.yml exec mongodb mongosh

# Просмотр оценок
use butler_db
db.summarization_evaluations.find().sort({evaluated_at: -1}).limit(10)

# Статистика по оценкам
db.summarization_evaluations.aggregate([
  {$group: {
    _id: null,
    avgOverall: {$avg: "$overall_score"},
    avgCoverage: {$avg: "$coverage_score"},
    avgAccuracy: {$avg: "$accuracy_score"},
    count: {$sum: 1}
  }}
])
```

## Технические детали

### LLM-as-Judge Pattern

Система использует паттерн "LLM как судья":
1. Тот же Mistral, который генерирует суммаризацию, оценивает её качество
2. Промпт содержит четкие критерии оценки (0.0-1.0 для каждой метрики)
3. Ответ парсится как JSON с оценками и объяснением

### Управление токенами

При оценке длинных текстов:
- Оригинальный текст обрезается до максимального размера контекста
- Суммаризация всегда помещается целиком
- Используется `SemanticChunker` для контроля токенов

### Docker volumes

```yaml
volumes:
  - ./models/fine_tuned:/models/fine_tuned:rw  # Дообученные модели
  - ./data:/app/data:rw                        # Датасеты
```

### Poetry extras

Зависимости для файнтюнинга опциональны:

```toml
[tool.poetry.extras]
finetuning = ["transformers", "datasets", "torch"]
```

Установка в Dockerfile:
```dockerfile
RUN poetry install --without dev --no-root --extras "finetuning"
```

## Паттерны и практики

### Clean Architecture

- **Domain** содержит value objects без внешних зависимостей
- **Infrastructure** использует Hugging Face Transformers
- **Application** остается независимой от ML-библиотек

### Асинхронность

```python
# Fire-and-forget evaluation
asyncio.create_task(
    self._evaluate_summary_quality(
        original_text=text,
        summary_result=result,
        context=context,
    )
)
```

### Resilient LLM Client

- Retry logic с exponential backoff
- Fallback механизмы
- Prometheus метрики для мониторинга

## Расширение системы

### Добавление новых типов файнтюнинга

1. Создайте новый value object для задачи
2. Реализуйте специфичный evaluator
3. Настройте `FineTuningTask` с `task_type="your_task"`
4. Используйте общий `FineTuningService`

### Пример: добавление классификации

```python
task = FineTuningTask(
    task_type="classification",
    model_name="mistralai/Mistral-7B-Instruct-v0.2",
    dataset_path="data/classification_dataset.jsonl",
    output_dir="/models/fine_tuned/classification",
    task_specific_config={
        "num_classes": 5,
        "loss_function": "cross_entropy"
    }
)
```

## Известные ограничения

1. **Память**: Файнтюнинг требует значительных ресурсов (рекомендуется 8GB+ RAM)
2. **Скорость**: Full fine-tuning медленный на CPU (рекомендуется GPU)
3. **Хранилище**: Дообученные модели занимают ~7GB каждая

## Метрики и мониторинг

### Prometheus метрики

- `llm_requests_total` - количество запросов к LLM
- `llm_request_duration_seconds` - длительность запросов
- `evaluation_count` - количество выполненных оценок
- `finetuning_runs_total` - количество запусков файнтюнинга

### Логирование

Структурированные логи включают:
- Оценки качества с метриками
- Старт/завершение файнтюнинга
- Ошибки при оценке (не ломают основной поток)

## Асинхронная суммаризация с длинными таймаутами

### Обзор

Для больших дайджестов, которые могут занимать несколько минут, реализована асинхронная система обработки с увеличенными таймаутами (600 секунд).

### Архитектура

**Длинные задачи обрабатываются в фоне:**
1. Пользователь запрашивает дайджест → задача ставится в очередь
2. Бот сразу отвечает подтверждением
3. Worker обрабатывает задачу с таймаутом 600 секунд
4. Результат отправляется отдельным сообщением

### Компоненты

**Domain:**
- `LongSummarizationTask` - сущность задачи
- `TaskStatus` - enum: QUEUED, RUNNING, SUCCEEDED, FAILED

**Application:**
- `RequestChannelDigestAsyncUseCase` - создает задачу в очереди
- `ProcessLongSummarizationTaskUseCase` - обрабатывает с длинным таймаутом

**Infrastructure:**
- `LongTasksRepository` - MongoDB репозиторий с идемпотентными операциями
- `TelegramNotifier` - отправка результатов через Telegram
- `create_adaptive_summarizer_with_long_timeout()` - factory с таймаутом 600s

**Worker:**
- `summary_worker` расширен для опроса и обработки длинных задач
- Атомарный `pick_next_queued()` предотвращает двойную обработку

### Настройки

```python
summarizer_timeout_seconds_long: float = 600.0  # Таймаут для длинных задач
long_tasks_poll_interval_seconds: int = 5  # Интервал опроса очереди
long_tasks_max_retries: int = 1  # Максимум повторов
enable_async_long_summarization: bool = True  # Feature flag
```

### Метрики

- `long_tasks_total{status}` - счетчик задач по статусам
- `long_tasks_duration_seconds{status}` - длительность обработки
- `long_tasks_queue_size` - размер очереди

### Использование

**MCP Tool:**
```python
result = await request_channel_digest_async(
    user_id=123,
    chat_id=456,
    channel_username="channel_name",  # или None для всех каналов
    hours=72,
    language="ru",
    max_sentences=8
)
# Возвращает: {"task_id": "...", "ack_message": "..."}
```

**Поток обработки:**
1. Задача создается со статусом QUEUED
2. Worker атомарно меняет статус на RUNNING
3. Генерируется суммаризация с таймаутом 600s
4. Статус меняется на SUCCEEDED или FAILED
5. Результат отправляется пользователю через TelegramNotifier

### Обработка ошибок

- При ошибке задача помечается как FAILED
- Пользователю отправляется сообщение с описанием ошибки и task_id
- Метрики фиксируют успешные и неуспешные задачи

## Следующие шаги

1. **Экспериментируйте с промптами** для оценки качества
2. **Настройте пороги** для автоматического файнтюнинга
3. **Добавьте новые типы задач** для файнтюнинга
4. **Используйте GPU** для ускорения обучения
5. **Интегрируйте A/B тестирование** базовой и дообученной модели

## Ссылки

- [Архитектура суммаризации](../architecture/SUMMARIZATION_CURRENT_STATE.md)
- [Docker Setup](../DOCKER_SETUP.md)
- [API Documentation](api.md)
- [Отчет для блога](../../reports/SUMMARIZATION_QUALITY_SYSTEM.md)

