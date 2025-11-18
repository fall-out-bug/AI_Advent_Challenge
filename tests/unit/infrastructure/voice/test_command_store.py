"""Unit tests for voice command store implementations.

Purpose:
    Tests Redis and in-memory implementations of VoiceCommandStore.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Optional
from uuid import uuid4

import pytest

from src.domain.voice.value_objects import (
    TranscriptionResult,
    VoiceCommand,
    VoiceCommandState,
)
from src.infrastructure.voice.command_store import InMemoryVoiceCommandStore
from src.infrastructure.voice.redis_command_store import RedisVoiceCommandStore


class FakeAsyncRedis:
    """Fake async Redis client for testing.

    Purpose:
        Minimal implementation of Redis commands needed for voice command store.
    """

    def __init__(self) -> None:
        self._storage: dict[str, tuple[bytes, float]] = {}

    async def get(self, key: str) -> Optional[bytes]:
        """Get value by key."""
        if key not in self._storage:
            return None
        value, expires_at = self._storage[key]
        if time.time() >= expires_at:
            del self._storage[key]
            return None
        return value

    async def setex(self, key: str, ttl: int, value: bytes) -> None:
        """Set value with TTL."""
        expires_at = time.time() + ttl
        self._storage[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        """Delete key."""
        if key in self._storage:
            del self._storage[key]

    async def aclose(self) -> None:
        """Close client (no-op for fake)."""
        pass


class TestInMemoryVoiceCommandStore:
    """Test in-memory voice command store."""

    async def test_save_and_get(self) -> None:
        """Save and retrieve voice command."""
        store = InMemoryVoiceCommandStore()
        command_id = uuid4()

        transcription = TranscriptionResult(
            text="Сделай дайджест",
            confidence=0.85,
            language="ru",
            duration_ms=2000,
        )
        command = VoiceCommand(
            id=command_id,
            user_id="123456789",
            transcription=transcription,
            state=VoiceCommandState.PENDING,
        )

        await store.save(command, ttl_seconds=600)

        retrieved = await store.get(command_id)

        assert retrieved is not None
        assert retrieved.id == command_id
        assert retrieved.user_id == "123456789"
        assert retrieved.transcription.text == "Сделай дайджест"
        assert retrieved.transcription.confidence == 0.85
        assert retrieved.state == VoiceCommandState.PENDING

    async def test_get_nonexistent_returns_none(self) -> None:
        """Getting non-existent command returns None."""
        store = InMemoryVoiceCommandStore()
        command_id = uuid4()

        result = await store.get(command_id)

        assert result is None

    async def test_delete(self) -> None:
        """Delete voice command."""
        store = InMemoryVoiceCommandStore()
        command_id = uuid4()

        transcription = TranscriptionResult(text="Test", confidence=0.9)
        command = VoiceCommand(
            id=command_id,
            user_id="123456789",
            transcription=transcription,
        )

        await store.save(command, ttl_seconds=600)
        await store.delete(command_id)

        result = await store.get(command_id)
        assert result is None

    async def test_expiration(self) -> None:
        """Expired commands are not returned."""
        store = InMemoryVoiceCommandStore()
        command_id = uuid4()

        transcription = TranscriptionResult(text="Test", confidence=0.9)
        command = VoiceCommand(
            id=command_id,
            user_id="123456789",
            transcription=transcription,
        )

        # Save with 0.1 second TTL
        await store.save(command, ttl_seconds=0)

        # Wait a bit
        await asyncio.sleep(0.2)

        # Should return None (expired)
        result = await store.get(command_id)
        assert result is None


class TestRedisVoiceCommandStore:
    """Test Redis voice command store."""

    @pytest.fixture
    async def redis_client(self):
        """Create fake Redis client for testing."""
        client = FakeAsyncRedis()
        try:
            yield client
        finally:
            await client.aclose()

    async def test_save_and_get(self, redis_client) -> None:
        """Save and retrieve voice command from Redis."""
        store = RedisVoiceCommandStore(redis_client=redis_client)
        command_id = uuid4()

        transcription = TranscriptionResult(
            text="Сделай дайджест",
            confidence=0.85,
            language="ru",
            duration_ms=2000,
        )
        command = VoiceCommand(
            id=command_id,
            user_id="123456789",
            transcription=transcription,
            state=VoiceCommandState.PENDING,
        )

        await store.save(command, ttl_seconds=600)

        retrieved = await store.get(command_id)

        assert retrieved is not None
        assert retrieved.id == command_id
        assert retrieved.user_id == "123456789"
        assert retrieved.transcription.text == "Сделай дайджест"
        assert retrieved.transcription.confidence == 0.85
        assert retrieved.state == VoiceCommandState.PENDING

    async def test_get_nonexistent_returns_none(self, redis_client) -> None:
        """Getting non-existent command returns None."""
        store = RedisVoiceCommandStore(redis_client=redis_client)
        command_id = uuid4()

        result = await store.get(command_id)

        assert result is None

    async def test_delete(self, redis_client) -> None:
        """Delete voice command from Redis."""
        store = RedisVoiceCommandStore(redis_client=redis_client)
        command_id = uuid4()

        transcription = TranscriptionResult(text="Test", confidence=0.9)
        command = VoiceCommand(
            id=command_id,
            user_id="123456789",
            transcription=transcription,
        )

        await store.save(command, ttl_seconds=600)
        await store.delete(command_id)

        result = await store.get(command_id)
        assert result is None

    async def test_close(self, redis_client) -> None:
        """Close Redis client connection."""
        store = RedisVoiceCommandStore(redis_client=redis_client)

        await store.close()

        # Should not raise
        assert True

