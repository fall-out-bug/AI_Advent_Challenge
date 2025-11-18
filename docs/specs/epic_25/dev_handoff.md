# Epic 25 · Developer Handoff Document

**Epic**: EP25 - Personalised Butler ("Alfred-style дворецкий")  
**Date**: 2025-11-18  
**Tech Lead**: cursor_tech_lead_v1  
**Target Audience**: Development Team

---

## Quick Start

### What You're Building
A personalised assistant layer for the Butler Telegram bot that:
- **Remembers who the user is** (profile: language, persona, tone, preferences)
- **Remembers past interactions** (per-user memory with automatic compression)
- **Responds in "Alfred-style дворецкий" persona** (snarky but caring, witty, respectful, Russian language)
- **Works with text and voice messages** (reuses EP24 voice integration)
- **Runs entirely on local infrastructure** (no external SaaS)

### Core Persona
**"Alfred-style дворецкий"** = Alfred Pennyworth from Batman:
- Polite, ironic, caring
- English humour, Russian language
- Witty but respectful
- Helpful and informative with a touch of light sarcasm

**Example interactions**:
- User: "Привет!"
- Butler: "Добрый день, сэр. Надеюсь, день проходит без излишней драмы? Чем могу быть полезен?"

- User: "Что нового?"
- Butler: "Ах, вечный вопрос. Позвольте проверить свои архивы... (показывает дайджест новостей)"

---

## Architecture Overview

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Presentation Layer (Telegram Bot)                            │
│ - MessageHandler → PersonalizedReplyUseCase                  │
│ - VoiceHandler → STT → PersonalizedReplyUseCase              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Application Layer (Use Cases)                                │
│ - PersonalizedReplyUseCase: load profile+memory → LLM       │
│ - ResetPersonalizationUseCase: clear profile+memory         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Domain Layer (Models & Interfaces)                           │
│ - UserProfile, UserMemoryEvent, MemorySlice                  │
│ - UserProfileRepository, UserMemoryRepository protocols      │
│ - PersonalizationService protocol                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Infrastructure Layer (Adapters)                              │
│ - MongoUserProfileRepository                                 │
│ - MongoUserMemoryRepository                                  │
│ - PersonalizationServiceImpl                                 │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User sends text/voice message** → Telegram Bot
2. **Handler extracts user_id** and message text
3. **PersonalizedReplyUseCase**:
   - Load `UserProfile` (create default if missing)
   - Load recent `UserMemoryEvent`s (last 20 events)
   - Check memory count: if >50 events → compress inline
   - Build `PersonalizedPrompt` (persona + memory + new message)
   - Call local LLM with prompt
   - Save user/assistant events to memory
4. **Send reply** to user via Telegram

---

## Implementation Guide

### Stage TL-01: Domain Models & Interfaces

**Deliverable**: Domain layer foundation (value objects + protocols)

#### Value Objects

**`UserProfile`** (`src/domain/personalization/user_profile.py`):
```python
@dataclass(frozen=True)
class UserProfile:
    user_id: str
    language: str  # "ru", "en"
    persona: str  # "Alfred-style дворецкий"
    tone: str  # "witty", "formal", "casual"
    preferred_topics: List[str]
    memory_summary: Optional[str]  # Compressed memory summary
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create_default_profile(user_id: str) -> "UserProfile":
        """Create default profile with Alfred persona and Russian language."""
        return UserProfile(
            user_id=user_id,
            language="ru",
            persona="Alfred-style дворецкий",
            tone="witty",
            preferred_topics=[],
            memory_summary=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
```

**`UserMemoryEvent`** (`src/domain/personalization/user_memory_event.py`):
```python
@dataclass(frozen=True)
class UserMemoryEvent:
    event_id: UUID
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    tags: List[str] = field(default_factory=list)

    @staticmethod
    def create_user_event(user_id: str, content: str) -> "UserMemoryEvent":
        return UserMemoryEvent(
            event_id=uuid4(),
            user_id=user_id,
            role="user",
            content=content,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def create_assistant_event(user_id: str, content: str) -> "UserMemoryEvent":
        return UserMemoryEvent(
            event_id=uuid4(),
            user_id=user_id,
            role="assistant",
            content=content,
            created_at=datetime.utcnow(),
        )
```

