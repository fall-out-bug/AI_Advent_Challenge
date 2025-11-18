# Quick Start: Live Testing Epic 25

**Epic**: EP25 - Personalised Butler
**Status**: ✅ Deployed, Ready for Testing

---

## Quick Verification (5 minutes)

### 1. Check Bot is Running
```bash
# Check status (project standard)
make butler-ps

# Check logs (project standard)
make butler-logs-bot | tail -20
```

### 2. Send First Test Message
```
Open Telegram → Butler Bot
Send: "Привет!"
```

**Expected**:
- Reply in Alfred-style дворецкий persona
- Profile auto-created in MongoDB

**Verify**:
```bash
mongosh mongodb://admin:${MONGO_PASSWORD}@localhost:27017/butler?authSource=admin
> db.user_profiles.findOne({"user_id": "YOUR_TELEGRAM_USER_ID"})
# Should show: persona: "Alfred-style дворецкий"
```

### 3. Test Memory Persistence
```
Send: "Расскажи про Python"
Wait for reply
Send: "А какие библиотеки?"
```

**Expected**: Bot remembers previous context about Python

**Verify**:
```bash
> db.user_memory.find({"user_id": "YOUR_USER_ID"}).sort({"created_at": 1})
# Should show: user + assistant message pairs
```

### 4. Check Metrics
```bash
curl http://localhost:8080/metrics | grep personalized
```

**Expected**:
- `personalized_requests_total{source="text",status="success"}`
- `user_profile_reads_total`
- `user_memory_events_total{role="user"}`

---

## Common Test Scenarios

### Scenario 1: New User First Message
```
User: "Привет, кто ты?"
Expected: Alfred-style reply introducing himself
Check: Profile created with default persona
```

### Scenario 2: Context Memory
```
User: "Меня зовут Иван"
Bot: [Reply acknowledging name]
User: "Как меня зовут?"
Expected: Bot remembers name "Иван"
```

### Scenario 3: Voice Message
```
User: [Sends voice message]
Expected:
  1. Transcription shown
  2. Personalized reply in Alfred style
Check: Memory saved with source="voice"
```

### Scenario 4: Memory Compression (Advanced)
```
Send 51+ messages to same user
Expected: Compression triggered, old events deleted
Check: memory_summary field populated in profile
```

---

## Troubleshooting

### Bot Not Responding with Persona
```bash
# Check feature flag (default is True)
poetry run python -c "from src.infrastructure.config.settings import get_settings; print(get_settings().personalization_enabled)"

# Check logs (project standard)
make butler-logs-bot | grep -i personalization
```

### No Profile Created
```bash
# Check MongoDB connection
mongosh mongodb://admin:${MONGO_PASSWORD}@localhost:27017/butler?authSource=admin
> db.user_profiles.find().limit(1)

# Check logs for errors
docker-compose logs butler-bot | grep -i error
```

### Memory Not Persisting
```bash
# Check memory collection
> db.user_memory.find().limit(5)

# Check compression threshold
> db.user_memory.countDocuments({"user_id": "YOUR_USER_ID"})
# Should be ≤50 (compression triggers at 50+)
```

---

## Monitoring Dashboard

### Key Metrics to Watch
1. **Request Success Rate**: `personalized_requests_total{status="success"}` / total
2. **Error Rate**: `personalized_requests_total{status="error"}` / total
3. **Memory Growth**: `user_memory_events_total`
4. **Compression Frequency**: `user_memory_compressions_total{status="success"}`

### Prometheus Queries
```promql
# Error rate
rate(personalized_requests_total{status="error"}[5m]) / rate(personalized_requests_total[5m])

# Memory events per user
sum by (user_id) (user_memory_events_total)

# Compression duration (P95)
histogram_quantile(0.95, rate(user_memory_compression_duration_seconds_bucket[5m]))
```

---

## Quick Rollback (if needed)

```bash
# Disable personalization
export PERSONALIZATION_ENABLED=false
docker-compose restart butler-bot

# Or revert code
git checkout <previous-commit>
docker-compose up -d --build butler-bot
```

---

## Success Indicators

✅ Bot responds with Alfred-style persona
✅ User profiles auto-created
✅ Memory persists across messages
✅ Voice messages work
✅ Metrics visible in Prometheus
✅ No errors in logs
✅ Response time <2s

---

**Ready for**: Live Testing
**Support**: See `DEPLOYMENT_CHECKLIST.md` for detailed instructions
