# Epic 25 Deployment Status

**Date**: 2025-11-18
**Status**: ⚠️ **READY FOR DEPLOYMENT** (MongoDB credentials needed)

---

## Pre-Deployment Checks ✅

### Code Quality ✅
- ✅ Feature flag default: `True` (verified)
- ✅ Prometheus alerts: Configured
- ✅ Metrics: Implemented
- ✅ Code: All changes committed

### Configuration ⚠️
- ⚠️ MongoDB connection: **Requires credentials**
- ⚠️ Environment variables: Need to be set

---

## Deployment Steps

### Step 1: Start Shared Infrastructure

```bash
# Start MongoDB, Prometheus, and other shared services
./scripts/infra/start_shared_infra.sh

# Load shared infra credentials (standard project way)
set -a
source ~/work/infra/.env.infra
set +a

# Set MongoDB URL (project standard)
export MONGODB_URL="mongodb://admin:${MONGO_PASSWORD}@127.0.0.1:27017/butler?authSource=admin"
```

### Step 2: Create MongoDB Indexes

```bash
# Run migration script (credentials already loaded from .env.infra)
poetry run python scripts/migrations/add_personalization_indexes.py
```

**Expected Output**:
```
✓ user_profiles.user_id_unique index created
✓ user_memory.user_id_created_at index created
✓ user_memory.created_at_ttl index created (90 days)
All personalization indexes created successfully
```

### Step 3: Verify Indexes

```bash
# Using mongosh (if available)
mongosh "${MONGODB_URL}"
> db.user_profiles.getIndexes()
> db.user_memory.getIndexes()
```

**Expected Indexes**:
- `user_profiles`: `user_id` (unique)
- `user_memory`: `(user_id, created_at)`, `created_at` (TTL 90 days)

### Step 4: Start Butler Bot

```bash
# Use project standard command (recommended)
make butler-up

# Or restart if already running
make butler-restart

# Check status
make butler-ps

# View logs
make butler-logs-bot
```

### Step 5: Verify Deployment

```bash
# Check bot is running
make butler-ps

# Check logs for personalization
make butler-logs-bot | grep -i personalization | tail -20

# Check metrics (if metrics endpoint available)
# curl http://localhost:8080/metrics | grep personalized
```

**Expected Metrics**:
- `personalized_requests_total{source="text",status="success"}`
- `user_profile_reads_total`
- `user_memory_events_total{role="user"}`

---

## Quick Test

### Test 1: First Message

```
Open Telegram → Butler Bot
Send: "Привет!"
```

**Expected**:
- Reply in Alfred-style дворецкий persona
- Profile auto-created

**Verify**:
```bash
# Check profile was created
mongosh "${MONGODB_URL}"
> db.user_profiles.findOne({"user_id": "YOUR_TELEGRAM_USER_ID"})
```

### Test 2: Memory Persistence

```
Send: "Расскажи про Python"
Wait for reply
Send: "А какие библиотеки?"
```

**Expected**: Bot remembers previous context

**Verify**:
```bash
> db.user_memory.find({"user_id": "YOUR_USER_ID"}).sort({"created_at": 1})
```

---

## Troubleshooting

### MongoDB Authentication Error

**Error**: `Command createIndexes requires authentication`

**Solution**:
```bash
# Ensure MONGODB_URL includes credentials
export MONGODB_URL="mongodb://admin:${MONGO_PASSWORD}@localhost:27017/butler?authSource=admin"

# Verify connection
poetry run python -c "from motor.motor_asyncio import AsyncIOMotorClient; from src.infrastructure.config.settings import get_settings; import asyncio; async def test(): s = get_settings(); c = AsyncIOMotorClient(s.mongodb_url); await c.admin.command('ping'); print('✅ Connected'); c.close(); asyncio.run(test())"
```

### Tests Failing

**Error**: `Command find requires authentication`

**Solution**:
```bash
# Set TEST_MONGODB_URL for tests
export TEST_MONGODB_URL="${MONGODB_URL}"

# Run tests
poetry run pytest tests/integration/application/personalization/ -v
```

### Bot Not Responding with Persona

**Check**:
1. Feature flag is enabled (default: `True`)
2. Logs show personalization is active
3. MongoDB connection is working

```bash
# Check logs
docker-compose logs butler-bot | grep -i "personalization\|alfred"

# Check feature flag
poetry run python -c "from src.infrastructure.config.settings import get_settings; print(get_settings().personalization_enabled)"
```

---

## Current Status

✅ **Code**: Ready
✅ **Configuration**: Feature flag default = True
✅ **Alerts**: Configured
✅ **Metrics**: Implemented
⚠️ **MongoDB**: Needs credentials setup
⚠️ **Indexes**: Need to run migration
⏳ **Deployment**: Pending MongoDB setup

---

## Next Actions

1. **Set MongoDB credentials** in environment
2. **Run index migration** script
3. **Start/restart Butler bot**
4. **Test with Telegram** bot
5. **Monitor metrics** and logs

---

**Ready for**: Live deployment after MongoDB setup
**Support**: See `DEPLOYMENT_CHECKLIST.md` for detailed instructions
