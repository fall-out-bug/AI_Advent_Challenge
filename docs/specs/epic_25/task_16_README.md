# Task 16: Interest Extraction & Profile Enrichment

**Epic 25 Enhancement · Auto-learn user interests from conversations**

---

## Quick Overview

### What It Does
Automatically extracts user interests (topics like "Python", "Docker", "Telegram bots") from conversations and uses them to personalize Butler responses.

### Why It Matters
- **Smarter Butler**: Adapts examples and suggestions to user's context
- **No Configuration**: Works automatically, no setup required
- **Privacy-First**: Only stores thematic topics (no API keys, passwords, personal info)

---

## User Experience

**Before Task 16**:
- User: "How do I handle errors?"
- Butler: "Error handling depends on your context, sir. Here are general approaches..."

**After Task 16** (user has interests: ["Python", "Telegram bots"]):
- User: "How do I handle errors?"
- Butler: "For Python Telegram bots, I recommend try/except blocks around bot.send_message() calls, sir. Consider using aiogram's error handlers..."

---

## How It Works

```
User sends 55+ messages about Python & Docker
  ↓
Memory compression triggered (event_count > 50)
  ↓
InterestExtractionService analyzes conversation
  ↓
LLM extracts: {"summary": "...", "interests": ["Python", "Docker"]}
  ↓
Profile updated: preferred_topics = ["Python", "Docker", ...]
  ↓
Future responses include Python/Docker context
```

---

## Implementation Summary

### New Component
**`InterestExtractionService`** (`src/application/personalization/`)
- Builds LLM prompt for interest extraction
- Parses JSON response: `summary` + `interests`
- Filters sensitive data (API keys, passwords, file paths)
- Merges new interests with existing (stable list of 3-7 items)

### Modified Components
1. **`UserProfile`**: Add `with_topics(topics)` method
2. **`PersonalizedReplyUseCase`**: Integrate interest extraction in `_compress_memory()`
3. **Factory**: Wire `InterestExtractionService` via DI

---

## Key Features

### ✅ Automatic Extraction
- Triggers during memory compression (~50 messages)
- No user configuration needed
- Runs in background, doesn't block responses

### ✅ Privacy Protection
- **Filters sensitive data** via regex patterns:
  - API keys: `sk-abcd1234...`
  - Passwords: `password=secret`
  - File paths: `/home/user/data.txt`
  - User IDs: `123456789`
- Only stores thematic topics: "Python", "Docker", "Clean Architecture"

### ✅ Stability
- **Merge logic** preserves existing topics (no churn)
- **Ranking**: Topics in both old/new lists ranked higher
- **Limit**: Maximum 7 topics per user

### ✅ Graceful Fallback
- LLM parse error → keep existing topics, use basic summary
- LLM timeout → compression still succeeds
- Metrics track failures for monitoring

---

## Configuration

### Environment Variables
```bash
INTEREST_EXTRACTION_ENABLED=true        # Default: true
INTEREST_EXTRACTION_MAX_TOPICS=7        # Default: 7 (range: 3-10)
INTEREST_EXTRACTION_LLM_TEMPERATURE=0.3 # Default: 0.3 (lower = more deterministic)
```

### Feature Flag
```python
# Disable interest extraction (emergency)
settings.interest_extraction_enabled = False
```

---

## Metrics

### Prometheus Metrics
- `interest_extraction_total{status}` — Operations (success/parse_error/llm_error)
- `interest_extraction_duration_seconds` — Extraction latency (histogram)
- `user_interests_updated_total` — Profile updates with new interests
- `user_interests_count` — Number of interests per profile (histogram)

### Grafana Dashboard
- Panel: "Interest Extraction Success Rate"
- Panel: "Topics per User Distribution"
- Panel: "Extraction Latency (P50/P95/P99)"

---

## Testing

### Unit Tests (8 tests)
- ✅ Extract topics from Python/Docker conversation
- ✅ Filter sensitive data (API keys rejected)
- ✅ Merge logic (existing + new → stable)
- ✅ JSON parse errors → graceful fallback
- ✅ Max topics constraint (≤7)

### Integration Tests (2 tests)
- ✅ 55 Python messages → compression → topics extracted
- ✅ Existing topics + new topics → proper merge

### E2E Tests (2 tests)
- ✅ Topics reflected in Butler responses
- ✅ No sensitive data in profile after themed conversation

**Coverage**: ≥80% for new service

---

## Rollout Plan

### Phase 1: Development (3 days)
- ✅ Implement `InterestExtractionService`
- ✅ Update `PersonalizedReplyUseCase`
- ✅ Write comprehensive tests
- Feature flag: **DISABLED** (`INTEREST_EXTRACTION_ENABLED=false`)