**`MemorySlice`** (`src/domain/personalization/memory_slice.py`):
```python
@dataclass
class MemorySlice:
    events: List[UserMemoryEvent]
    summary: Optional[str] = None
    total_events: int = 0

    def to_prompt_context(self) -> str:
        """Format events for prompt injection."""
        lines = []
        if self.summary:
            lines.append(f"Summary: {self.summary}\n")
        
        lines.append("Recent interactions:")
        for event in self.events[-10:]:  # Last 10 events
            role_label = "User" if event.role == "user" else "Butler"
            lines.append(f"- {role_label}: {event.content[:200]}")
        
        return "\n".join(lines)
```

**`PersonalizedPrompt`** (`src/domain/personalization/personalized_prompt.py`):
```python
@dataclass
class PersonalizedPrompt:
    persona_section: str
    memory_context: str
    new_message: str
    full_prompt: str

    def estimate_tokens(self) -> int:
        """Simple token estimation (4 chars ≈ 1 token)."""
        return len(self.full_prompt) // 4
```

#### Protocols

**Repository Protocols** (`src/domain/interfaces/personalization.py`):
```python
class UserProfileRepository(Protocol):
    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Get profile; return None if not exists."""
        ...

    async def save(self, profile: UserProfile) -> None:
        """Save (upsert) profile."""
        ...

    async def reset(self, user_id: str) -> None:
        """Delete profile and recreate default."""
        ...

class UserMemoryRepository(Protocol):
    async def append_events(self, events: List[UserMemoryEvent]) -> None:
        """Append new memory events."""
        ...

    async def get_recent_events(self, user_id: str, limit: int) -> List[UserMemoryEvent]:
        """Get recent events, sorted by created_at descending."""
        ...

    async def compress(self, user_id: str, summary: str, keep_last_n: int) -> None:
        """Compress memory: delete old events, keep last N."""
        ...

    async def count_events(self, user_id: str) -> int:
        """Count total events for user."""
        ...

class PersonalizationService(Protocol):
    async def load_profile(self, user_id: str) -> UserProfile:
        """Load profile (create default if missing)."""
        ...

    async def build_personalized_prompt(
        self, profile: UserProfile, memory_slice: MemorySlice, new_message: str
    ) -> PersonalizedPrompt:
        """Build personalized prompt for LLM."""
        ...
```

**Testing**: Unit tests for value objects (validation, factories, `to_prompt_context()`).

---

### Stage TL-02: Infrastructure Repositories

**Deliverable**: Mongo-backed repositories with indexes and metrics

#### MongoUserProfileRepository

**Implementation** (`src/infrastructure/personalization/profile_repository.py`):
```python
class MongoUserProfileRepository:
    def __init__(self, mongo_client: AsyncIOMotorClient, database: str = "butler"):
        self.collection = mongo_client[database]["user_profiles"]

    async def get(self, user_id: str) -> Optional[UserProfile]:
        doc = await self.collection.find_one({"user_id": user_id})
        if not doc:
            # Auto-create default profile
            profile = UserProfile.create_default_profile(user_id)
            await self.save(profile)
            return profile
        return self._doc_to_profile(doc)

    async def save(self, profile: UserProfile) -> None:
        await self.collection.update_one(
            {"user_id": profile.user_id},
            {"$set": self._profile_to_doc(profile)},
            upsert=True,
        )

    async def reset(self, user_id: str) -> None:
        await self.collection.delete_one({"user_id": user_id})
        # Recreate default
        profile = UserProfile.create_default_profile(user_id)
        await self.save(profile)
```

