# 🚀 Быстрый старт системы оценки качества и файнтюна

## 1. Проверка переменных окружения

Убедитесь, что в `.env` есть:
```bash
ENABLE_QUALITY_EVALUATION=true
ENABLE_AUTO_FINETUNING=true
FINETUNING_MIN_SAMPLES=100
```

## 2. Сборка образов

```bash
make butler-build
# или
docker-compose -f docker-compose.butler.yml build
```

⚠️ **Внимание**: Сборка может занять 10-20 минут из-за установки `transformers`, `datasets`, `torch` (~3-4GB).

## 3. Запуск всех сервисов

```bash
make butler-up
# или
docker-compose -f docker-compose.butler.yml up -d
```

## 4. Проверка статуса

```bash
make butler-ps
# или
docker-compose -f docker-compose.butler.yml ps
```

Все сервисы должны быть в статусе `healthy` или `running`.

## 5. Просмотр логов

```bash
# Все логи
make butler-logs

# Только MCP Server (оценка качества)
make butler-logs-mcp

# Только Worker (посты и суммаризация)
make butler-logs-post-fetcher
```

## Что происходит после запуска:

1. ✅ **Автоматическая оценка**: После каждой суммаризации качество оценивается через LLM
2. ✅ **Сохранение в MongoDB**: Все оценки сохраняются в коллекцию `summarization_evaluations`
3. ✅ **Автоматический файнтюнинг**: При накоплении 100+ образцов запускается дообучение модели
4. ✅ **Сохранение моделей**: Дообученные модели сохраняются в `./models/fine_tuned/`

## Проверка работы:

```bash
# Проверить что оценки сохраняются
docker-compose -f docker-compose.butler.yml exec mongodb mongosh butler --eval "db.summarization_evaluations.countDocuments()"

# Проверить количество образцов для файнтюна
docker-compose -f docker-compose.butler.yml exec mongodb mongosh butler --eval "db.summarization_evaluations.countDocuments({overall_score: {\$gte: 0.7}})"
```

## Экспорт датасета вручную:

```bash
docker-compose -f docker-compose.butler.yml exec mcp-server \
  python scripts/export_fine_tuning_dataset.py \
  --min-score 0.8 --limit 500
```

## Остановка:

```bash
make butler-down
# или
docker-compose -f docker-compose.butler.yml down
```