### Phase 2: Staging (1 week)
- Deploy to staging
- Feature flag: **ENABLED** (`INTEREST_EXTRACTION_ENABLED=true`)
- Monitor metrics (error rates, extraction quality)
- Manual testing: themed conversations

### Phase 3: Production (Gradual)
- Canary: Enable for 10% users
- Monitor: Error rates < 5%, extraction latency < 2s (P95)
- Gradual: 10% → 25% → 50% → 100%
- Fallback: Disable flag if issues detected

---

## Example Topics

### Good Topics (Extracted)
- "Python"
- "Docker"
- "Clean Architecture"
- "Telegram bots"
- "API design"
- "Machine Learning"
- "FastAPI"

### Bad Topics (Filtered)
- ~~"sk-1234567890abcdef"~~ (API key)
- ~~"password=mysecret"~~ (password)
- ~~"/home/user/data.txt"~~ (file path)
- ~~"123456789"~~ (user ID)
- ~~"user@example.com"~~ (email)

---

## Troubleshooting

### Issue: Topics not extracted after 55 messages
**Check**:
- Feature flag enabled: `INTEREST_EXTRACTION_ENABLED=true`
- Memory compression triggered: Check logs for "Memory compressed"
- LLM response valid: Check metrics `interest_extraction_total{status="parse_error"}`

### Issue: Generic topics ("technology", "coding")
**Solution**: Improve prompt engineering (ask for specific technologies/frameworks)

### Issue: Topics change every compression
**Solution**: Verify merge logic prioritizes existing topics

### Issue: Sensitive data in topics
**Solution**: Add more regex patterns to `SENSITIVE_PATTERNS`

---

## Documentation

### For Users
- [Personalized Butler User Guide](../../guides/personalized_butler_user_guide.md) — User-facing docs (Russian)

### For Developers
- [Full Specification](./task_16_interest_extraction_spec.md) — Detailed technical spec (27 pages)
- [Developer Handoff](./task_16_dev_handoff.md) — Implementation guide with code examples

### For Operators
- [Metrics Documentation](../../operational/metrics.md) — Prometheus metrics and alerts

---

## Files

### New Files
```
src/application/personalization/
  └── interest_extraction_service.py          (NEW)

tests/unit/application/personalization/
  └── test_interest_extraction_service.py     (NEW)

tests/integration/personalization/
  └── test_interest_extraction_flow.py        (NEW)

tests/e2e/personalization/
  └── test_interest_aware_replies.py          (NEW)
```

### Modified Files
```
src/domain/personalization/
  └── user_profile.py                         (add with_topics())

src/application/personalization/use_cases/
  └── personalized_reply.py                   (integrate service)

src/infrastructure/personalization/
  ├── factory.py                              (wire DI)
  └── metrics.py                              (add metrics)

src/infrastructure/config/
  └── settings.py                             (add config)
```

---

## Success Criteria

### Functional
- ✅ After 3-5 themed conversations, `preferred_topics` populated
- ✅ Butler responses include relevant examples from user's domains
- ✅ No sensitive data in `preferred_topics`

### Performance
- ✅ Interest extraction < 2s (P95)
- ✅ Error rate < 5%
- ✅ No significant increase in compression duration

### Quality
- ✅ Topics relevant and stable (no churn)
- ✅ Topic names canonical ("Python" not "python coding")
- ✅ Test coverage ≥80%

---

## Timeline

| Phase | Duration | Owner | Status |
| --- | --- | --- | --- |
| Development | 3 days | Dev A + Dev B | ⏳ Pending |
| Testing | Included | QA | ⏳ Pending |
| Staging Validation | 1 week | Team | ⏳ Pending |
| Production Rollout | 2 weeks (gradual) | DevOps | ⏳ Pending |

**Total**: ~4 weeks from start to 100% rollout

---

## Quick Start

```bash
# 1. Read full spec
cat docs/specs/epic_25/task_16_interest_extraction_spec.md

# 2. Read developer guide
cat docs/specs/epic_25/task_16_dev_handoff.md

# 3. Create service
# (See dev_handoff.md for code examples)

# 4. Run tests
pytest tests/unit/application/personalization/test_interest_extraction_service.py -v
pytest tests/integration/personalization/test_interest_extraction_flow.py -v

# 5. Check metrics
curl http://localhost:8000/metrics | grep interest_extraction

# 6. Enable feature flag (staging)
export INTEREST_EXTRACTION_ENABLED=true

# 7. Test with themed conversation
# (Send 55+ messages about Python/Docker)
```

---

**Status**: ✅ Ready for implementation  
**Effort**: 2-3 days development  
**Priority**: Medium (enhancement, not blocking)  
**Dependencies**: Epic 25 TL-01 to TL-07 complete

---

**Questions?** See full specification or ask Tech Lead.