**Indexes**:
```python
# In scripts/migrations/add_personalization_indexes.py
await db.user_profiles.create_index([("user_id", 1)], unique=True)
```

#### MongoUserMemoryRepository

**Implementation** (`src/infrastructure/personalization/memory_repository.py`):
```python
class MongoUserMemoryRepository:
    def __init__(self, mongo_client: AsyncIOMotorClient, database: str = "butler"):
        self.collection = mongo_client[database]["user_memory"]

    async def append_events(self, events: List[UserMemoryEvent]) -> None:
        docs = [self._event_to_doc(e) for e in events]
        await self.collection.insert_many(docs)

    async def get_recent_events(self, user_id: str, limit: int) -> List[UserMemoryEvent]:
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        events = [self._doc_to_event(d) for d in docs]
        return list(reversed(events))  # Return in chronological order

    async def compress(self, user_id: str, summary: str, keep_last_n: int) -> None:
        # Get all events sorted by created_at
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        events = await cursor.to_list(length=None)
        
        if len(events) <= keep_last_n:
            return  # Nothing to compress
        
        # Delete older events (keep last N)
        keep_ids = [e["_id"] for e in events[:keep_last_n]]
        await self.collection.delete_many({
            "user_id": user_id,
            "_id": {"$nin": keep_ids}
        })
        
        # Update profile with summary (done in use case)

    async def count_events(self, user_id: str) -> int:
        return await self.collection.count_documents({"user_id": user_id})
```

**Indexes**:
```python
# Compound index for efficient queries
await db.user_memory.create_index([("user_id", 1), ("created_at", -1)])
# Optional TTL index (90 days auto-cleanup)
await db.user_memory.create_index([("created_at", 1)], expireAfterSeconds=7776000)
```

**Metrics** (`src/infrastructure/personalization/metrics.py`):
```python
from prometheus_client import Counter, Histogram

user_profile_reads_total = Counter(
    "user_profile_reads_total", "Total user profile reads"
)
user_profile_writes_total = Counter(
    "user_profile_writes_total", "Total user profile writes"
)
user_memory_events_total = Counter(
    "user_memory_events_total", "Total memory events appended", ["role"]
)
user_memory_compressions_total = Counter(
    "user_memory_compressions_total", "Total memory compressions"
)
```

**Testing**: Integration tests with fakemongo, verify indexes created.

---

### Stage TL-03: Personalisation Service & Prompt Assembly

**Deliverable**: Service that builds personalized prompts

#### Prompt Templates

**Templates** (`src/application/personalization/templates.py`):
```python
PERSONA_TEMPLATE = """Ты — {persona}. Твой тон: {tone}. Язык ответа: {language}.

Instructions:
- Отвечай как Alfred из Batman (вежливый, ироничный, заботливый).
- Используй английский юмор, но говори на русском.
- Будь полезным и информативным, но добавляй лёгкую иронию.
- Preferred topics: {preferred_topics}.
"""

MEMORY_CONTEXT_TEMPLATE = """Previous interactions:
{memory_events}

Summary: {summary}
"""

FULL_PROMPT_TEMPLATE = """{persona_section}

{memory_context}

User: {new_message}
Butler:"""
```

#### PersonalizationServiceImpl

