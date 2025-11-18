# Stage TL-02: Infrastructure Repositories

**Epic**: EP25 - Personalised Butler
**Stage**: TL-02
**Duration**: 2 days
**Owner**: Dev B
**Dependencies**: TL-01
**Status**: Pending

---

## Goal

Implement Mongo-backed repositories with indexes, metrics, and comprehensive error handling.

---

## Objectives

1. Implement MongoUserProfileRepository
2. Implement MongoUserMemoryRepository
3. Create Mongo indexes and migrations
4. Add Prometheus metrics
5. Write integration tests with test containers

---

## File Structure

```
src/infrastructure/personalization/
├── __init__.py
├── profile_repository.py     # MongoUserProfileRepository
├── memory_repository.py      # MongoUserMemoryRepository
└── metrics.py                # Prometheus metrics

scripts/migrations/
└── add_personalization_indexes.py  # Mongo index creation

tests/integration/infrastructure/personalization/
├── __init__.py
├── conftest.py               # Test fixtures
├── test_profile_repository.py
└── test_memory_repository.py
```

---

## Implementation Details

### 1. Prometheus Metrics

**File**: `src/infrastructure/personalization/metrics.py`

**Requirements**:
- Counter metrics for profile reads/writes
- Counter metrics for memory operations
- Histogram for memory compression duration

**Implementation**:

```python
"""Prometheus metrics for personalization."""

from prometheus_client import Counter, Histogram

# Profile metrics
user_profile_reads_total = Counter(
    "user_profile_reads_total",
    "Total user profile reads from repository"
)

user_profile_writes_total = Counter(
    "user_profile_writes_total",
    "Total user profile writes to repository"
)

# Memory metrics
user_memory_events_total = Counter(
    "user_memory_events_total",
    "Total memory events appended",
    ["role"]  # Labels: user, assistant
)

user_memory_compressions_total = Counter(
    "user_memory_compressions_total",
    "Total memory compressions performed"
)

user_memory_compression_duration_seconds = Histogram(
    "user_memory_compression_duration_seconds",
    "Memory compression duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)
```

---

### 2. MongoUserProfileRepository

**File**: `src/infrastructure/personalization/profile_repository.py`

**Requirements**:
- Auto-create default profile if missing
- Upsert on save
- Increment metrics on operations
- Structured logging
- Error handling with specific exceptions

**Implementation**:

