# 🚀 Быстрый старт системы оценки качества и файнтюна

## 1. Проверка переменных окружения

Убедитесь, что в `.env` есть:
```bash
ENABLE_QUALITY_EVALUATION=true
ENABLE_AUTO_FINETUNING=true
FINETUNING_MIN_SAMPLES=100
HW_CHECKER_MCP_URL=http://mcp-server:8005
HW_CHECKER_MCP_ENABLED=true
EXTERNAL_API_URL=
EXTERNAL_API_KEY=
LOG_ANALYSIS_MIN_SEVERITY=WARNING
LOG_ANALYSIS_MAX_GROUPS=20
LOG_ANALYSIS_TIMEOUT=60
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
2. ✅ **Мультипроходной review-пайплайн**: Pass 1–3 + статический анализ + Pass 4 логов + хайку
3. ✅ **Публикация ревью**: MCP tool `submit_review_result` (fallback → External API)
4. ✅ **Сохранение результатов**: Markdown, статический анализ и лог-диагностика сохраняются в MongoDB
5. ✅ **Автоматический файнтюнинг**: При накоплении 100+ образцов запускается дообучение модели
6. ✅ **Сохранение моделей**: Дообученные модели сохраняются в `./models/fine_tuned/`

## Проверка работы:

```bash
# Проверить что оценки сохраняются
docker-compose -f docker-compose.butler.yml exec mongodb mongosh butler --eval "db.summarization_evaluations.countDocuments()"

# Проверить количество образцов для файнтюна
docker-compose -f docker-compose.butler.yml exec mongodb mongosh butler --eval "db.summarization_evaluations.countDocuments({overall_score: {\$gte: 0.7}})"
```

## Отправка code review

```bash
curl -X POST "http://localhost:8000/api/v1/reviews" \
  -F "student_id=student_123" \
  -F "assignment_id=HW2" \
  -F "new_commit=abc123def456" \
  -F "new_zip=@review_archives/hw2_latest.zip" \
  -F "old_zip=@review_archives/hw2_prev.zip" \
  -F "logs_zip=@review_archives/hw2_logs.zip"

# Проверить статус
curl -X GET "http://localhost:8000/api/v1/reviews/task_abc123"
```

Ответ `result` содержит `static_analysis_results`, `pass_4_logs`, `haiku` и поле `published_via` (`mcp` или `fallback`).

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
