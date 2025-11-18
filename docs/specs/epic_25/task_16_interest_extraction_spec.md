# Task 16 · Interest Extraction & Profile Enrichment

**Epic**: EP25 - Personalised Butler
**Task**: Task 16 from Epic 25 Backlog
**Owner**: Dev A (Application) + Dev B (Infrastructure)
**Estimated Effort**: 2-3 days
**Date**: 2025-11-18

---

## Overview

Extend memory summarization to automatically extract and track user interests from conversations. Butler will adapt responses based on detected topics (e.g., "Python", "LLM orchestration", "Telegram bots").

**Key Goal**: Make Butler progressively smarter about what the user cares about, without requiring explicit configuration.

---

## Current State

### Existing Implementation ✅
- ✅ `UserProfile.preferred_topics: List[str]` field exists but is empty by default
- ✅ Memory compression logic in `PersonalizedReplyUseCase._compress_memory()`
- ✅ Persona prompt includes `{preferred_topics}` placeholder in templates
- ✅ Memory summarization via LLM (produces summary text only)

### Gaps to Address 🔧
- ❌ Summarization doesn't extract topics
- ❌ `preferred_topics` is never populated
- ❌ Topics aren't used to enrich responses (just shown in prompt)
- ❌ No validation to prevent sensitive data in topics

---

## Requirements

### Functional Requirements

**FR-1**: Extract Topics During Summarization
- During memory compression (`event_count > 50`), LLM should:
  - Analyze conversation history
  - Identify recurring topics, technologies, domains
  - Output structured data: `summary` + `interests`
- Example topics: "Python", "Docker", "Machine Learning", "API design", "Telegram bots"

**FR-2**: Update Profile with Interests
- After successful topic extraction:
  - Update `UserProfile.preferred_topics` with new list (3-7 items)
  - Preserve stability: merge new topics with existing (avoid churn)
  - Save updated profile to Mongo

**FR-3**: Use Topics in Persona Prompt
- `PersonalizationService.build_personalized_prompt()` already includes `preferred_topics`
- Ensure prompt guides Butler to:
  - Use relevant examples from user's domains
  - Suggest solutions in familiar technologies
  - Adapt wording to user's context

**FR-4**: Data Privacy & Safety
- **Never store sensitive data** as interests:
  - No API keys, tokens, passwords
  - No user IDs, names, personal info
  - No file paths, URLs with sensitive info
- Focus on **thematic topics only**: technologies, concepts, domains

**FR-5**: Validation & Testing
- Verify that after 3-5 themed conversations:
  - `preferred_topics` contains relevant topics
  - Butler replies reference these topics naturally
  - No sensitive data leaks into profile

---

## Design

### Architecture Layers

```
PersonalizedReplyUseCase
  ↓ (when event_count > 50)
_compress_memory()
  ↓
InterestExtractionService  ← NEW
  ↓
LLM (interest extraction prompt)
  ↓
Parse response (summary + interests)
  ↓
Merge topics with existing profile
  ↓
Update UserProfile.preferred_topics
  ↓
Save to Mongo via profile_repo
```

### Component Responsibilities

**1. InterestExtractionService** (NEW)
- **Location**: `src/application/personalization/interest_extraction_service.py`
- **Responsibilities**:
  - Build LLM prompt for interest extraction
  - Parse LLM response (extract `summary` + `interests`)
  - Merge new interests with existing topics (stable list)
  - Validate extracted topics (no sensitive data)
- **Interface**:
  ```python
  class InterestExtractionService:
      async def extract_interests(
          self,
          events: List[UserMemoryEvent],
          existing_topics: List[str]
      ) -> Tuple[str, List[str]]:
          """
          Extract summary and interests from conversation history.

          Args:
              events: List of memory events to analyze.
              existing_topics: Current preferred_topics from profile.

          Returns:
              Tuple of (summary_text, interests_list).
              interests_list is stable (3-7 items), no sensitive data.
          """
  ```

