# Task 16 · Developer Handoff: Interest Extraction

**Quick Start Guide for Implementation**

---

## What You're Building

Extend memory compression to automatically extract user interests (topics like "Python", "Docker", "Telegram bots") and use them to personalize Butler responses.

**User Experience**:
- User talks about Python and Docker for several conversations
- After ~50 messages, Butler automatically extracts these interests
- Future responses include Python/Docker examples naturally

---

## Implementation Checklist

### Phase 1: Service Layer (1 day)

**Create** `src/application/personalization/interest_extraction_service.py`:

```python
from typing import List, Tuple
import json
import re

class InterestExtractionService:
    """Extract user interests from conversation history."""
    
    SENSITIVE_PATTERNS = [
        r"(api[_-]?key|token|password|secret)\s*[=:]\s*['\"]?[\w-]+",
        r"sk-[a-zA-Z0-9]{20,}",
        r"/home/[\w/]+|/var/[\w/]+",
        r"\d{13,19}",  # User IDs
    ]
    
    def __init__(self, llm_client, max_topics: int = 7):
        self._llm_client = llm_client
        self._max_topics = max_topics
        self._logger = get_logger(__name__)
    
    async def extract_interests(
        self, 
        events: List[UserMemoryEvent], 
        existing_topics: List[str]
    ) -> Tuple[str, List[str]]:
        """Extract summary + interests from conversation."""
        prompt = self._build_prompt(events, existing_topics)
        
        try:
            response = await self._llm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=512
            )
            
            # Parse JSON: {"summary": "...", "interests": [...]}
            data = json.loads(response)
            summary = data["summary"]
            new_topics = data["interests"]
            
            # Filter sensitive data
            clean_topics = [
                t for t in new_topics 
                if not self._contains_sensitive_data(t)
            ]
            
            # Merge with existing topics
            merged = self._merge_interests(existing_topics, clean_topics)
            
            return summary, merged
            
        except (json.JSONDecodeError, KeyError) as e:
            self._logger.warning("Failed to parse interests", extra={"error": str(e)})
            # Fallback: return basic summary, keep existing topics
            return self._fallback_summary(events), existing_topics
    
    def _build_prompt(
        self, 
        events: List[UserMemoryEvent], 
        existing_topics: List[str]
    ) -> str:
        """Build LLM prompt for interest extraction."""
        events_text = "\n".join([
            f"- {event.role}: {event.content[:200]}" 
            for event in events
        ])
        
        return f"""Analyze conversation and extract user interests.

Rules:
- Identify 3-7 recurring topics, technologies, or domains
- Use canonical names (Python, Docker, Clean Architecture)
- EXCLUDE: API keys, passwords, file paths, personal info
- Prefer stability: keep existing topics if still relevant

Conversation:
{events_text}

Existing interests: {existing_topics}

Output JSON:
{{"summary": "Brief overview (max 300 tokens)", "interests": ["Topic1", "Topic2", ...]}}

JSON:"""
    
    def _contains_sensitive_data(self, text: str) -> bool:
        """Check if text contains sensitive patterns."""
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _merge_interests(
        self, 
        existing: List[str], 
        new: List[str]
    ) -> List[str]:
        """Merge existing + new topics, keeping stable top-N."""
        # Normalize for comparison
        existing_norm = {t.lower(): t for t in existing}
        new_norm = {t.lower(): t for t in new}
        
        # Priority: topics in both lists
        confirmed = [
            existing_norm[key] 
            for key in existing_norm 
            if key in new_norm
        ]
        
        # Add remaining existing
        for topic in existing:
            if topic not in confirmed:
                confirmed.append(topic)
        
        # Add new topics (if space)
        for topic in new:
            if topic not in confirmed and len(confirmed) < self._max_topics:
                confirmed.append(topic)
        
        return confirmed[:self._max_topics]
    
    def _fallback_summary(self, events: List[UserMemoryEvent]) -> str:
        """Generate basic summary without LLM."""
        return f"User discussed various topics in {len(events)} messages."
```

