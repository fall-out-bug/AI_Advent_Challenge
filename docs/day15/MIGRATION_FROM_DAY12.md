# Миграция с Day 12 на Day 15 (Butler)

## Обзор изменений

День 15 добавляет автоматическую оценку качества и файнтюнинг без breaking changes в существующем API.

## Изменения в Docker Compose

### Старое (day12):
```bash
docker-compose -f docker-compose.day12.yml up -d
```

### Новое (butler):
```bash
docker-compose -f docker-compose.butler.yml up -d
# или
make butler-up
```

### Обратная совместимость

Makefile поддерживает legacy команды:
```bash
make day-12-up    # Алиас для make butler-up
make day-12-down  # Алиас для make butler-down
```

## Новые зависимости

Добавлены опциональные зависимости для файнтюнинга:
```toml
[tool.poetry.extras]
finetuning = ["transformers", "datasets", "torch"]
```

В `Dockerfile.mcp` теперь устанавливаются с флагом `--extras "finetuning"`.

## Новые переменные окружения

Добавьте в `.env`:

```bash
# Evaluation (optional, default: true)
ENABLE_QUALITY_EVALUATION=true
EVALUATION_MIN_SCORE_FOR_DATASET=0.7

# Fine-tuning (optional, default: true)
ENABLE_AUTO_FINETUNING=true
FINETUNING_MIN_SAMPLES=100
FINETUNING_BASE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
FINETUNING_NUM_EPOCHS=3
FINETUNING_BATCH_SIZE=4
FINETUNING_LEARNING_RATE=2e-5
FINETUNING_MODEL_OUTPUT_DIR=/models/fine_tuned
```

**Если не хотите использовать новые возможности:**
```bash
ENABLE_QUALITY_EVALUATION=false
ENABLE_AUTO_FINETUNING=false
```

## Новые volumes

```yaml
volumes:
  - ./models/fine_tuned:/models/fine_tuned:rw  # NEW
  - ./data:/app/data:rw                        # NEW
```

Создайте директории:
```bash
mkdir -p models/fine_tuned
mkdir -p data
```

## Новая MongoDB коллекция

Автоматически создается коллекция `summarization_evaluations`:
```javascript
{
  summary_id: String,
  original_text: String,
  summary_text: String,
  coverage_score: Number,
  accuracy_score: Number,
  coherence_score: Number,
  informativeness_score: Number,
  overall_score: Number,
  // ... метаданные
}
```

## Изменения в коде

### Без изменений (100% совместимо):

- Все существующие use cases (`GenerateChannelDigest`, etc.)
- Все MCP tools
- Telegram bot handlers
- Workers (post fetcher, summary worker)

### Новое поведение:

Если `ENABLE_QUALITY_EVALUATION=true`, после каждой суммаризации:
1. Запускается асинхронная оценка качества
2. Результат сохраняется в MongoDB
3. **Основной поток не блокируется**

## Пошаговая миграция

### Шаг 1: Остановить старые контейнеры

```bash
# Остановка day-12
docker-compose -f docker-compose.day12.yml down

# ИЛИ через make
make day-12-down
```

### Шаг 2: Обновить код

```bash
git pull origin main
```

### Шаг 3: Обновить зависимости

```bash
poetry lock
```

### Шаг 4: Обновить .env

Добавьте новые переменные (см. выше).

### Шаг 5: Создать директории

```bash
mkdir -p models/fine_tuned
mkdir -p data
```

### Шаг 6: Пересобрать образы

```bash
make butler-build
# или
docker-compose -f docker-compose.butler.yml build
```

**Важно:** Сборка займет больше времени из-за установки Transformers.

### Шаг 7: Запустить новую версию

```bash
make butler-up
# или
docker-compose -f docker-compose.butler.yml up -d
```

### Шаг 8: Проверить работу

```bash
# Проверка статуса
make butler-ps

# Проверка логов
make butler-logs | grep -i evaluation

# Проверка health
curl http://localhost:8004/health
```

## Проверка миграции

### 1. Проверка оценки качества

Запросите дайджест через Telegram или MCP tool:
```bash
# Через MCP
python -m mcp client http://localhost:8004

# Через Telegram
/digest @channel_name 24h
```

Проверьте логи:
```bash
docker-compose -f docker-compose.butler.yml logs mcp-server | grep "evaluation complete"
```

### 2. Проверка MongoDB

```bash
docker-compose -f docker-compose.butler.yml exec mongodb mongosh

use butler_db
db.summarization_evaluations.countDocuments()
db.summarization_evaluations.findOne()
```

### 3. Проверка volumes

```bash
ls -la models/fine_tuned/
ls -la data/
```

## Rollback (откат назад)

Если что-то пошло не так:

### Шаг 1: Остановить butler
```bash
make butler-down
```

### Шаг 2: Запустить day-12
```bash
docker-compose -f docker-compose.day12.yml up -d
```

### Шаг 3: Отключить новые фичи

В `.env`:
```bash
ENABLE_QUALITY_EVALUATION=false
ENABLE_AUTO_FINETUNING=false
```

## Известные проблемы и решения

### Проблема: Сборка падает с ошибкой poetry

**Решение:**
```bash
poetry lock
docker-compose -f docker-compose.butler.yml build --no-cache
```

### Проблема: Недостаточно памяти для файнтюнинга

**Решение:** Отключите автоматический файнтюнинг:
```bash
ENABLE_AUTO_FINETUNING=false
```

### Проблема: Transformers не установлен

**Решение:** Проверьте Dockerfile.mcp, должна быть строка:
```dockerfile
RUN poetry install --without dev --no-root --extras "finetuning"
```

### Проблема: Оценка качества замедляет систему

**Решение:** Это не должно происходить (асинхронная оценка). Проверьте:
```bash
docker-compose -f docker-compose.butler.yml logs mcp-server | grep "Fire-and-forget"
```

Если проблема сохраняется, отключите:
```bash
ENABLE_QUALITY_EVALUATION=false
```

## Отличия в производительности

- **Нагрузка на LLM**: +1 запрос на каждую суммаризацию (для оценки)
- **MongoDB**: +1 документ на каждую суммаризацию
- **Disk**: Дообученные модели занимают ~7GB каждая
- **RAM**: Файнтюнинг требует 8GB+ (можно отключить)

## Преимущества миграции

✅ Автоматическая оценка качества  
✅ Накопление датасета для обучения  
✅ Автоматический файнтюнинг (опционально)  
✅ Улучшение модели со временем  
✅ Обратная совместимость (100%)  
✅ Можно отключить все новые фичи  

## Дальнейшие шаги

1. Запустите систему и накопите ~100 оценок
2. Проверьте качество оценок в MongoDB
3. Экспортируйте датасет и проверьте его вручную
4. Запустите файнтюнинг (вручную или автоматически)
5. Оцените улучшение качества суммаризации

## Поддержка

Если возникли проблемы:
1. Проверьте логи: `make butler-logs`
2. Проверьте health: `curl http://localhost:8004/health`
3. Откатитесь на day-12 при необходимости
4. Отключите новые фичи через `.env`