**Implementation** (`src/application/personalization/personalization_service.py`):
```python
class PersonalizationServiceImpl:
    def __init__(
        self,
        profile_repo: UserProfileRepository,
        memory_repo: UserMemoryRepository,
    ):
        self.profile_repo = profile_repo
        self.memory_repo = memory_repo

    async def load_profile(self, user_id: str) -> UserProfile:
        profile = await self.profile_repo.get(user_id)
        if not profile:
            profile = UserProfile.create_default_profile(user_id)
            await self.profile_repo.save(profile)
        return profile

    async def build_personalized_prompt(
        self, profile: UserProfile, memory_slice: MemorySlice, new_message: str
    ) -> PersonalizedPrompt:
        # Build persona section
        persona_section = PERSONA_TEMPLATE.format(
            persona=profile.persona,
            tone=profile.tone,
            language=profile.language,
            preferred_topics=", ".join(profile.preferred_topics) if profile.preferred_topics else "general topics",
        )

        # Build memory context
        memory_context = memory_slice.to_prompt_context()

        # Assemble full prompt
        full_prompt = FULL_PROMPT_TEMPLATE.format(
            persona_section=persona_section,
            memory_context=memory_context,
            new_message=new_message,
        )

        # Estimate tokens
        estimated_tokens = len(full_prompt) // 4

        # Truncate if too long (>2000 tokens)
        if estimated_tokens > 2000:
            # Keep summary + last 5 events
            truncated_slice = MemorySlice(
                events=memory_slice.events[-5:],
                summary=memory_slice.summary,
                total_events=memory_slice.total_events,
            )
            memory_context = truncated_slice.to_prompt_context()
            full_prompt = FULL_PROMPT_TEMPLATE.format(
                persona_section=persona_section,
                memory_context=memory_context,
                new_message=new_message,
            )

        return PersonalizedPrompt(
            persona_section=persona_section,
            memory_context=memory_context,
            new_message=new_message,
            full_prompt=full_prompt,
        )
```

**Testing**: Unit tests with mock repos, verify prompt assembly and token truncation.

---

### Stage TL-04: Personalised Reply Use Case

**Deliverable**: Core use case that orchestrates personalised replies

#### DTOs

**Input/Output DTOs** (`src/application/personalization/dtos.py`):
```python
@dataclass
class PersonalizedReplyInput:
    user_id: str
    text: str
    source: Literal["text", "voice"] = "text"

@dataclass
class PersonalizedReplyOutput:
    reply: str
    used_persona: bool
    memory_events_used: int
```

#### PersonalizedReplyUseCase

**Implementation** (`src/application/personalization/use_cases/personalized_reply.py`):
```python
class PersonalizedReplyUseCase:
    def __init__(
        self,
        personalization_service: PersonalizationService,
        memory_repo: UserMemoryRepository,
        profile_repo: UserProfileRepository,
        llm_client: LLMClient,
    ):
        self.personalization_service = personalization_service
        self.memory_repo = memory_repo
        self.profile_repo = profile_repo
        self.llm_client = llm_client
        self.logger = get_logger("personalized_reply")

    async def execute(self, input_data: PersonalizedReplyInput) -> PersonalizedReplyOutput:
        try:
            # 1. Load profile (auto-create if missing)
            profile = await self.personalization_service.load_profile(input_data.user_id)

            # 2. Check memory count and compress if needed
            event_count = await self.memory_repo.count_events(input_data.user_id)
            if event_count > 50:
                await self._compress_memory(input_data.user_id, profile)

            # 3. Load recent memory
            recent_events = await self.memory_repo.get_recent_events(input_data.user_id, limit=20)
            memory_slice = MemorySlice(
                events=recent_events,
                summary=profile.memory_summary,
                total_events=event_count,
            )

            # 4. Build personalized prompt
            prompt = await self.personalization_service.build_personalized_prompt(
                profile, memory_slice, input_data.text
            )

            self.logger.info(
                "Built personalized prompt",
                extra={
                    "user_id": input_data.user_id,
                    "persona": profile.persona,
                    "memory_events_used": len(recent_events),
                    "prompt_tokens": prompt.estimate_tokens(),
                },
            )

            # 5. Call LLM
            reply = await self.llm_client.generate(prompt.full_prompt)

            # 6. Save interaction to memory
            user_event = UserMemoryEvent.create_user_event(input_data.user_id, input_data.text)
            assistant_event = UserMemoryEvent.create_assistant_event(input_data.user_id, reply)
            await self.memory_repo.append_events([user_event, assistant_event])

            self.logger.info(
                "Personalized reply generated",
                extra={
                    "user_id": input_data.user_id,
                    "reply_length": len(reply),
                    "source": input_data.source,
                },
            )

            return PersonalizedReplyOutput(
                reply=reply,
                used_persona=True,
                memory_events_used=len(recent_events),
            )

        except Exception as e:
            self.logger.error(
                "Failed to generate personalized reply",
                extra={"user_id": input_data.user_id, "error": str(e)},
                exc_info=True,
            )
            # Fallback message
            return PersonalizedReplyOutput(
                reply="Извините, временные технические проблемы. Попробуйте позже.",
                used_persona=False,
                memory_events_used=0,
            )

    async def _compress_memory(self, user_id: str, profile: UserProfile) -> None:
        """Inline memory compression when threshold exceeded."""
        self.logger.info("Compressing memory", extra={"user_id": user_id})
        
        # Load all events for summarization
        all_events = await self.memory_repo.get_recent_events(user_id, limit=1000)
        
        # Summarize via LLM (simple implementation for MVP)
        events_text = "\n".join([
            f"{e.role}: {e.content[:200]}" for e in all_events
        ])
        summary_prompt = f"Summarise the following conversation history in Russian (max 300 tokens):\n{events_text}"
        summary = await self.llm_client.generate(summary_prompt)
        
        # Compress: keep last 20 events
        await self.memory_repo.compress(user_id, summary, keep_last_n=20)
        
        # Update profile with summary
        updated_profile = UserProfile(
            user_id=profile.user_id,
            language=profile.language,
            persona=profile.persona,
            tone=profile.tone,
            preferred_topics=profile.preferred_topics,
            memory_summary=summary,
            created_at=profile.created_at,
            updated_at=datetime.utcnow(),
        )
        await self.profile_repo.save(updated_profile)
        
        self.logger.info("Memory compressed", extra={"user_id": user_id, "summary_length": len(summary)})
```