**2. PersonalizedReplyUseCase** (MODIFIED)
- **Changes**:
  - Inject `InterestExtractionService` dependency
  - In `_compress_memory()`:
    - Call `interest_extraction_service.extract_interests()` instead of basic summarization
    - Get both `summary` and `interests`
    - Update profile with new interests via `profile.with_topics(interests)`
    - Save updated profile

**3. UserProfile** (ENHANCED)
- **Add method**:
  ```python
  def with_topics(self, topics: List[str]) -> "UserProfile":
      """Create new profile with updated preferred_topics.

      Args:
          topics: New list of preferred topics (3-7 items).

      Returns:
          New UserProfile with updated topics and timestamp.
      """
  ```

**4. Interest Extraction Prompt** (NEW)
- **Location**: `config/persona_templates.yaml`
- **Add section**:
  ```yaml
  interest_extraction_prompt: |
    Analyze the following conversation history and extract:
    1. Summary: Brief summary of what was discussed (max 300 tokens)
    2. Interests: List of 3-7 recurring topics, technologies, or domains the user cares about

    Rules for interests:
    - Focus on technologies (Python, Docker), concepts (RAG, Clean Architecture), domains (ML, Telegram bots)
    - Use clear, canonical names (e.g., "Python" not "python coding")
    - Exclude sensitive data (API keys, passwords, personal info, file paths)
    - Prefer stability: if user mentioned topic before, keep it

    Output format (JSON):
    {
      "summary": "User discussed Python development and asked about...",
      "interests": ["Python", "Docker", "Clean Architecture", "Telegram bots"]
    }

    Conversation history:
    {events}

    Existing interests: {existing_topics}

    JSON output:
  ```

---

## Implementation Plan

### Stage 1: Interest Extraction Service (1 day, Dev A)

**Tasks**:
1. Create `InterestExtractionService` class
2. Implement `extract_interests()` method:
   - Build prompt from template
   - Call LLM with prompt
   - Parse JSON response
   - Validate topics (no sensitive data regex check)
   - Merge with existing topics (stable top-7)
3. Add interest extraction prompt to `config/persona_templates.yaml`
4. Add unit tests:
   - Test topic extraction from sample conversations
   - Test merging logic (new + existing → stable list)
   - Test sensitive data filtering (API keys, tokens rejected)

**Deliverables**:
- `src/application/personalization/interest_extraction_service.py`
- Updated `config/persona_templates.yaml`
- `tests/unit/application/personalization/test_interest_extraction_service.py`

---

### Stage 2: Profile Enhancement (0.5 day, Dev A)

**Tasks**:
1. Add `with_topics()` method to `UserProfile`:
   - Immutable update pattern (like `with_summary()`)
   - Update `updated_at` timestamp
2. Add unit tests for `with_topics()`

**Deliverables**:
- Updated `src/domain/personalization/user_profile.py`
- Updated `tests/unit/domain/personalization/test_user_profile.py`

---

### Stage 3: Use Case Integration (0.5 day, Dev A)

**Tasks**:
1. Update `PersonalizedReplyUseCase.__init__()`:
   - Add `interest_extraction_service` dependency
2. Modify `_compress_memory()`:
   - Replace `_summarize_events()` call with `interest_extraction_service.extract_interests()`
   - Get `(summary, interests)` tuple
   - Update profile: `profile.with_summary(summary).with_topics(interests)`
   - Save updated profile
3. Add structured logging:
   - Log extracted interests
   - Log topics added/removed

**Deliverables**:
- Updated `src/application/personalization/use_cases/personalized_reply.py`
- Updated integration tests

---

### Stage 4: Factory & DI (0.25 day, Dev B)

**Tasks**:
1. Update `create_personalized_use_cases()` factory:
   - Instantiate `InterestExtractionService`
   - Pass to `PersonalizedReplyUseCase`
2. Wire LLM client dependency

**Deliverables**:
- Updated `src/infrastructure/personalization/factory.py`

---

### Stage 5: Testing & Validation (0.75 day, QA)

**Tasks**:
1. **Integration test**: Themed conversations
   - Test scenario:
     - Send 55 messages about Python, Docker, Clean Architecture
     - Trigger compression
     - Verify `preferred_topics` contains ["Python", "Docker", "Clean Architecture"]
   - File: `tests/integration/personalization/test_interest_extraction_flow.py`

