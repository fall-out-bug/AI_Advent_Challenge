# Epic 25: Quick Deploy Guide

**Использует стандартные команды проекта**

---

## Быстрый деплой (3 шага)

### 1. Запустить инфраструктуру
```bash
./scripts/infra/start_shared_infra.sh

# Загрузить credentials (стандартный способ проекта)
set -a
source ~/work/infra/.env.infra
set +a
export MONGODB_URL="mongodb://admin:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin"
```

### 2. Создать индексы MongoDB
```bash
poetry run python scripts/migrations/add_personalization_indexes.py
```

### 3. Запустить Butler bot
```bash
make butler-up
```

---

## Проверка

```bash
# Статус сервисов
make butler-ps

# Логи
make butler-logs-bot | grep -i personalization

# Тест в Telegram
# Отправить: "Привет!"
# Ожидать: ответ в стиле Alfred
```

---

## Полезные команды

```bash
# Перезапуск
make butler-restart

# Остановка
make butler-down

# Логи всех сервисов
make butler-logs

# Статус
make butler-ps
```

---

**Готово!** 🚀

Подробности: `DEPLOYMENT_STATUS.md`

