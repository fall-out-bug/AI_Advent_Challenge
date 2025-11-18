# Stage TL-08: Background Memory Compression Worker

**Epic**: EP25 - Personalised Butler  
**Stage**: TL-08  
**Duration**: 2 days  
**Owner**: Dev B  
**Dependencies**: TL-07  
**Status**: Optional (Future Enhancement)

---

## Goal

Implement background worker for periodic memory compression to offload work from request handlers.

---

## Objectives

1. Create background worker script for memory compression
2. Add distributed locking to prevent overlapping runs
3. Implement scheduler (cron/systemd)
4. Add worker metrics and logging
5. Write tests and operational runbook

---

## Rationale

### Why Background Worker?

Currently, memory compression happens inline during requests (TL-04):
- **Blocking**: Compression blocks user request (LLM summarization takes time)
- **Unpredictable**: User experiences variable response times
- **Resource spikes**: Multiple compressions can happen simultaneously

Background worker provides:
- **Non-blocking**: Compression happens asynchronously
- **Predictable**: Users get consistent response times
- **Controlled**: Compression scheduled during off-peak hours
- **Monitoring**: Centralized compression metrics

---

## File Structure

```
scripts/workers/
├── __init__.py
└── personalization_memory_worker.py  # Background worker

scripts/cron/
└── personalization_worker.crontab    # Cron schedule

tests/integration/workers/
├── __init__.py
└── test_memory_worker.py             # Worker tests

docs/operational/runbooks/
└── personalization_worker_runbook.md # Operations guide
```

---

## Implementation Details

### 1. Background Worker

**File**: `scripts/workers/personalization_memory_worker.py`

**Requirements**:
- Scan for users with >50 events
- Compress memory for each user
- Distributed locking (Redis)
- Metrics and logging
- Graceful error handling

**Implementation**:

```python
"""Background worker for memory compression.

Purpose:
    Periodically compress user memory to keep system performant.
    Runs as standalone script or cron job.

Usage:
    python scripts/workers/personalization_memory_worker.py --dry-run
    python scripts/workers/personalization_memory_worker.py --limit 100
"""

import asyncio
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import click
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.factory import (
    create_personalized_use_cases
)
from prometheus_client import Counter, Histogram, push_to_gateway

logger = get_logger("memory_worker")

# Metrics
worker_runs_total = Counter(
    "personalized_memory_worker_runs_total",
    "Total worker runs"
)
worker_errors_total = Counter(
    "personalized_memory_worker_errors_total",
    "Total worker errors"
)
worker_users_processed_total = Counter(
    "personalized_memory_worker_users_processed_total",
    "Total users processed"
)
worker_duration_seconds = Histogram(
    "personalized_memory_worker_duration_seconds",
    "Worker run duration"
)

# Constants
MEMORY_THRESHOLD = 50  # Compress when exceeds this
LOCK_TIMEOUT = 600  # 10 minutes lock timeout
LOCK_KEY = "personalization:worker:lock"


class MemoryWorker:
    """Background worker for memory compression.
    
    Purpose:
        Scan MongoDB for users exceeding memory threshold.
        Compress memory for each user using summarization.
    
    Attributes:
        settings: Application settings.
        mongo_client: MongoDB client.
        redis_client: Redis client for locking.
        llm_client: LLM client for summarization.
    """
    
    def __init__(
        self,
        settings: "Settings",
        mongo_client: AsyncIOMotorClient,
        redis_client: aioredis.Redis,
        llm_client: "LLMClient",
    ) -> None:
        """Initialize worker.
        
        Args:
            settings: Application settings.
            mongo_client: MongoDB client.
            redis_client: Redis client for locking.
            llm_client: LLM client for summarization.
        """
        self.settings = settings
        self.mongo_client = mongo_client
        self.redis_client = redis_client
        self.llm_client = llm_client
        self.db = mongo_client[settings.db_name]
        logger.info("MemoryWorker initialized")
    
    async def run(
        self,
        dry_run: bool = False,
        limit: int | None = None,
    ) -> dict:
        """Run worker to compress memories.
        
        Purpose:
            Main worker loop:
            1. Acquire distributed lock
            2. Find users exceeding threshold
            3. Compress each user's memory
            4. Release lock
        
        Args:
            dry_run: If True, only scan without compressing.
            limit: Maximum users to process (None = all).
        
        Returns:
            Dict with run statistics.
        
        Example:
            >>> worker = MemoryWorker(...)
            >>> stats = await worker.run(dry_run=False, limit=100)
            >>> stats["users_processed"]
            42
        """
        worker_runs_total.inc()
        start_time = time.time()
        
        try:
            # Acquire distributed lock
            lock_acquired = await self._acquire_lock()
            if not lock_acquired:
                logger.warning("Failed to acquire lock, another worker running")
                return {
                    "success": False,
                    "reason": "lock_not_acquired",
                    "users_processed": 0,
                }
            
            logger.info("Lock acquired, starting worker run")
            
            # Find users exceeding threshold
            users_to_compress = await self._find_users_exceeding_threshold()
            
            logger.info(
                f"Found {len(users_to_compress)} users exceeding threshold",
                extra={"count": len(users_to_compress)}
            )
            
            if dry_run:
                logger.info("Dry run mode, skipping compression")
                return {
                    "success": True,
                    "dry_run": True,
                    "users_found": len(users_to_compress),
                    "users_processed": 0,
                }
            
            # Process users (with limit)
            users_to_process = users_to_compress[:limit] if limit else users_to_compress
            processed_count = 0
            error_count = 0
            
            for user_data in users_to_process:
                user_id = user_data["user_id"]
                event_count = user_data["event_count"]
                
                try:
                    await self._compress_user_memory(user_id, event_count)
                    processed_count += 1
                    worker_users_processed_total.inc()
                    
                    logger.info(
                        "User memory compressed",
                        extra={
                            "user_id": user_id,
                            "event_count_before": event_count,
                        }
                    )
                    
                except Exception as e:
                    error_count += 1
                    worker_errors_total.inc()
                    logger.error(
                        "Failed to compress user memory",
                        extra={"user_id": user_id, "error": str(e)},
                        exc_info=True,
                    )
            
            elapsed = time.time() - start_time
            worker_duration_seconds.observe(elapsed)
            
            logger.info(
                "Worker run complete",
                extra={
                    "processed": processed_count,
                    "errors": error_count,
                    "elapsed_seconds": round(elapsed, 2),
                }
            )
            
            return {
                "success": True,
                "users_found": len(users_to_compress),
                "users_processed": processed_count,
                "errors": error_count,
                "elapsed_seconds": elapsed,
            }
            
        except Exception as e:
            worker_errors_total.inc()
            logger.error(
                "Worker run failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            return {
                "success": False,
                "reason": str(e),
                "users_processed": 0,
            }
        finally:
            # Release lock
            await self._release_lock()
            logger.info("Lock released")
    
    async def _acquire_lock(self) -> bool:
        """Acquire distributed lock via Redis.
        
        Returns:
            True if lock acquired, False otherwise.
        """
        try:
            # SET NX EX: set if not exists with expiry
            acquired = await self.redis_client.set(
                LOCK_KEY,
                f"worker_{datetime.utcnow().isoformat()}",
                nx=True,
                ex=LOCK_TIMEOUT,
            )
            return bool(acquired)
        except Exception as e:
            logger.error(
                "Failed to acquire lock",
                extra={"error": str(e)},
                exc_info=True,
            )
            return False
    
    async def _release_lock(self) -> None:
        """Release distributed lock."""
        try:
            await self.redis_client.delete(LOCK_KEY)
        except Exception as e:
            logger.error(
                "Failed to release lock",
                extra={"error": str(e)},
                exc_info=True,
            )
    
    async def _find_users_exceeding_threshold(self) -> List[dict]:
        """Find users with event count > threshold.
        
        Returns:
            List of dicts with user_id and event_count.
        """
        # Aggregate to count events per user
        pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "event_count": {"$sum": 1}
                }
            },
            {
                "$match": {
                    "event_count": {"$gt": MEMORY_THRESHOLD}
                }
            },
            {
                "$sort": {"event_count": -1}  # Process highest first
            }
        ]
        
        cursor = self.db.user_memory.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        # Convert to list of dicts
        users = [
            {"user_id": r["_id"], "event_count": r["event_count"]}
            for r in results
        ]
        
        return users
    
    async def _compress_user_memory(
        self, user_id: str, event_count: int
    ) -> None:
        """Compress memory for single user.
        
        Args:
            user_id: User identifier.
            event_count: Current event count.
        """
        from src.infrastructure.personalization.profile_repository import (
            MongoUserProfileRepository
        )
        from src.infrastructure.personalization.memory_repository import (
            MongoUserMemoryRepository
        )
        
        profile_repo = MongoUserProfileRepository(
            self.mongo_client, self.settings.db_name
        )
        memory_repo = MongoUserMemoryRepository(
            self.mongo_client, self.settings.db_name
        )
        
        # Get profile
        profile = await profile_repo.get(user_id)
        
        # Load all events for summarization
        all_events = await memory_repo.get_recent_events(user_id, limit=1000)
        
        # Build events text for LLM
        events_text = "\n".join([
            f"{e.role}: {e.content[:200]}" for e in all_events
        ])
        
        # Summarize via LLM
        summary_prompt = (
            f"Summarise the following conversation history in Russian "
            f"(max 300 tokens):\n\n{events_text}"
        )
        summary = await self.llm_client.generate(summary_prompt)
        
        # Compress: keep last 20
        await memory_repo.compress(user_id, summary, keep_last_n=20)
        
        # Update profile with summary
        updated_profile = profile.with_summary(summary)
        await profile_repo.save(updated_profile)
        
        logger.info(
            "Memory compressed",
            extra={
                "user_id": user_id,
                "events_before": event_count,
                "summary_length": len(summary),
            }
        )


@click.command()
@click.option("--dry-run", is_flag=True, help="Scan only, don't compress")
@click.option("--limit", type=int, help="Maximum users to process")
def main(dry_run: bool, limit: int | None):
    """Run memory compression worker.
    
    Purpose:
        Background worker for compressing user memories.
    
    Example:
        python scripts/workers/personalization_memory_worker.py --dry-run
        python scripts/workers/personalization_memory_worker.py --limit 100
    """
    async def _main():
        settings = get_settings()
        
        # Initialize clients
        mongo_client = AsyncIOMotorClient(settings.mongodb_url)
        redis_client = aioredis.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}",
            password=settings.redis_password,
            encoding="utf-8",
            decode_responses=True,
        )
        
        # Mock LLM client (replace with real implementation)
        from unittest.mock import AsyncMock, MagicMock
        llm_client = MagicMock()
        llm_client.generate = AsyncMock(return_value="Summary of conversation")
        
        try:
            worker = MemoryWorker(
                settings, mongo_client, redis_client, llm_client
            )
            
            stats = await worker.run(dry_run=dry_run, limit=limit)
            
            # Print stats
            click.echo("\n=== Worker Run Statistics ===")
            click.echo(f"Success: {stats.get('success')}")
            click.echo(f"Users found: {stats.get('users_found', 0)}")
            click.echo(f"Users processed: {stats.get('users_processed', 0)}")
            if "errors" in stats:
                click.echo(f"Errors: {stats['errors']}")
            if "elapsed_seconds" in stats:
                click.echo(f"Elapsed: {stats['elapsed_seconds']:.2f}s")
            
            # Push metrics to Pushgateway (if configured)
            if settings.prometheus_pushgateway_url:
                push_to_gateway(
                    settings.prometheus_pushgateway_url,
                    job="personalization_memory_worker",
                    registry=None,  # Use default registry
                )
            
        finally:
            mongo_client.close()
            await redis_client.close()
    
    asyncio.run(_main())


if __name__ == "__main__":
    main()
```