2. **E2E test**: Interest-aware responses
   - Test scenario:
     - User has `preferred_topics = ["Python", "Telegram bots"]`
     - Ask general question: "How to handle errors?"
     - Verify Butler response mentions Python or Telegram context
   - File: `tests/e2e/personalization/test_interest_aware_replies.py`

3. **Characterization test**: Sensitive data filtering
   - Test with conversations containing:
     - API keys: `sk-1234567890abcdef`
     - Passwords: `password=mysecret`
     - File paths: `/home/user/secret.txt`
   - Verify these are NOT in `preferred_topics`
   - File: `tests/unit/application/personalization/test_sensitive_data_filtering.py`

**Deliverables**:
- 3 new test files (integration + E2E + unit)
- Test coverage ≥80% for new service

---

## Technical Details

### Interest Merging Logic

```python
def _merge_interests(
    existing: List[str],
    new: List[str],
    max_items: int = 7
) -> List[str]:
    """Merge new interests with existing, preserving stability.

    Algorithm:
    1. Combine existing + new (deduplicate, case-insensitive)
    2. Rank by frequency (topics in both lists ranked higher)
    3. Keep top N (default 7)
    4. Preserve order: existing topics first, then new

    Args:
        existing: Current preferred_topics from profile.
        new: Newly extracted topics from conversation.
        max_items: Maximum topics to keep (default 7).

    Returns:
        Merged list of topics (max_items length).

    Example:
        >>> existing = ["Python", "Docker"]
        >>> new = ["Python", "Clean Architecture", "Telegram bots"]
        >>> _merge_interests(existing, new, max_items=4)
        ['Python', 'Docker', 'Clean Architecture', 'Telegram bots']
    """
    # Normalize: lowercase for comparison
    existing_normalized = {t.lower(): t for t in existing}
    new_normalized = {t.lower(): t for t in new}

    # Priority: topics in both lists (confirmed interests)
    confirmed = []
    for key in existing_normalized:
        if key in new_normalized:
            confirmed.append(existing_normalized[key])

    # Add remaining existing topics
    for topic in existing:
        if topic not in confirmed:
            confirmed.append(topic)

    # Add new topics (if space remains)
    for topic in new:
        if topic not in confirmed and len(confirmed) < max_items:
            confirmed.append(topic)

    return confirmed[:max_items]
```

### Sensitive Data Patterns (Regex)

```python
SENSITIVE_PATTERNS = [
    r"(api[_-]?key|token|password|secret|bearer)\s*[=:]\s*['\"]?[\w-]+",  # API keys
    r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
    r"/home/[\w/]+|/var/[\w/]+|C:\\Users\\[\w\\]+",  # File paths
    r"\d{13,19}",  # User IDs (Telegram)
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Emails
]

def _contains_sensitive_data(text: str) -> bool:
    """Check if text contains sensitive data patterns.

    Args:
        text: Topic candidate string.

    Returns:
        True if sensitive data detected.
    """
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
```

---

## Prompt Engineering

### Interest Extraction Prompt (Structured)

```
You are analyzing a conversation to extract user interests.

Rules:
1. Identify 3-7 recurring topics, technologies, or domains the user discusses
2. Use canonical names (e.g., "Python", "Docker", "Clean Architecture")
3. Focus on: programming languages, frameworks, concepts, domains
4. EXCLUDE: API keys, passwords, personal info, file paths, URLs with secrets
5. Prefer stability: if topic mentioned before, keep it

Conversation history:
- User: I'm learning Python and working on a Telegram bot
- Butler: Excellent choice, sir. Python is well-suited for Telegram bot development.
- User: How do I deploy it with Docker?
- Butler: Docker containerization is recommended for production deployments...
[... more events ...]

Existing interests from previous conversations:
["Python", "Telegram bots"]

Extract:
1. Summary (max 300 tokens): Brief overview of what was discussed
2. Interests (3-7 items): List of topics user cares about

Output JSON:
{
  "summary": "User discussed...",
  "interests": ["Python", "Telegram bots", "Docker", "API deployment"]
}

JSON:
```