```python
"""Mongo-backed user profile repository."""

from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from src.domain.interfaces.personalization import UserProfileRepository
from src.domain.personalization.user_profile import UserProfile
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.metrics import (
    user_profile_reads_total,
    user_profile_writes_total,
)

logger = get_logger("profile_repository")


class MongoUserProfileRepository:
    """Mongo-backed repository for user profiles.

    Purpose:
        Implements UserProfileRepository protocol using MongoDB.
        Handles persistence, retrieval, and default profile creation.

    Attributes:
        collection: MongoDB collection for user_profiles.

    Example:
        >>> from motor.motor_asyncio import AsyncIOMotorClient
        >>> client = AsyncIOMotorClient("mongodb://localhost:27017")
        >>> repo = MongoUserProfileRepository(client, "butler")
        >>> profile = await repo.get("123456789")
    """

    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        database: str = "butler"
    ) -> None:
        """Initialize repository with Mongo client.

        Args:
            mongo_client: Motor async Mongo client.
            database: Database name (default: "butler").
        """
        self.collection = mongo_client[database]["user_profiles"]
        logger.info(
            "MongoUserProfileRepository initialized",
            extra={"database": database, "collection": "user_profiles"}
        )

    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID (auto-create if missing).

        Purpose:
            Retrieve user profile from MongoDB. If profile doesn't exist,
            automatically create and save default profile.

        Args:
            user_id: User identifier.

        Returns:
            UserProfile (newly created if didn't exist).

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> profile = await repo.get("123")
            >>> profile.persona
            'Alfred-style дворецкий'
        """
        user_profile_reads_total.inc()

        try:
            doc = await self.collection.find_one({"user_id": user_id})

            if not doc:
                # Auto-create default profile
                logger.info(
                    "Profile not found, creating default",
                    extra={"user_id": user_id}
                )
                profile = UserProfile.create_default_profile(user_id)
                await self.save(profile)
                return profile

            # Convert document to UserProfile
            profile = self._doc_to_profile(doc)
            logger.debug(
                "Profile loaded",
                extra={
                    "user_id": user_id,
                    "persona": profile.persona,
                    "language": profile.language
                }
            )
            return profile

        except PyMongoError as e:
            logger.error(
                "Failed to get profile",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            raise

    async def save(self, profile: UserProfile) -> None:
        """Save (upsert) user profile.

        Purpose:
            Persist profile to MongoDB using upsert (insert or update).

        Args:
            profile: Profile to save.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> profile = UserProfile.create_default_profile("123")
            >>> await repo.save(profile)
        """
        user_profile_writes_total.inc()

        try:
            doc = self._profile_to_doc(profile)
            await self.collection.update_one(
                {"user_id": profile.user_id},
                {"$set": doc},
                upsert=True
            )

            logger.info(
                "Profile saved",
                extra={
                    "user_id": profile.user_id,
                    "persona": profile.persona,
                    "has_summary": profile.memory_summary is not None
                }
            )

        except PyMongoError as e:
            logger.error(
                "Failed to save profile",
                extra={"user_id": profile.user_id, "error": str(e)},
                exc_info=True
            )
            raise

    async def reset(self, user_id: str) -> None:
        """Delete profile and recreate with defaults.

        Purpose:
            Remove existing profile and create fresh default profile.
            Used for "reset memory" functionality.

        Args:
            user_id: User identifier.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> await repo.reset("123")
        """
        try:
            # Delete existing profile
            await self.collection.delete_one({"user_id": user_id})

            # Create default profile
            profile = UserProfile.create_default_profile(user_id)
            await self.save(profile)

            logger.info(
                "Profile reset to defaults",
                extra={"user_id": user_id}
            )

        except PyMongoError as e:
            logger.error(
                "Failed to reset profile",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            raise

    def _doc_to_profile(self, doc: dict) -> UserProfile:
        """Convert Mongo document to UserProfile.

        Args:
            doc: MongoDB document.

        Returns:
            UserProfile value object.
        """
        return UserProfile(
            user_id=doc["user_id"],
            language=doc["language"],
            persona=doc["persona"],
            tone=doc["tone"],
            preferred_topics=doc.get("preferred_topics", []),
            memory_summary=doc.get("memory_summary"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )

    def _profile_to_doc(self, profile: UserProfile) -> dict:
        """Convert UserProfile to Mongo document.

        Args:
            profile: UserProfile value object.

        Returns:
            MongoDB document dictionary.
        """
        return {
            "user_id": profile.user_id,
            "language": profile.language,
            "persona": profile.persona,
            "tone": profile.tone,
            "preferred_topics": profile.preferred_topics,
            "memory_summary": profile.memory_summary,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }
```

**Tests** (`tests/integration/infrastructure/personalization/test_profile_repository.py`):

```python
"""Integration tests for MongoUserProfileRepository."""

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.domain.personalization.user_profile import UserProfile
from src.infrastructure.personalization.profile_repository import (
    MongoUserProfileRepository
)


@pytest.fixture
async def mongo_client():
    """Provide test MongoDB client."""
    # Use testcontainers or fakemongo for tests
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    # Cleanup
    await client.drop_database("butler_test")
    client.close()


@pytest.fixture
def repo(mongo_client):
    """Provide repository instance."""
    return MongoUserProfileRepository(mongo_client, "butler_test")


@pytest.mark.asyncio
async def test_get_creates_default_profile(repo):
    """Test that get() auto-creates default profile."""
    user_id = "test_user_123"

    # Get profile (should auto-create)
    profile = await repo.get(user_id)

    assert profile is not None
    assert profile.user_id == user_id
    assert profile.persona == "Alfred-style дворецкий"
    assert profile.language == "ru"
    assert profile.tone == "witty"


@pytest.mark.asyncio
async def test_save_and_get_profile(repo):
    """Test save and retrieve profile."""
    user_id = "test_user_456"
    profile = UserProfile.create_default_profile(user_id)

    # Save profile
    await repo.save(profile)

    # Retrieve and verify
    retrieved = await repo.get(user_id)
    assert retrieved.user_id == profile.user_id
    assert retrieved.persona == profile.persona


@pytest.mark.asyncio
async def test_reset_profile(repo):
    """Test reset profile to defaults."""
    user_id = "test_user_789"

    # Create profile with custom summary
    profile = UserProfile.create_default_profile(user_id)
    profile_with_summary = profile.with_summary("Custom summary")
    await repo.save(profile_with_summary)

    # Reset
    await repo.reset(user_id)

    # Verify reset to defaults
    reset_profile = await repo.get(user_id)
    assert reset_profile.memory_summary is None
    assert reset_profile.persona == "Alfred-style дворецкий"
```