**Tests** `tests/unit/application/personalization/test_interest_extraction_service.py`:
- Test extraction with sample conversations
- Test sensitive data filtering
- Test merging logic
- Test JSON parse errors (graceful fallback)

---

### Phase 2: Domain Enhancement (0.5 day)

**Update** `src/domain/personalization/user_profile.py`:

```python
def with_topics(self, topics: List[str]) -> "UserProfile":
    """Create new profile with updated preferred_topics.
    
    Args:
        topics: New list of preferred topics (3-7 items).
    
    Returns:
        New UserProfile with updated topics and timestamp.
    """
    return UserProfile(
        user_id=self.user_id,
        language=self.language,
        persona=self.persona,
        tone=self.tone,
        preferred_topics=topics,
        memory_summary=self.memory_summary,
        created_at=self.created_at,
        updated_at=datetime.utcnow(),
    )
```

---

### Phase 3: Use Case Integration (0.5 day)

**Update** `src/application/personalization/use_cases/personalized_reply.py`:

```python
class PersonalizedReplyUseCase:
    def __init__(
        self,
        personalization_service: PersonalizationService,
        memory_repo: UserMemoryRepository,
        profile_repo: UserProfileRepository,
        llm_client: LLMClient,
        interest_extraction_service: InterestExtractionService,  # NEW
    ):
        # ... existing init ...
        self.interest_extraction_service = interest_extraction_service
    
    async def _compress_memory(
        self, user_id: str, profile: UserProfile
    ) -> UserProfile:
        """Compress memory and extract interests."""
        start_time = time.time()
        
        # Load all events for summarization
        all_events = await self.memory_repo.get_recent_events(user_id, limit=1000)
        
        # Extract summary + interests (replaces old _summarize_events)
        summary, interests = await self.interest_extraction_service.extract_interests(
            events=all_events,
            existing_topics=profile.preferred_topics
        )
        
        # Compress events (keep last 20)
        await self.memory_repo.compress(
            user_id, 
            summary=summary, 
            keep_last_n=KEEP_AFTER_COMPRESSION
        )
        
        # Update profile with summary + interests
        updated_profile = profile.with_summary(summary).with_topics(interests)
        await self.profile_repo.save(updated_profile)
        
        # Metrics
        duration = time.time() - start_time
        user_memory_compression_duration_seconds.observe(duration)
        
        logger.info(
            "Memory compressed with interest extraction",
            extra={
                "user_id": user_id,
                "new_interests": interests,
                "existing_interests": profile.preferred_topics,
                "duration_ms": duration * 1000,
            }
        )
        
        return updated_profile
```

---

### Phase 4: Factory Update (0.25 day)

**Update** `src/infrastructure/personalization/factory.py`:

```python
def create_personalized_use_cases(...):
    # ... existing setup ...
    
    # Create interest extraction service
    interest_extraction_service = InterestExtractionService(
        llm_client=llm_client,
        max_topics=settings.interest_extraction_max_topics,
    )
    
    # Pass to use case
    personalized_reply_use_case = PersonalizedReplyUseCase(
        personalization_service=personalization_service,
        memory_repo=memory_repo,
        profile_repo=profile_repo,
        llm_client=llm_client,
        interest_extraction_service=interest_extraction_service,  # NEW
    )
    
    return personalized_reply_use_case, reset_use_case
```

---

### Phase 5: Metrics (included in service)

**Add to** `src/infrastructure/personalization/metrics.py`:

```python
interest_extraction_total = Counter(
    "interest_extraction_total",
    "Total interest extraction operations",
    ["status"]  # success, parse_error, llm_error
)

interest_extraction_duration_seconds = Histogram(
    "interest_extraction_duration_seconds",
    "Interest extraction operation duration"
)

user_interests_updated_total = Counter(
    "user_interests_updated_total",
    "Total user profile interests updates"
)
```