---

### 2. Cron Schedule

**File**: `scripts/cron/personalization_worker.crontab`

```cron
# Personalization Memory Worker
# Runs daily at 2 AM (low traffic time)
# Processes up to 1000 users per run

0 2 * * * cd /app && python scripts/workers/personalization_memory_worker.py --limit 1000 >> /var/log/personalization_worker.log 2>&1
```

**Alternative: Systemd Timer**

**File**: `/etc/systemd/system/personalization-worker.timer`

```ini
[Unit]
Description=Personalization Memory Worker Timer
Requires=personalization-worker.service

[Timer]
OnCalendar=daily
OnCalendar=02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**File**: `/etc/systemd/system/personalization-worker.service`

```ini
[Unit]
Description=Personalization Memory Worker
After=network.target mongodb.service redis.service

[Service]
Type=oneshot
User=butler
WorkingDirectory=/app
Environment="PYTHONPATH=/app"
ExecStart=/app/.venv/bin/python /app/scripts/workers/personalization_memory_worker.py --limit 1000
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

### 3. Operational Runbook

**File**: `docs/operational/runbooks/personalization_worker_runbook.md`

```markdown
# Personalization Memory Worker Runbook

## Overview

Background worker for compressing user memories to maintain system performance.

## Schedule

- **Frequency**: Daily at 2 AM
- **Duration**: ~5-30 minutes (depends on user count)
- **Limit**: 1000 users per run

## Monitoring

### Metrics

- `personalized_memory_worker_runs_total` — Total runs
- `personalized_memory_worker_errors_total` — Total errors
- `personalized_memory_worker_users_processed_total` — Users processed
- `personalized_memory_worker_duration_seconds` — Run duration

### Alerts

- `MemoryWorkerHighErrors` — >5 errors in run
- `MemoryWorkerLongRunning` — Duration >30 minutes

## Operations

### Manual Run

```bash
# Dry run (scan only)
python scripts/workers/personalization_memory_worker.py --dry-run

# Process up to 100 users
python scripts/workers/personalization_memory_worker.py --limit 100

# Process all users
python scripts/workers/personalization_memory_worker.py
```

### Check Status

```bash
# Cron log
tail -f /var/log/personalization_worker.log

