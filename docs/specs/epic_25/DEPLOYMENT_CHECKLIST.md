# Epic 25 Deployment Checklist

**Epic**: EP25 - Personalised Butler  
**Status**: ✅ Ready for Production  
**Date**: 2025-11-18

---

## Pre-Deployment Checks

### Code Quality ✅
- [x] All tests passing (unit + integration + E2E)
- [x] Code coverage ≥80%
- [x] No linting errors
- [x] Type hints 100%
- [x] All docstrings complete

### Review & Approvals ✅
- [x] Code review completed
- [x] All blockers resolved
- [x] Feature flag default set to `True`
- [x] Prometheus alerts configured
- [x] Documentation complete

### Configuration ✅
- [x] `personalization_enabled: True` (default)
- [x] MongoDB indexes created
- [x] Prometheus alerts active
- [x] Metrics instrumentation complete

---

## Deployment Steps

### 1. Database Migration

```bash
# Ensure MongoDB indexes are created
poetry run python -m src.infrastructure.personalization.migrations.create_indexes

# Verify indexes
mongosh mongodb://admin:${MONGO_PASSWORD}@localhost:27017/butler?authSource=admin
> db.user_profiles.getIndexes()
> db.user_memory.getIndexes()
```

**Expected Indexes**:
- `user_profiles`: `user_id` (unique), `created_at`
- `user_memory`: `(user_id, created_at)`, `created_at` (TTL 90 days)

### 2. Configuration Update

Verify environment variables:
```bash
# Check personalization is enabled (default: True)
export PERSONALIZATION_ENABLED=true  # Optional, True is default

# MongoDB connection
export MONGODB_URL="mongodb://admin:${MONGO_PASSWORD}@localhost:27017/butler?authSource=admin"

# LLM client (Qwen-7B)
export LLM_API_URL="http://localhost:8000"  # Or your LLM endpoint
```

### 3. Prometheus Alerts

Verify alerts are loaded:
```bash
# Check Prometheus config
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.component=="personalization")'

# Expected alerts:
# - PersonalizationHighErrorRate
# - MemoryCompressionFailures
```

### 4. Deploy Butler Bot

```bash
# Build and deploy (example with docker-compose)
cd /home/fall_out_bug/studies/AI_Challenge
docker-compose up -d butler-bot

# Or if using systemd/service
systemctl restart butler-bot
```

### 5. Verify Deployment

```bash
# Check bot is running
curl http://localhost:8080/health  # Or your health endpoint

# Check logs
docker-compose logs -f butler-bot | grep -i personalization

# Verify metrics endpoint
curl http://localhost:8080/metrics | grep personalized
```

---

## Post-Deployment Testing

### 1. Basic Functionality Test

**Test Case**: First message from new user
```
User: Привет!
Expected: Reply in Alfred-style дворецкий persona
Check: Profile auto-created in MongoDB
```

**Verification**:
```bash
# Check profile was created
mongosh mongodb://admin:${MONGO_PASSWORD}@localhost:27017/butler?authSource=admin
> db.user_profiles.findOne({"user_id": "YOUR_USER_ID"})
# Should show: persona: "Alfred-style дворецкий", language: "ru"
```

### 2. Memory Persistence Test

**Test Case**: Multiple messages from same user
```
User: Расскажи про Python
Bot: [Reply about Python]

User: А какие библиотеки популярны?
Expected: Bot remembers previous context about Python
Check: Memory events stored in MongoDB
```

**Verification**:
```bash
# Check memory events
> db.user_memory.find({"user_id": "YOUR_USER_ID"}).sort({"created_at": 1})
# Should show: user message + assistant reply pairs
```

### 3. Voice Message Test

**Test Case**: Voice message transcription → personalized reply
```
User: [Sends voice message]
Expected: 
  1. STT transcription shown
  2. Personalized reply in Alfred style
Check: Memory saved with source="voice"
```

### 4. Memory Compression Test

**Test Case**: Send 51+ messages to trigger compression
```
# Send 51 messages
for i in {1..51}; do
  # Send message via Telegram
done

Expected: 
  - Compression triggered at 50+ events
  - Old events deleted, last 20 kept
  - Summary stored in profile
```

