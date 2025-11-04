# Docker Setup для системы оценки качества и файнтюна

## Обзор

Система полностью упакована в Docker контейнеры с поддержкой:
- LLM-сервер (Mistral)
- MongoDB для хранения данных и оценок
- MCP Server с системой оценки качества
- Telegram Bot
- Workers (post fetcher, summary worker)

## Предварительные требования

1. Docker и Docker Compose установлены
2. NVIDIA GPU (опционально, для ускорения LLM)
3. Переменные окружения в `.env` файле

## Переменные окружения

Добавьте в `.env`:

```bash
# Quality Evaluation
ENABLE_QUALITY_EVALUATION=true
EVALUATION_MIN_SCORE_FOR_DATASET=0.7

# Fine-tuning
ENABLE_AUTO_FINETUNING=true
FINETUNING_MIN_SAMPLES=100
FINETUNING_BASE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
FINETUNING_NUM_EPOCHS=3
FINETUNING_BATCH_SIZE=4
FINETUNING_LEARNING_RATE=2e-5
```

## Запуск

### 1. Сборка образов

```bash
make butler-build
# или
docker-compose -f docker-compose.butler.yml build
```

**Важно**: Сборка может занять время из-за установки `transformers`, `datasets` и `torch`.

### 2. Запуск всех сервисов

```bash
make butler-up
# или
docker-compose -f docker-compose.butler.yml up -d
```

### 3. Проверка статуса

```bash
docker-compose -f docker-compose.butler.yml ps
```

### 4. Просмотр логов

```bash
# Все логи
docker-compose -f docker-compose.butler.yml logs -f

# Только MCP Server (где происходит оценка)
docker-compose -f docker-compose.butler.yml logs -f mcp-server

# Только Workers
docker-compose -f docker-compose.butler.yml logs -f post-fetcher-worker
```

## Volumes

Система использует следующие volumes:

- `./models/fine_tuned:/models/fine_tuned` - сохранение дообученных моделей
- `./data:/app/data` - данные для датасетов
- `./sessions:/app/sessions` - сессии Telegram
- `/datam/mongodb:/data/db` - данные MongoDB

## Работа системы

### Автоматическая оценка качества

После каждой суммаризации автоматически запускается оценка качества:
1. Оценка выполняется асинхронно (не блокирует основной поток)
2. Результаты сохраняются в MongoDB коллекцию `summarization_evaluations`
3. Метрики: coverage, accuracy, coherence, informativeness, overall

### Автоматический файнтюнинг

Когда накапливается 100+ качественных образцов (score >= 0.7):
1. Автоматически экспортируется датасет в JSONL
2. Запускается полный файнтюнинг модели
3. Дообученная модель сохраняется в `/models/fine_tuned/summarization`

### Ручной экспорт датасета

```bash
docker-compose -f docker-compose.butler.yml exec mcp-server \
  python scripts/export_fine_tuning_dataset.py \
  --min-score 0.8 --limit 500 \
  --output /app/data/fine_tuning_dataset.jsonl
```

## Мониторинг

- Prometheus: http://localhost:9090
- LLM Server health: http://localhost:8001/health
- MCP Server health: http://localhost:8004/health

## Остановка

```bash
docker-compose -f docker-compose.butler.yml down
```

С данными:
```bash
docker-compose -f docker-compose.butler.yml down -v
```

## Troubleshooting

### Проблемы с памятью при файнтюнинге

Увеличьте лимиты в `docker-compose.butler.yml` для `mcp-server`:

```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Увеличьте при необходимости
```

### Transformers не установлен

Проверьте, что сборка прошла успешно:

```bash
docker-compose -f docker-compose.butler.yml build mcp-server
docker-compose -f docker-compose.butler.yml exec mcp-server \
  python -c "import transformers; print('OK')"
```

### Ошибки при оценке

Проверьте логи MCP Server:

```bash
docker-compose -f docker-compose.butler.yml logs mcp-server | grep -i evaluation
```

## Production рекомендации

1. **Отключите автоматический файнтюнинг** в production, запускайте вручную:
   ```bash
   ENABLE_AUTO_FINETUNING=false
   ```

2. **Используйте GPU** для файнтюна (добавьте `runtime: nvidia` в docker-compose)

3. **Настройте бэкапы** для MongoDB и моделей

4. **Мониторинг ресурсов**: файнтюнинг требует много CPU/RAM