# Systemd status
systemctl status personalization-worker.timer
journalctl -u personalization-worker -f
```

### Troubleshooting

#### Worker Not Running

**Symptom**: No recent runs in metrics

**Check**:
```bash
# Cron
crontab -l | grep personalization

# Systemd
systemctl status personalization-worker.timer
```

**Fix**: Restart timer/cron

#### High Error Rate

**Symptom**: Many errors in run

**Check**:
- MongoDB connectivity
- Redis connectivity
- LLM service availability

**Fix**: Resolve connectivity issues, retry manually

#### Lock Timeout

**Symptom**: "Failed to acquire lock" in logs

**Reason**: Previous worker run still holds lock

**Fix**:
```bash
# Check Redis lock
redis-cli GET "personalization:worker:lock"

# Manually release (if stuck)
redis-cli DEL "personalization:worker:lock"
```

## See Also

- Worker Implementation: `scripts/workers/personalization_memory_worker.py`
- Epic 25 Documentation: `docs/specs/epic_25/`
```

---

## Testing Requirements

### Integration Tests

**File**: `tests/integration/workers/test_memory_worker.py`

```python
"""Integration tests for memory worker."""

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis

from scripts.workers.personalization_memory_worker import MemoryWorker


@pytest.fixture
async def mongo_client():
    """Provide test MongoDB client."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    await client.drop_database("butler_test")
    client.close()


@pytest.fixture
async def redis_client():
    """Provide test Redis client."""
    client = aioredis.from_url("redis://localhost:6379")
    yield client
    await client.flushdb()
    await client.close()


@pytest.mark.asyncio
async def test_worker_finds_users_exceeding_threshold(
    mongo_client, redis_client, settings, llm_client
):
    """Test worker finds users with >50 events."""
    # Seed test data: user with 51 events
    db = mongo_client.butler_test
    for i in range(51):
        await db.user_memory.insert_one({
            "event_id": str(i),
            "user_id": "test_123",
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message {i}",
            "created_at": datetime.utcnow(),
            "tags": [],
        })
    
    worker = MemoryWorker(settings, mongo_client, redis_client, llm_client)
    
    stats = await worker.run(dry_run=False, limit=10)
    
    assert stats["success"] is True
    assert stats["users_processed"] == 1


@pytest.mark.asyncio
async def test_worker_acquires_lock(redis_client, settings):
    """Test worker acquires distributed lock."""
    # ... test implementation ...


@pytest.mark.asyncio
async def test_worker_skips_if_lock_held(redis_client, settings):
    """Test worker skips run if lock already held."""
    # ... test implementation ...
```

---

## Acceptance Criteria

- [ ] Background worker implemented with distributed locking
- [ ] Cron/systemd scheduler configured
- [ ] Worker metrics added
- [ ] Operational runbook complete
- [ ] Integration tests with ≥80% coverage
- [ ] Manual testing successful
- [ ] Documentation complete

---

## Dependencies

- **Upstream**: TL-07 (testing & observability)
- **Downstream**: None (optional enhancement)

---

## Deliverables

- [ ] `scripts/workers/personalization_memory_worker.py`
- [ ] `scripts/cron/personalization_worker.crontab`
- [ ] `tests/integration/workers/test_memory_worker.py`
- [ ] `docs/operational/runbooks/personalization_worker_runbook.md`
- [ ] Systemd timer/service files (optional)

---

## Rollout Plan

1. **Phase 1**: Deploy worker without schedule (manual testing)
2. **Phase 2**: Enable cron with --limit 10 (small batch testing)
3. **Phase 3**: Increase limit to 100 (medium batch)
4. **Phase 4**: Full rollout with --limit 1000
5. **Monitor**: Track metrics and error rates

---

## Alternative: Keep Inline Compression

### When to Skip This Stage

Skip background worker if:
- User count is low (<100 active users)
- Inline compression is fast enough (<500ms)
- No user complaints about response time
- Team bandwidth limited

### Tradeoffs

**Inline Compression (Current)**:
- ✅ Simpler architecture
- ✅ No additional infrastructure
- ✅ Immediate compression
- ❌ Blocks user requests
- ❌ Variable response times

**Background Worker**:
- ✅ Non-blocking for users
- ✅ Predictable response times
- ✅ Controlled resource usage
- ❌ More complex architecture
- ❌ Requires Redis for locking
- ❌ Delayed compression

---

## Next Steps

After completion:
1. Manual worker run with --dry-run
2. Deploy worker without schedule
3. Test with small batch (--limit 10)
4. Enable scheduler
5. Monitor metrics and adjust schedule/limit

---

**Status**: Optional (Future Enhancement)  
**Estimated Effort**: 2 days  
**Priority**: Low (can defer to post-MVP)