---

### 3. MongoUserMemoryRepository

**File**: `src/infrastructure/personalization/memory_repository.py`

**Requirements**:
- Chronological event storage
- Efficient queries with indexes
- Compression logic
- Metrics and logging

**Implementation**:

```python
"""Mongo-backed user memory repository."""

from datetime import datetime
from typing import List
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from src.domain.interfaces.personalization import UserMemoryRepository
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.metrics import (
    user_memory_events_total,
    user_memory_compressions_total,
)

logger = get_logger("memory_repository")


class MongoUserMemoryRepository:
    """Mongo-backed repository for user memory events.

    Purpose:
        Implements UserMemoryRepository protocol using MongoDB.
        Stores conversation history with chronological ordering.

    Attributes:
        collection: MongoDB collection for user_memory.

    Example:
        >>> repo = MongoUserMemoryRepository(client, "butler")
        >>> events = await repo.get_recent_events("123", limit=10)
    """

    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        database: str = "butler"
    ) -> None:
        """Initialize repository with Mongo client.

        Args:
            mongo_client: Motor async Mongo client.
            database: Database name (default: "butler").
        """
        self.collection = mongo_client[database]["user_memory"]
        logger.info(
            "MongoUserMemoryRepository initialized",
            extra={"database": database, "collection": "user_memory"}
        )

    async def append_events(self, events: List[UserMemoryEvent]) -> None:
        """Append new memory events.

        Purpose:
            Insert new events into MongoDB in batch.

        Args:
            events: List of events to append.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> event = UserMemoryEvent.create_user_event("123", "Hello")
            >>> await repo.append_events([event])
        """
        if not events:
            return

        try:
            docs = [self._event_to_doc(e) for e in events]
            await self.collection.insert_many(docs)

            # Update metrics
            for event in events:
                user_memory_events_total.labels(role=event.role).inc()

            logger.info(
                "Memory events appended",
                extra={
                    "user_id": events[0].user_id,
                    "count": len(events),
                    "roles": [e.role for e in events]
                }
            )

        except PyMongoError as e:
            logger.error(
                "Failed to append events",
                extra={
                    "user_id": events[0].user_id if events else None,
                    "count": len(events),
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def get_recent_events(
        self, user_id: str, limit: int
    ) -> List[UserMemoryEvent]:
        """Get recent events in chronological order.

        Purpose:
            Retrieve most recent N events for context building.
            Returns in chronological order (oldest first).

        Args:
            user_id: User identifier.
            limit: Maximum events to return.

        Returns:
            List of recent events (chronological order).

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> events = await repo.get_recent_events("123", limit=20)
            >>> len(events) <= 20
            True
        """
        try:
            # Query with descending sort, then reverse
            cursor = self.collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit)

            docs = await cursor.to_list(length=limit)
            events = [self._doc_to_event(d) for d in docs]

            # Reverse to chronological order
            events_chronological = list(reversed(events))

            logger.debug(
                "Recent events loaded",
                extra={
                    "user_id": user_id,
                    "requested_limit": limit,
                    "actual_count": len(events_chronological)
                }
            )

            return events_chronological

        except PyMongoError as e:
            logger.error(
                "Failed to get recent events",
                extra={"user_id": user_id, "limit": limit, "error": str(e)},
                exc_info=True
            )
            raise

    async def compress(
        self, user_id: str, summary: str, keep_last_n: int
    ) -> None:
        """Compress memory by deleting old events.

        Purpose:
            Delete older events while keeping recent N events.
            Summary of deleted content stored in user profile.

        Args:
            user_id: User identifier.
            summary: Summary of deleted events (stored separately).
            keep_last_n: Number of recent events to retain.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> await repo.compress("123", "User talked about Python", 20)
        """
        user_memory_compressions_total.inc()

        try:
            # Get all events sorted descending
            cursor = self.collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1)

            all_events = await cursor.to_list(length=None)

            if len(all_events) <= keep_last_n:
                logger.info(
                    "No compression needed",
                    extra={"user_id": user_id, "event_count": len(all_events)}
                )
                return

            # Keep last N, delete rest
            keep_ids = [e["_id"] for e in all_events[:keep_last_n]]
            result = await self.collection.delete_many({
                "user_id": user_id,
                "_id": {"$nin": keep_ids}
            })

            logger.info(
                "Memory compressed",
                extra={
                    "user_id": user_id,
                    "deleted_count": result.deleted_count,
                    "kept_count": keep_last_n,
                    "summary_length": len(summary)
                }
            )

        except PyMongoError as e:
            logger.error(
                "Failed to compress memory",
                extra={
                    "user_id": user_id,
                    "keep_last_n": keep_last_n,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def count_events(self, user_id: str) -> int:
        """Count total events for user.

        Purpose:
            Get event count for compression threshold checks.

        Args:
            user_id: User identifier.

        Returns:
            Total event count.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> count = await repo.count_events("123")
            >>> count >= 0
            True
        """
        try:
            count = await self.collection.count_documents({"user_id": user_id})

            logger.debug(
                "Event count retrieved",
                extra={"user_id": user_id, "count": count}
            )

            return count

        except PyMongoError as e:
            logger.error(
                "Failed to count events",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True
            )
            raise

    def _event_to_doc(self, event: UserMemoryEvent) -> dict:
        """Convert UserMemoryEvent to Mongo document.

        Args:
            event: UserMemoryEvent value object.

        Returns:
            MongoDB document dictionary.
        """
        return {
            "event_id": str(event.event_id),
            "user_id": event.user_id,
            "role": event.role,
            "content": event.content,
            "created_at": event.created_at,
            "tags": event.tags,
        }

    def _doc_to_event(self, doc: dict) -> UserMemoryEvent:
        """Convert Mongo document to UserMemoryEvent.

        Args:
            doc: MongoDB document.

        Returns:
            UserMemoryEvent value object.
        """
        return UserMemoryEvent(
            event_id=UUID(doc["event_id"]),
            user_id=doc["user_id"],
            role=doc["role"],
            content=doc["content"],
            created_at=doc["created_at"],
            tags=doc.get("tags", []),
        )
```

