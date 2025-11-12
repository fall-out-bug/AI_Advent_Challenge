# API Documentation - День 15

## Evaluation API

### SummarizationEvaluator

Оценка качества суммаризации с использованием LLM.

#### `evaluate()`

```python
async def evaluate(
    self,
    original_text: str,
    summary_text: str,
    context: SummarizationContext,
    summary_metadata: dict[str, Any],
) -> SummarizationEvaluation
```

**Параметры:**
- `original_text` - исходный текст
- `summary_text` - сгенерированная суммаризация
- `context` - контекст суммаризации
- `summary_metadata` - метаданные результата

**Возвращает:** `SummarizationEvaluation` с оценками по всем критериям

**Пример:**
```python
evaluator = SummarizationEvaluator(llm_client, token_counter)

evaluation = await evaluator.evaluate(
    original_text="Длинный текст...",
    summary_text="Краткая суммаризация...",
    context=SummarizationContext(
        source_type="telegram_posts",
        language="ru",
        max_output_length=1500,
    ),
    summary_metadata={"method": "map_reduce", "chunks": 3},
)

print(f"Общая оценка: {evaluation.overall_score:.2f}")
print(f"Полнота: {evaluation.coverage_score:.2f}")
print(f"Точность: {evaluation.accuracy_score:.2f}")
```

## Fine-tuning API

### FineTuningService

Сервис для файнтюнинга моделей.

#### `fine_tune()`

```python
async def fine_tune(
    self,
    task: FineTuningTask,
) -> FineTuningResult
```

**Параметры:**
- `task` - конфигурация задачи файнтюнинга

**Возвращает:** `FineTuningResult` с метриками обучения

**Пример:**
```python
from src.domain.value_objects.finetuning import FineTuningTask
from src.infrastructure.finetuning import FineTuningService

service = FineTuningService()

task = FineTuningTask(
    task_type="summarization",
    model_name="mistralai/Mistral-7B-Instruct-v0.2",
    dataset_path="/app/data/fine_tuning_dataset.jsonl",
    output_dir="/models/fine_tuned/summarization",
    num_epochs=3,
    batch_size=4,
    learning_rate=2e-5,
)

result = await service.fine_tune(task)

print(f"Training loss: {result.training_loss:.4f}")
print(f"Trained on {result.num_samples} samples")
print(f"Duration: {result.training_duration_seconds:.0f}s")
```

## Repository API

### SummarizationEvaluationRepository

Работа с оценками качества в MongoDB.

#### `save_evaluation()`

```python
async def save_evaluation(
    self,
    evaluation: SummarizationEvaluation,
) -> str
```

Сохраняет оценку в базу данных.

**Возвращает:** ID сохраненной оценки

#### `count_by_score()`

```python
async def count_by_score(
    self,
    min_score: float = 0.0,
    max_score: float = 1.0,
) -> int
```

Подсчитывает количество оценок в диапазоне.

#### `export_to_fine_tuning_dataset()`

```python
async def export_to_fine_tuning_dataset(
    self,
    output_path: str,
    min_score: float = 0.7,
    limit: int | None = None,
) -> int
```

Экспортирует высококачественные образцы в JSONL для файнтюнинга.

**Возвращает:** Количество экспортированных образцов

**Пример:**
```python
from src.infrastructure.database.mongo import get_db
from src.infrastructure.repositories import SummarizationEvaluationRepository

db = await get_db()
repo = SummarizationEvaluationRepository(db)

# Подсчет качественных образцов
count = await repo.count_by_score(min_score=0.7)
print(f"High-quality samples: {count}")

# Экспорт датасета
exported = await repo.export_to_fine_tuning_dataset(
    output_path="/app/data/fine_tuning_dataset.jsonl",
    min_score=0.8,
    limit=500,
)
print(f"Exported {exported} samples")
```

#### `should_trigger_finetuning()`

```python
async def should_trigger_finetuning(
    self,
    min_samples: int,
    min_score: float,
) -> bool
```

Проверяет, достаточно ли накоплено образцов для файнтюнинга.

## Value Objects

### SummarizationEvaluation

