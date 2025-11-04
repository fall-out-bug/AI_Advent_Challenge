# Homework Review System - Quick Start

## 🚀 Быстрый старт

### 1. Запустить модель Mistral

```bash
# Вариант 1: Использовать готовый скрипт
./scripts/start_models.sh

# Вариант 2: Вручную
cd local_models
docker-compose up -d mistral-chat
```

### 2. Дождаться загрузки модели

```bash
# Проверить статус
./scripts/check_model_status.sh

# Или подождать автоматически
./scripts/wait_for_model.sh
```

**Примечание**: Первая загрузка может занять 5-10 минут. Последующие запуски - ~30 секунд.

### 3. Протестировать на реальном архиве

```bash
# Тест на HW1
python scripts/test_homework_review.py \
  "/home/fall_out_bug/ai_masters/ml_sysdes/aim_sub_MLSYS_F25/HW1/Гаврись_Александр_mlsd_hw1.zip" \
  --model mistral

# Тест на HW2
python scripts/test_homework_review.py \
  "/home/fall_out_bug/ai_masters/ml_sysdes/aim_sub_MLSYS_F25/HW2/Гаврись_Александр_hw2_Гаврись_Александр.zip" \
  --model mistral

# Тест на HW3
python scripts/test_homework_review.py \
  "/home/fall_out_bug/ai_masters/ml_sysdes/aim_sub_MLSYS_F25/HW3/Гаврись_Александр_hw3_Гаврись_Александр.zip" \
  --model mistral
```

### 4. Использовать через MCP

Tool автоматически доступен в MCP server:

```python
from src.presentation.mcp.tools.homework_review_tool import review_homework_archive

result = await review_homework_archive(
    archive_path="/path/to/archive.zip",
    assignment_type="auto",  # или "HW1", "HW2", "HW3"
    token_budget=8000,
    model_name="mistral"
)

print(result["markdown_report"])
```

## 📊 Что делает система

1. **Pass 1 (Architecture)**: Обнаруживает компоненты (Docker, Airflow, Spark, MLflow)
2. **Pass 2 (Components)**: Детальный анализ каждого компонента
3. **Pass 3 (Synthesis)**: Синтез всех findings и финальные рекомендации

## 📁 Структура результатов

После выполнения создается:
- `<archive_name>_review.md` - Полный отчет в Markdown
- Session сохраняется в `/tmp/sessions/<session_id>/`

## 🔧 Требования

- Docker и Docker Compose
- ~15GB свободного места (для модели)
- ~14GB RAM (для Mistral-7B)
- NVIDIA GPU (рекомендуется, но не обязательно)

## 📚 Документация

- `docs/MCP_TOOL_USAGE.md` - Использование через MCP
- `docs/MODEL_SETUP.md` - Настройка моделей
- `docs/PHASE_1_IMPLEMENTATION.md` - Архитектура системы
- `docs/TESTING_FIXTURES_GUIDE.md` - Тестовые фикстуры

## 🐛 Troubleshooting

### Модель не запускается

```bash
# Проверить логи
docker logs local_models-mistral-chat-1

# Перезапустить
cd local_models
docker-compose restart mistral-chat
```

### Health endpoint не отвечает

Модель может еще загружаться. Проверьте логи:
```bash
docker logs -f local_models-mistral-chat-1
```

Ожидайте сообщения "Model loaded" или "Server started".

### Порт 8001 занят

Измените порт в `local_models/docker-compose.yml`:
```yaml
ports:
  - "8002:8000"  # Изменить 8001 на 8002
```

И обновите конфигурацию в `shared/shared_package/config/models.py`.