**Tests** (`tests/integration/infrastructure/personalization/test_memory_repository.py`):

```python
"""Integration tests for MongoUserMemoryRepository."""

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository
)


@pytest.fixture
async def mongo_client():
    """Provide test MongoDB client."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    await client.drop_database("butler_test")
    client.close()


@pytest.fixture
def repo(mongo_client):
    """Provide repository instance."""
    return MongoUserMemoryRepository(mongo_client, "butler_test")


@pytest.mark.asyncio
async def test_append_and_get_events(repo):
    """Test appending and retrieving events."""
    user_id = "test_user_123"

    # Create events
    events = [
        UserMemoryEvent.create_user_event(user_id, "Hello"),
        UserMemoryEvent.create_assistant_event(user_id, "Hi there!"),
    ]

    # Append
    await repo.append_events(events)

    # Retrieve
    retrieved = await repo.get_recent_events(user_id, limit=10)

    assert len(retrieved) == 2
    assert retrieved[0].role == "user"
    assert retrieved[0].content == "Hello"
    assert retrieved[1].role == "assistant"


@pytest.mark.asyncio
async def test_count_events(repo):
    """Test counting events."""
    user_id = "test_user_456"

    # Initial count should be 0
    count = await repo.count_events(user_id)
    assert count == 0

    # Add events
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}")
        for i in range(5)
    ]
    await repo.append_events(events)

    # Count should be 5
    count = await repo.count_events(user_id)
    assert count == 5


@pytest.mark.asyncio
async def test_compress_memory(repo):
    """Test memory compression."""
    user_id = "test_user_789"

    # Create 30 events
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}")
        for i in range(30)
    ]
    await repo.append_events(events)

    # Compress: keep last 10
    await repo.compress(user_id, "Summary of old messages", keep_last_n=10)

    # Verify only 10 remain
    count = await repo.count_events(user_id)
    assert count == 10

    # Verify recent events are kept
    recent = await repo.get_recent_events(user_id, limit=20)
    assert len(recent) == 10
```