**Expected LLM Response**:
```json
{
  "summary": "User is learning Python for Telegram bot development and asked about Docker deployment strategies. Discussed containerization best practices and production deployment workflows.",
  "interests": ["Python", "Telegram bots", "Docker", "API deployment", "Clean Architecture"]
}
```

---

## Metrics & Observability

### New Metrics

```python
# In src/infrastructure/personalization/metrics.py

interest_extraction_total = Counter(
    "interest_extraction_total",
    "Total interest extraction operations",
    ["status"]  # success, parse_error, llm_error
)

interest_extraction_duration_seconds = Histogram(
    "interest_extraction_duration_seconds",
    "Interest extraction operation duration",
)

user_interests_updated_total = Counter(
    "user_interests_updated_total",
    "Total user profile interests updates"
)

user_interests_count = Histogram(
    "user_interests_count",
    "Number of interests per user profile",
    buckets=[0, 1, 3, 5, 7, 10]
)
```

### Logging

```python
logger.info(
    "Interests extracted and profile updated",
    extra={
        "user_id": user_id,
        "new_interests": interests,
        "existing_interests": profile.preferred_topics,
        "merged_interests": updated_profile.preferred_topics,
        "compression_duration_ms": duration_ms,
    }
)
```

---

## Configuration

### Environment Variables (Optional)

```bash
# In docker-compose or .env
INTEREST_EXTRACTION_ENABLED=true  # Default: true
INTEREST_EXTRACTION_MAX_TOPICS=7  # Default: 7 (3-7 range)
INTEREST_EXTRACTION_LLM_TEMPERATURE=0.3  # Lower = more deterministic
```

### Settings Update

```python
# In src/infrastructure/config/settings.py

class PersonalizationSettings(BaseSettings):
    # ... existing settings ...

    interest_extraction_enabled: bool = True
    interest_extraction_max_topics: int = Field(default=7, ge=3, le=10)
    interest_extraction_llm_temperature: float = Field(default=0.3, ge=0.0, le=1.0)
```

---

## Testing Strategy

### Unit Tests

**1. Interest Extraction Service**
- ✅ Test topic extraction from sample conversations
- ✅ Test JSON parsing (valid and malformed responses)
- ✅ Test merging logic (existing + new → stable list)
- ✅ Test sensitive data filtering (API keys, passwords rejected)
- ✅ Test max_topics constraint (3-7 items)

**2. Profile with_topics() Method**
- ✅ Test immutable update
- ✅ Test timestamp update
- ✅ Test validation (empty list → valid)

### Integration Tests

**3. Full Compression Flow**
- ✅ Scenario: 55 Python/Docker messages → verify topics extracted
- ✅ Scenario: Compression with existing topics → verify merge logic
- ✅ Scenario: LLM failure → graceful degradation (summary only)

### E2E Tests

**4. Interest-Aware Responses**
- ✅ User with `preferred_topics = ["Python", "Telegram bots"]`
- ✅ Ask generic question → verify response includes relevant context
- ✅ Metric check: verify `user_interests_count` histogram updated

**5. Characterization Tests**
- ✅ Conversations with sensitive data → verify topics clean
- ✅ Edge cases: very long topic names, special characters

---

## Rollout Plan

### Phase 1: Development & Testing (3 days)
- ✅ Implement InterestExtractionService
- ✅ Update PersonalizedReplyUseCase
- ✅ Write comprehensive tests
- ✅ Feature flag: `INTEREST_EXTRACTION_ENABLED=false` (disabled)

### Phase 2: Staging Validation (1 week)
- ✅ Deploy to staging
- ✅ Enable feature flag: `INTEREST_EXTRACTION_ENABLED=true`
- ✅ Monitor metrics: `interest_extraction_total`, `user_interests_count`
- ✅ Manual testing: themed conversations
- ✅ Verify no sensitive data leaks