**Metrics**:
```python
personalized_requests_total = Counter(
    "personalized_requests_total", "Total personalized requests", ["source", "status"]
)
personalized_prompt_tokens_total = Histogram(
    "personalized_prompt_tokens_total", "Personalized prompt token count"
)
personalized_memory_compressions_total = Counter(
    "personalized_memory_compressions_total", "Total memory compressions"
)
```

**Testing**: Unit tests with mocked repos/LLM, integration tests with fake Mongo.

---

### Stage TL-05: Telegram Bot Integration

**Deliverable**: Updated handlers to use personalized use case

#### Updated Message Handler

**Before** (`src/presentation/bot/handlers/message_handler.py`):
```python
async def handle_message(message: Message):
    user_id = str(message.from_user.id)
    text = message.text
    
    # Route to ButlerOrchestrator
    reply = await butler_orchestrator.handle_user_message(user_id, text, session_id)
    await message.answer(reply)
```

**After**:
```python
async def handle_message(message: Message):
    if not settings.personalization_enabled:
        # Fallback to Butler
        reply = await butler_orchestrator.handle_user_message(...)
        await message.answer(reply)
        return

    user_id = str(message.from_user.id)
    text = message.text
    
    # Route to PersonalizedReplyUseCase
    input_data = PersonalizedReplyInput(user_id=user_id, text=text, source="text")
    output = await personalized_reply_use_case.execute(input_data)
    
    await message.answer(output.reply)
```

#### Updated Voice Handler

**After STT transcription**:
```python
# After: transcription = await process_voice_command_use_case.execute(...)

# Route transcription to personalized use case
input_data = PersonalizedReplyInput(
    user_id=user_id,
    text=transcription.text,
    source="voice"
)
output = await personalized_reply_use_case.execute(input_data)

await message.answer(
    f"🎤 Распознала: «{transcription.text}»\n\n{output.reply}"
)
```

#### Factory for DI