```python
@dataclass
class SummarizationEvaluation:
    summary_id: str
    original_text: str
    summary_text: str
    coverage_score: float        # 0.0-1.0
    accuracy_score: float        # 0.0-1.0
    coherence_score: float       # 0.0-1.0
    informativeness_score: float # 0.0-1.0
    overall_score: float         # 0.0-1.0
    evaluation_method: str
    evaluator_model: str
    evaluation_prompt: str
    raw_response: str
    summarization_context: dict[str, Any]
    summary_metadata: dict[str, Any]
    evaluated_at: datetime

    def to_fine_tuning_sample(self) -> dict[str, Any]:
        """Преобразует в формат для файнтюнинга."""
```

### FineTuningTask

```python
@dataclass
class FineTuningTask:
    task_type: str              # "summarization" | "classification" | "qa"
    model_name: str
    dataset_path: str
    output_dir: str
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-5
    max_steps: int | None = None
    task_specific_config: dict[str, Any] | None = None
```

### FineTuningResult

```python
@dataclass
class FineTuningResult:
    task_type: str
    model_name: str
    fine_tuned_model_path: str
    training_loss: float
    validation_loss: float | None
    num_samples: int
    num_epochs: int
    training_duration_seconds: float
    started_at: datetime
    completed_at: datetime
    metadata: dict[str, Any] | None = None
```

## Scripts

### export_fine_tuning_dataset.py

Экспорт датасета из MongoDB в JSONL.

```bash
python scripts/export_fine_tuning_dataset.py \
  --min-score 0.8 \
  --limit 500 \
  --output /app/data/fine_tuning_dataset.jsonl
```

**Аргументы:**
- `--min-score` - минимальная оценка (default: 0.7)
- `--limit` - максимальное количество образцов (optional)
- `--output` - путь к выходному файлу (default: /app/data/fine_tuning_dataset.jsonl)

## Async Long Summarization API

### request_channel_digest_async

MCP tool для создания асинхронной задачи на генерацию дайджеста.

```python
@mcp.tool()
async def request_channel_digest_async(
    user_id: int,
    chat_id: int,
    channel_username: str | None = None,
    hours: int = 72,
    language: str = "ru",
    max_sentences: int = 8,
) -> Dict[str, Any]
```

**Параметры:**
- `user_id` - Telegram user ID
- `chat_id` - Telegram chat ID для отправки результатов
- `channel_username` - Имя канала (None = все каналы)
- `hours` - Временное окно в часах (default: 72)
- `language` - Язык суммаризации ("ru" | "en", default: "ru")
- `max_sentences` - Максимум предложений (default: 8)

**Возвращает:**
```python
{
    "task_id": "digest_abc123_1234567890",
    "ack_message": "Принял задачу на создание дайджеста..."
}
```

**Пример:**
```python
result = await request_channel_digest_async(
    user_id=123,
    chat_id=456,
    channel_username="channel_name",
    hours=72,
    language="ru",
    max_sentences=8
)
# Пользователь получает: "Принял задачу на создание дайджеста канала channel_name за 72 часов. Пришлю результат отдельным сообщением."
# Worker обрабатывает задачу с таймаутом 600s
# Результат отправляется отдельным сообщением: "📋 Дайджест канала channel_name:\n\n..."
```

### LongSummarizationTask

Сущность задачи для длинной суммаризации.

```python
@dataclass
class LongSummarizationTask:
    task_id: str
    user_id: int
    chat_id: int
    channel_username: str | None = None
    context: SummarizationContext
    status: TaskStatus  # QUEUED, RUNNING, SUCCEEDED, FAILED
    result_text: str | None = None
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
```

### LongTasksRepository

Репозиторий для работы с длинными задачами.

```python
class LongTasksRepository:
    async def create(task: LongSummarizationTask) -> str
    async def pick_next_queued() -> LongSummarizationTask | None
    async def mark_running(task_id: str) -> None
    async def complete(task_id: str, result_text: str) -> None
    async def fail(task_id: str, error: str) -> None
    async def get_by_id(task_id: str) -> LongSummarizationTask | None
    async def get_by_user(user_id: int, limit: int, status: TaskStatus | None) -> list[LongSummarizationTask]
```

**Особенности:**
- Атомарный `pick_next_queued()` предотвращает двойную обработку
- Идемпотентные операции через MongoDB
- Автоматический TTL 7 дней для старых задач

### Метрики

**Prometheus метрики:**
- `long_tasks_total{status}` - счетчик задач по статусам (queued, running, succeeded, failed)
- `long_tasks_duration_seconds{status}` - длительность обработки задач
- `long_tasks_queue_size` - текущий размер очереди

### Настройки