### Phase 3: Production Rollout (Gradual)
- ✅ Enable for 10% of users (canary)
- ✅ Monitor error rates, extraction quality
- ✅ Gradual rollout: 25% → 50% → 100%
- ✅ Fallback: disable flag if issues detected

---

## Success Criteria

### Functional
- ✅ After 3-5 themed conversations, `preferred_topics` populated
- ✅ Butler responses include relevant examples from user's domains
- ✅ No sensitive data in `preferred_topics` (validated via tests)

### Performance
- ✅ Interest extraction < 2s (P95)
- ✅ No significant increase in compression duration
- ✅ Error rate < 5% (graceful fallback if LLM fails)

### Quality
- ✅ Topics are relevant and stable (no churn)
- ✅ Topic names are canonical (e.g., "Python" not "python coding")
- ✅ Test coverage ≥80% for new service

---

## Risk Mitigation

| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| LLM extracts sensitive data | High | Medium | Regex validation + manual review of logs in staging |
| Topic churn (list changes often) | Medium | Medium | Stable merging logic (existing topics prioritized) |
| LLM fails to parse JSON | Medium | Low | Graceful fallback: use summary only, log parse error |
| Topics too generic ("technology") | Low | Medium | Prompt engineering: prefer specific technologies |
| Performance degradation | Medium | Low | Async extraction, monitor latency metrics |

---

## Future Enhancements (Out of Scope)

1. **Topic Decay**: Remove topics not mentioned in last 100 messages
2. **Topic Ranking**: Weight topics by recency and frequency
3. **Multi-Language Topics**: Extract topics in English even for RU conversations
4. **User Feedback**: `/topics` command to view/edit interests
5. **Semantic Clustering**: Group similar topics (Python + FastAPI → Backend Development)

---

## Acceptance Checklist

- [ ] `InterestExtractionService` implemented with unit tests
- [ ] `UserProfile.with_topics()` method added
- [ ] `PersonalizedReplyUseCase._compress_memory()` updated
- [ ] Interest extraction prompt added to `persona_templates.yaml`
- [ ] Sensitive data filtering tested and validated
- [ ] Integration test: themed conversations → topics extracted
- [ ] E2E test: topics reflected in replies
- [ ] Metrics added and exposed via `/metrics`
- [ ] Feature flag `INTEREST_EXTRACTION_ENABLED` implemented
- [ ] Documentation updated (user guide, operational docs)
- [ ] Code review passed
- [ ] Staging validation complete

---

## Documentation Updates

### User Guide

Add section to `docs/guides/personalized_butler_user_guide.md`:

```markdown
## Адаптация под ваши интересы

Butler автоматически запоминает темы, которые вас интересуют, и адаптирует ответы под ваш контекст.

**Как это работает**:
- Во время общения Butler анализирует ваши вопросы и запоминает темы (например, "Python", "Docker", "Telegram боты")
- Когда вы задаёте вопросы, Butler использует примеры и предложения из ваших областей
- Темы обновляются автоматически каждые ~50 сообщений

**Конфиденциальность**:
- Сохраняются только темы (технологии, концепции)
- API ключи, пароли и личная информация НЕ сохраняются
- Все данные хранятся локально в Mongo (не отправляются в external SaaS)

**Пример**:
- Если вы часто спрашиваете про Python и Docker, Butler будет предлагать решения в Python и упоминать Docker при уместной возможности
```

### Operational Docs

Add to `docs/operational/metrics.md`:

```markdown
## Interest Extraction Metrics

- `interest_extraction_total{status}` — Total interest extraction operations (success/parse_error/llm_error)
- `interest_extraction_duration_seconds` — Interest extraction latency histogram
- `user_interests_updated_total` — Total profile updates with new interests
- `user_interests_count` — Number of interests per user (histogram, buckets: 0,1,3,5,7,10)

**Alerts**:
- High parse error rate: >10% parse errors in 5min
- Slow extractions: P95 >5s
```

---

**Spec Version**: 1.0
**Status**: Ready for implementation
**Estimated Effort**: 2-3 days
**Dependencies**: Epic 25 TL-01 to TL-07 complete