**Factory** (`src/infrastructure/personalization/factory.py`):
```python
def create_personalized_use_cases(
    settings: Settings,
    mongo_client: AsyncIOMotorClient,
    llm_client: LLMClient,
) -> Tuple[PersonalizedReplyUseCase, ResetPersonalizationUseCase]:
    # Create repos
    profile_repo = MongoUserProfileRepository(mongo_client, settings.mongo_database)
    memory_repo = MongoUserMemoryRepository(mongo_client, settings.mongo_database)
    
    # Create service
    personalization_service = PersonalizationServiceImpl(profile_repo, memory_repo)
    
    # Create use cases
    personalized_reply_use_case = PersonalizedReplyUseCase(
        personalization_service=personalization_service,
        memory_repo=memory_repo,
        profile_repo=profile_repo,
        llm_client=llm_client,
    )
    
    reset_use_case = ResetPersonalizationUseCase(
        profile_repo=profile_repo,
        memory_repo=memory_repo,
    )
    
    return personalized_reply_use_case, reset_use_case
```

**Testing**: Manual test (text message → verify Alfred-style reply), manual test (voice → STT → personalized reply).

---

### Stage TL-06: Admin Tools Only (no public commands)

**Deliverable**: Admin CLI for internal profile/memory management (no user-facing profile commands)

#### Admin CLI Tool

**CLI** (`scripts/tools/profile_admin.py`):
```python
import asyncio
import click
from motor.motor_asyncio import AsyncIOMotorClient

@click.group()
def cli():
    """Admin CLI for user profiles and memory."""
    pass

@cli.command()
def list():
    """List all user profiles."""
    async def _list():
        client = AsyncIOMotorClient(settings.mongodb_url)
        profiles = await client.butler.user_profiles.find().to_list(length=1000)
        for p in profiles:
            print(f"User: {p['user_id']}, Persona: {p['persona']}, Language: {p['language']}")
    asyncio.run(_list())

@cli.command()
@click.argument("user_id")
def show(user_id):
    """Show profile and memory stats for user."""
    async def _show():
        client = AsyncIOMotorClient(settings.mongodb_url)
        profile = await client.butler.user_profiles.find_one({"user_id": user_id})
        event_count = await client.butler.user_memory.count_documents({"user_id": user_id})
        print(f"Profile: {profile}")
        print(f"Memory events: {event_count}")
    asyncio.run(_show())

@cli.command()
@click.argument("user_id")
def reset(user_id):
    """Reset profile and memory for user."""
    async def _reset():
        client = AsyncIOMotorClient(settings.mongodb_url)
        await client.butler.user_profiles.delete_one({"user_id": user_id})
        await client.butler.user_memory.delete_many({"user_id": user_id})
        print(f"Reset complete for {user_id}")
    asyncio.run(_reset())

if __name__ == "__main__":
    cli()
```

**Usage**:
```bash
python scripts/tools/profile_admin.py list
python scripts/tools/profile_admin.py show 123456789
python scripts/tools/profile_admin.py reset 123456789
```

---

### Stage TL-07: Testing, Observability & Docs

**Deliverable**: Comprehensive tests, metrics, alerts, documentation

#### Integration Tests

**E2E Test** (`tests/e2e/personalization/test_personalized_flow.py`):
```python
async def test_personalized_text_flow(telegram_bot, fake_mongo, llm_client):
    """Test: text message → personalized reply → memory stored."""
    user_id = "test_user_123"
    message_text = "Привет, как дела?"
    
    # Send message
    response = await telegram_bot.send_message(user_id, message_text)
    
    # Verify reply has Alfred persona
    assert "сэр" in response.text or "надеюсь" in response.text
    
    # Verify memory stored
    events = await fake_mongo.butler.user_memory.find({"user_id": user_id}).to_list(length=10)
    assert len(events) == 2  # user + assistant
    assert events[0]["role"] == "user"
    assert events[0]["content"] == message_text
    assert events[1]["role"] == "assistant"

async def test_memory_compression(telegram_bot, fake_mongo, llm_client):
    """Test: >50 messages → memory compressed."""
    user_id = "test_user_compression"
    
    # Send 51 messages
    for i in range(51):
        await telegram_bot.send_message(user_id, f"Message {i}")
    
    # Verify compression triggered
    event_count = await fake_mongo.butler.user_memory.count_documents({"user_id": user_id})
    assert event_count <= 20  # Compressed to last 20
    
    # Verify summary exists in profile
    profile = await fake_mongo.butler.user_profiles.find_one({"user_id": user_id})
    assert profile["memory_summary"] is not None
```

