# Day 12 - Быстрый запуск и тестирование

## Быстрый старт

### 1. Установка зависимостей

```bash
poetry install
# или
pip install prometheus-client pytest pytest-asyncio httpx
```

### 2. Настройка окружения

Создайте `.env` файл с необходимыми переменными (см. `docs/day12/DEPLOYMENT.md`)

### 3. Запуск тестов

```bash
# Все тесты
python scripts/day12_run.py test --type all

# Только unit тесты
python scripts/day12_run.py test --type unit

# Только integration тесты
python scripts/day12_run.py test --type integration

# Только тесты метрик
python scripts/day12_run.py test --type metrics
```

### 4. Запуск сервисов

```bash
# Запуск всех сервисов
python scripts/day12_run.py start

# Проверка статуса
python scripts/day12_run.py check

# Просмотр метрик
python scripts/day12_run.py metrics

# Просмотр логов
python scripts/day12_run.py logs
```

### 5. Остановка сервисов

```bash
python scripts/day12_run.py stop
```

## Проверка работоспособности

### Проверка метрик Prometheus

```bash
# Проверка endpoint
curl http://localhost:8004/metrics

# Проверка конкретных метрик
curl http://localhost:8004/metrics | grep post_fetcher
curl http://localhost:8004/metrics | grep pdf_generation
curl http://localhost:8004/metrics | grep bot_digest
```

### Проверка health endpoints

```bash
# MCP Server
curl http://localhost:8004/health

# Список инструментов
curl http://localhost:8004/tools
```

### Проверка логов

```bash
# Все сервисы
python scripts/day12_run.py logs

# Конкретный сервис
python scripts/day12_run.py logs post-fetcher-worker
python scripts/day12_run.py logs mcp-server
python scripts/day12_run.py logs telegram-bot
```

## Тестирование функциональности

### Тест Post Fetcher Worker

1. Убедитесь, что MongoDB запущен
2. Проверьте логи worker:
   ```bash
   python scripts/day12_run.py logs post-fetcher-worker
   ```
3. Проверьте метрики:
   ```bash
   curl http://localhost:8004/metrics | grep post_fetcher
   ```

### Тест PDF генерации

1. Запустите бота
2. Отправьте команду `/menu` боту
3. Нажмите кнопку "Digest"
4. Проверьте получение PDF файла
5. Проверьте метрики:
   ```bash
   curl http://localhost:8004/metrics | grep pdf_generation
   ```

## Устранение неполадок

### Тесты не запускаются

```bash
# Проверьте зависимости
pip list | grep prometheus-client
pip list | grep pytest

# Переустановите зависимости
poetry install
```

### Сервисы не запускаются

```bash
# Проверьте Docker
docker ps
docker-compose --version

# Пересоберите образы
docker-compose -f docker-compose.day12.yml build --no-cache
docker-compose -f docker-compose.day12.yml up -d
```

### Метрики недоступны

```bash
# Проверьте prometheus-client
python -c "from prometheus_client import Counter; print('OK')"

# Проверьте логи MCP сервера
python scripts/day12_run.py logs mcp-server
```

## Чеклист перед запуском

- [ ] Установлены все зависимости
- [ ] Настроен `.env` файл
- [ ] Все тесты проходят успешно
- [ ] Docker и Docker Compose установлены
- [ ] MongoDB доступен (или запускается через Docker)
- [ ] Telegram бот токен настроен
- [ ] Telegram API credentials настроены

## Дополнительная информация

Полная документация:
- Тестирование: `docs/day12/TESTING_AND_LAUNCH.md`
- Развертывание: `docs/day12/DEPLOYMENT.md`
- API документация: `docs/day12/api.md`
- Архитектура: `docs/day12/ARCHITECTURE.md`