```python
summarizer_timeout_seconds_long: float = 600.0  # Таймаут для длинных задач
long_tasks_poll_interval_seconds: int = 5  # Интервал опроса очереди worker'ом
long_tasks_max_retries: int = 1  # Максимум повторов
enable_async_long_summarization: bool = True  # Feature flag
```

### Обработка ошибок

При ошибке обработки:
1. Задача помечается как FAILED в MongoDB
2. Пользователю отправляется сообщение с описанием ошибки и task_id
3. Метрики фиксируют неуспешную задачу
4. Логи содержат полный traceback для отладки

## MongoDB Schema

### Collection: `summarization_evaluations`

```javascript
{
  _id: ObjectId,
  summary_id: String,
  original_text: String,
  summary_text: String,
  coverage_score: Number,
  accuracy_score: Number,
  coherence_score: Number,
  informativeness_score: Number,
  overall_score: Number,
  evaluation_method: String,
  evaluator_model: String,
  evaluation_prompt: String,
  raw_response: String,
  summarization_context: Object,
  summary_metadata: Object,
  evaluated_at: ISODate
}
```

**Индексы:**
- `overall_score` (для быстрого поиска качественных образцов)
- `evaluated_at` (для сортировки по времени)
- `summary_id` (для уникальности)

## Environment Variables

```bash
# Evaluation settings
ENABLE_QUALITY_EVALUATION=true
EVALUATION_MIN_SCORE_FOR_DATASET=0.7

# Fine-tuning settings
ENABLE_AUTO_FINETUNING=true
FINETUNING_MIN_SAMPLES=100
FINETUNING_MODEL_OUTPUT_DIR=/models/fine_tuned
FINETUNING_BASE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
FINETUNING_NUM_EPOCHS=3
FINETUNING_BATCH_SIZE=4
FINETUNING_LEARNING_RATE=2e-5
```

## Docker Compose Services

### mcp-server (с поддержкой файнтюнинга)

```yaml
mcp-server:
  volumes:
    - ./models/fine_tuned:/models/fine_tuned:rw
    - ./data:/app/data:rw
  environment:
    - ENABLE_QUALITY_EVALUATION=true
    - ENABLE_AUTO_FINETUNING=true
    - FINETUNING_MIN_SAMPLES=100
  deploy:
    resources:
      limits:
        memory: 8G  # Для файнтюнинга
```

## Примеры использования

### Пример 1: Мониторинг качества

```python
from src.infrastructure.repositories import SummarizationEvaluationRepository

# Получить последние оценки
evaluations = await repo.get_recent_evaluations(limit=10)

for eval in evaluations:
    print(f"Summary: {eval.summary_id}")
    print(f"  Overall: {eval.overall_score:.2f}")
    print(f"  Coverage: {eval.coverage_score:.2f}")
    print(f"  Accuracy: {eval.accuracy_score:.2f}")
```

### Пример 2: Ручной триггер файнтюнинга

```python
from src.workers.finetuning_worker import FineTuningWorker

worker = FineTuningWorker(
    evaluation_repo=repo,
    finetuning_service=service,
    settings=settings,
)

# Проверить и запустить файнтюнинг
await worker.check_and_run_finetuning()
```

### Пример 3: Проверка готовности к файнтюнингу

```python
# Подсчет качественных образцов
count = await repo.count_by_score(min_score=0.7)
min_required = settings.finetuning_min_samples

if count >= min_required:
    print(f"✅ Готово к файнтюнингу: {count}/{min_required}")
else:
    print(f"⏳ Нужно еще образцов: {count}/{min_required}")
```

## Ошибки и обработка

### Evaluation Errors

```python
try:
    evaluation = await evaluator.evaluate(...)
except json.JSONDecodeError:
    logger.error("Failed to parse LLM response as JSON")
except ValueError as e:
    logger.error(f"Invalid evaluation scores: {e}")
```

### Fine-tuning Errors

```python
try:
    result = await service.fine_tune(task)
except ImportError:
    logger.error("Transformers not installed")
except RuntimeError as e:
    logger.error(f"Training failed: {e}")
```

## Best Practices

1. **Асинхронная оценка**: Всегда используйте fire-and-forget для оценки
2. **Мониторинг**: Следите за количеством накопленных образцов
3. **Ресурсы**: Файнтюнинг требует много памяти, планируйте ресурсы
4. **Валидация**: Проверяйте качество дообученной модели перед использованием
5. **Бэкапы**: Сохраняйте исходные модели перед файнтюнингом