#### Prometheus Alerts

**Alerts** (`config/prometheus/alerts/personalization.yml`):
```yaml
groups:
  - name: personalization
    rules:
      - alert: PersonalizationHighErrorRate
        expr: rate(personalized_requests_total{status="error"}[5m]) / rate(personalized_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in personalized requests (>10%)"

      - alert: MemoryCompressionFailures
        expr: rate(personalized_memory_compressions_total{status="error"}[5m]) > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Memory compression failures (>5 in 5min)"
```

#### Documentation

**User Guide** (`docs/user_guides/personalized_butler.md`):
```markdown
# Personalised Butler User Guide

## What is Personalised Butler?

Butler теперь помнит вас и ваши предыдущие разговоры! Бот использует персону "Alfred-style дворецкий" (вежливый, ироничный, заботливый).

## How it Works

- **Automatic**: Персонализация включена автоматически для всех сообщений
- **Memory**: Бот помнит последние 50 сообщений (старые автоматически сжимаются)
- **Persona**: Ответы в стиле Alfred из Batman (английский юмор, русский язык)

## Commands

- `/profile` — показать ваш профиль
- `/profile reset` — сбросить профиль и память (начать заново)

## Privacy

- Все данные хранятся локально в Mongo (не отправляются в external SaaS)
- История автоматически удаляется через 90 дней
```

---

## Configuration

### Environment Variables

Add to `docker-compose.butler.yml` or `.env`:

```bash
# Personalisation
PERSONALIZATION_ENABLED=true  # Default: true (set to false to disable)

# Mongo (already configured from EP24)
MONGODB_URL=mongodb://admin:password@shared-mongo:27017/butler?authSource=admin

# LLM (already configured)
LLM_API_URL=http://llm-api:8000
```

---

## Testing Checklist

### Manual Testing
- [ ] Send text message → verify Alfred-style reply
- [ ] Send voice message → verify STT → personalized reply
- [ ] Send 51 messages → verify memory compression triggered
- [ ] Run `/profile` → verify profile displayed
- [ ] Run `/profile reset` → verify memory cleared
- [ ] Run `profile_admin.py list` → verify CLI works

### Automated Testing
- [ ] Unit tests pass (`pytest tests/unit/personalization`)
- [ ] Integration tests pass (`pytest tests/integration/personalization`)
- [ ] E2E tests pass (`pytest tests/e2e/personalization`)
- [ ] Metrics visible (`curl http://localhost:8000/metrics | grep personalized_`)

---

## Common Issues & Troubleshooting

### Issue: Replies are generic, not personalized
- **Check**: `PERSONALIZATION_ENABLED=true` in environment
- **Check**: Logs show "Built personalized prompt" message
- **Check**: Profile exists in `user_profiles` collection

### Issue: Memory not compressing
- **Check**: Event count >50 via `profile_admin.py show <user_id>`
- **Check**: LLM API accessible for summarization
- **Check**: Logs show "Compressing memory" message

### Issue: `/profile reset` not working
- **Check**: User has admin permissions (if access control implemented)
- **Check**: Mongo connection working
- **Check**: Logs for errors

---

## References

- **Epic 25 Plan**: `docs/specs/epic_25/tech_lead_plan.md`
- **Acceptance Matrix**: `docs/specs/epic_25/acceptance_matrix.md`
- **Architecture**: `docs/specs/epic_25/architect_plan.md`
- **User Guide**: `docs/user_guides/personalized_butler.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-18  
**Status**: Ready for implementation