---

## Testing

### Unit Test Example

```python
@pytest.mark.asyncio
async def test_extract_interests_from_python_conversation():
    """Test interest extraction from Python-themed conversation."""
    # Mock LLM client
    llm_client = MockLLMClient(
        response='{"summary": "User discussed Python", "interests": ["Python", "Docker"]}'
    )
    
    service = InterestExtractionService(llm_client, max_topics=7)
    
    # Sample events
    events = [
        UserMemoryEvent.create_user_event("123", "I'm learning Python"),
        UserMemoryEvent.create_assistant_event("123", "Excellent choice, sir."),
        UserMemoryEvent.create_user_event("123", "How do I deploy with Docker?"),
    ]
    
    # Extract
    summary, interests = await service.extract_interests(events, existing_topics=[])
    
    # Verify
    assert "Python" in summary
    assert "Python" in interests
    assert "Docker" in interests
    assert len(interests) <= 7
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_themed_conversation_extracts_topics(
    real_mongodb, real_llm_client
):
    """Test: 55 Python messages → compression → topics extracted."""
    user_id = "test_user_python"
    
    # Send 55 Python-themed messages
    for i in range(55):
        await send_message(user_id, f"Python question {i}")
    
    # Verify compression triggered and topics extracted
    profile = await profile_repo.get(user_id)
    
    assert "Python" in profile.preferred_topics
    assert len(profile.preferred_topics) >= 1
    assert len(profile.preferred_topics) <= 7
```

---

## Configuration

**Add to** `src/infrastructure/config/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Interest extraction
    interest_extraction_enabled: bool = True
    interest_extraction_max_topics: int = Field(default=7, ge=3, le=10)
    interest_extraction_llm_temperature: float = Field(default=0.3, ge=0.0, le=1.0)
```

**Environment variables**:
```bash
INTEREST_EXTRACTION_ENABLED=true
INTEREST_EXTRACTION_MAX_TOPICS=7
INTEREST_EXTRACTION_LLM_TEMPERATURE=0.3
```

---

## Common Issues

### Issue: LLM returns invalid JSON
**Solution**: Service has graceful fallback (returns summary without interests, keeps existing topics)

### Issue: Sensitive data in topics
**Solution**: Regex filtering in `_contains_sensitive_data()`. Add more patterns if needed.

### Issue: Topics change too often
**Solution**: Merging logic prioritizes existing topics (stable list)

### Issue: Topics too generic ("technology")
**Solution**: Prompt engineering — ask for specific technologies/frameworks

---

## Acceptance Criteria

- [ ] Service extracts 3-7 topics from conversations
- [ ] Sensitive data filtered (API keys, passwords rejected)
- [ ] Topics reflected in Butler responses
- [ ] Test coverage ≥80%
- [ ] Metrics exposed via `/metrics`
- [ ] Graceful fallback on LLM errors

---

## Files to Create/Modify

**New Files**:
- `src/application/personalization/interest_extraction_service.py`
- `tests/unit/application/personalization/test_interest_extraction_service.py`
- `tests/integration/personalization/test_interest_extraction_flow.py`
- `tests/e2e/personalization/test_interest_aware_replies.py`

**Modified Files**:
- `src/domain/personalization/user_profile.py` (add `with_topics()`)
- `src/application/personalization/use_cases/personalized_reply.py` (integrate service)
- `src/infrastructure/personalization/factory.py` (wire DI)
- `src/infrastructure/personalization/metrics.py` (add metrics)
- `src/infrastructure/config/settings.py` (add config)

---

**Ready to Start**: Yes  
**Estimated Time**: 2-3 days  
**Dependencies**: Epic 25 TL-01 to TL-07 complete

**Questions?** See full spec: `task_16_interest_extraction_spec.md`