**Verification**:
```bash
# Check compression
> db.user_memory.countDocuments({"user_id": "YOUR_USER_ID"})
# Should be ≤22 (20 kept + 2 new)

> db.user_profiles.findOne({"user_id": "YOUR_USER_ID"})
# Should show: memory_summary field populated
```

### 5. Error Handling Test

**Test Case**: LLM failure
```
# Simulate LLM failure or timeout
Expected: Graceful error message, no crash
Check: Error logged, metrics updated
```

**Verification**:
```bash
# Check error metrics
curl http://localhost:8080/metrics | grep personalized_requests_total
# Should show: status="error" counter if errors occurred
```

### 6. Prometheus Alerts Test

**Test Case**: Trigger alert conditions
```
# Simulate high error rate (>10% in 5min)
# Or compression failures (>5 in 5min)

Expected: Alert fires in Prometheus
Check: Alertmanager receives alert
```

**Verification**:
```bash
# Check Prometheus alerts
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.component=="personalization")'

# Check Alertmanager
curl http://localhost:9093/api/v2/alerts | jq '.[] | select(.labels.component=="personalization")'
```

---

## Monitoring Checklist

### Metrics to Monitor

1. **Request Metrics**:
   - `personalized_requests_total{source,status}` - Track success/error rates
   - `personalized_prompt_tokens_total` - Monitor prompt sizes

2. **Profile Metrics**:
   - `user_profile_reads_total` - Profile read frequency
   - `user_profile_writes_total` - Profile creation/updates

3. **Memory Metrics**:
   - `user_memory_events_total{role}` - Memory growth
   - `user_memory_compressions_total{status}` - Compression frequency
   - `user_memory_compression_duration_seconds` - Compression performance

### Alerts to Watch

1. **PersonalizationHighErrorRate**: >10% error rate in 5 minutes
   - **Action**: Check LLM connectivity, MongoDB status
   - **Runbook**: `docs/operational/metrics.md`

2. **MemoryCompressionFailures**: >5 failures in 5 minutes
   - **Action**: Check LLM summarization, MongoDB performance
   - **Runbook**: `docs/operational/metrics.md`

### Logs to Monitor

```bash
# Watch for errors
docker-compose logs -f butler-bot | grep -i "error\|failed\|exception"

# Watch personalization activity
docker-compose logs -f butler-bot | grep -i "personalized\|memory\|profile"

# Watch compression
docker-compose logs -f butler-bot | grep -i "compress"
```

---

## Rollback Plan

If issues occur:

### Quick Disable
```bash
# Set feature flag to False
export PERSONALIZATION_ENABLED=false
# Restart bot
docker-compose restart butler-bot
```

### Full Rollback
```bash
# Revert to previous version
git checkout <previous-commit>
docker-compose up -d --build butler-bot
```

### Data Cleanup (if needed)
```bash
# Remove all personalization data
mongosh mongodb://admin:${MONGO_PASSWORD}@localhost:27017/butler?authSource=admin
> db.user_profiles.deleteMany({})
> db.user_memory.deleteMany({})
```

---

## Success Criteria

- [ ] Bot responds with Alfred-style persona
- [ ] User profiles auto-created on first message
- [ ] Memory persists across messages
- [ ] Voice messages work with personalization
- [ ] Memory compression triggers at 50+ events
- [ ] Prometheus metrics visible
- [ ] Alerts configured and tested
- [ ] No errors in logs
- [ ] Performance acceptable (<2s response time)

---

## Post-Deployment Tasks

1. **Monitor for 24 hours**:
   - Check error rates
   - Monitor memory growth
   - Verify compression works
   - Watch alert frequency

2. **User Feedback**:
   - Collect user feedback on persona
   - Monitor user satisfaction
   - Track usage patterns

3. **Performance Tuning**:
   - Optimize prompt sizes if needed
   - Adjust compression threshold if needed
   - Scale resources if needed

4. **Documentation**:
   - Update runbooks with lessons learned
   - Document any issues encountered
   - Update metrics dashboards

---

## Support Contacts

- **Tech Lead**: For technical issues
- **DevOps**: For infrastructure/deployment issues
- **Documentation**: `docs/specs/epic_25/`

---

**Status**: ✅ Ready for Deployment  
**Last Updated**: 2025-11-18

