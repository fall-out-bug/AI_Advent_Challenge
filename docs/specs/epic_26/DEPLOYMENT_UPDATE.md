# Обновление Test Agent контейнера

## Быстрое обновление (если код изменился)

Если вы изменили код и нужно обновить контейнер:

```bash
# 1. Пересобрать образ с новым кодом
docker-compose -f docker-compose.test-agent.yml build

# 2. Перезапустить контейнер с новым образом
docker-compose -f docker-compose.test-agent.yml up -d --force-recreate
```

## Полное обновление (без кэша)

Если нужно гарантированно пересобрать всё с нуля:

```bash
# 1. Пересобрать образ без кэша
docker-compose -f docker-compose.test-agent.yml build --no-cache

# 2. Перезапустить контейнер
docker-compose -f docker-compose.test-agent.yml up -d --force-recreate
```

## Проверка обновления

После обновления проверьте:

```bash
# Проверить статус контейнера
docker ps | grep test-agent

# Проверить версию кода в контейнере
docker exec test-agent head -5 /app/src/application/test_agent/use_cases/generate_tests_use_case.py

# Проверить, что pytest работает
docker exec test-agent pytest --version
```

## Обновление только кода (без пересборки образа)

Если вы используете volume mount для разработки (раскомментированы строки в docker-compose):

```bash
# Просто перезапустить контейнер
docker-compose -f docker-compose.test-agent.yml restart
```

## Очистка старых образов

После обновления можно удалить старые образы:

```bash
# Удалить неиспользуемые образы
docker image prune -f

# Удалить конкретный старый образ (если нужно)
docker rmi ai-challenge-test-agent:latest
```

## Типичные сценарии

### Сценарий 1: Изменили Python код
```bash
docker-compose -f docker-compose.test-agent.yml build
docker-compose -f docker-compose.test-agent.yml up -d --force-recreate
```

### Сценарий 2: Изменили зависимости (pyproject.toml)
```bash
docker-compose -f docker-compose.test-agent.yml build --no-cache
docker-compose -f docker-compose.test-agent.yml up -d --force-recreate
```

### Сценарий 3: Изменили Dockerfile
```bash
docker-compose -f docker-compose.test-agent.yml build --no-cache
docker-compose -f docker-compose.test-agent.yml up -d --force-recreate
```

### Сценарий 4: Только перезапуск (без изменений)
```bash
docker-compose -f docker-compose.test-agent.yml restart
```

## Просмотр логов после обновления

```bash
# Просмотр логов
docker-compose -f docker-compose.test-agent.yml logs -f test-agent

# Последние 50 строк логов
docker logs test-agent --tail 50
```