---

### 4. Mongo Indexes Migration

**File**: `scripts/migrations/add_personalization_indexes.py`

**Requirements**:
- Create indexes for efficient queries
- Idempotent execution
- Logging

**Implementation**:

```python
"""Add MongoDB indexes for personalization collections."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger

logger = get_logger("personalization_indexes")


async def create_indexes() -> None:
    """Create MongoDB indexes for personalization.

    Purpose:
        Create indexes for user_profiles and user_memory collections.
        Ensures efficient queries and TTL cleanup.

    Example:
        >>> await create_indexes()
    """
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.db_name]

    try:
        # User profiles indexes
        logger.info("Creating user_profiles indexes...")
        await db.user_profiles.create_index(
            [("user_id", 1)],
            unique=True,
            name="user_id_unique"
        )
        logger.info("✓ user_profiles.user_id_unique index created")

        # User memory indexes
        logger.info("Creating user_memory indexes...")

        # Compound index for efficient queries
        await db.user_memory.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="user_id_created_at"
        )
        logger.info("✓ user_memory.user_id_created_at index created")

        # TTL index for auto-cleanup (90 days)
        await db.user_memory.create_index(
            [("created_at", 1)],
            expireAfterSeconds=7776000,  # 90 days
            name="created_at_ttl"
        )
        logger.info("✓ user_memory.created_at_ttl index created (90 days)")

        logger.info("All personalization indexes created successfully")

    except Exception as e:
        logger.error(
            "Failed to create indexes",
            extra={"error": str(e)},
            exc_info=True
        )
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
```

**Usage**:

```bash
# Run migration
python scripts/migrations/add_personalization_indexes.py

# Verify indexes
mongo butler --eval "db.user_profiles.getIndexes()"
mongo butler --eval "db.user_memory.getIndexes()"
```

---

## Testing Requirements

### Integration Tests Coverage

- **MongoUserProfileRepository**: ≥80%
  - Get (auto-creation)
  - Save (upsert)
  - Reset
  - Error handling

- **MongoUserMemoryRepository**: ≥80%
  - Append events
  - Get recent events (ordering)
  - Compress (keep last N)
  - Count events
  - Error handling

### Test Execution

```bash
# Run integration tests
pytest tests/integration/infrastructure/personalization/ -v

# With coverage
pytest tests/integration/infrastructure/personalization/ --cov=src/infrastructure/personalization --cov-report=term-missing

# Run migrations
python scripts/migrations/add_personalization_indexes.py
```

---

## Acceptance Criteria

- [ ] MongoUserProfileRepository implemented
- [ ] MongoUserMemoryRepository implemented
- [ ] Prometheus metrics added
- [ ] Mongo indexes migration script created
- [ ] Integration tests with ≥80% coverage
- [ ] All docstrings complete
- [ ] Error handling with structured logging
- [ ] Metrics incremented on operations

---

## Dependencies

- **Upstream**: TL-01 (domain models)
- **Downstream**: TL-03 (personalization service), TL-04 (use cases)

---

## Deliverables

- [ ] `src/infrastructure/personalization/profile_repository.py`
- [ ] `src/infrastructure/personalization/memory_repository.py`
- [ ] `src/infrastructure/personalization/metrics.py`
- [ ] `scripts/migrations/add_personalization_indexes.py`
- [ ] `tests/integration/infrastructure/personalization/*.py`
- [ ] Integration test coverage report

---

## Next Steps

After completion:
1. Run migration to create indexes
2. Verify metrics in Prometheus
3. Code review with Tech Lead
4. Begin TL-03 (Personalization Service)

---

**Status**: Pending
**Estimated Effort**: 2 days
**Priority**: High
