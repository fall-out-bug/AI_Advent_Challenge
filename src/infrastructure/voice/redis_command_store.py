"""Redis implementation of voice command store.

Purpose:
    Redis-based storage for voice commands with TTL support.
    Primary storage for production, falls back to in-memory on errors.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional
from uuid import UUID

import redis.asyncio as redis

from src.domain.voice.value_objects import VoiceCommand
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.voice.command_store import (
    VoiceCommandStore,
    _dict_to_voice_command,
    _voice_command_to_dict,
)

logger = get_logger(__name__)


class RedisVoiceCommandStore(VoiceCommandStore):
    """Redis-based voice command store.

    Purpose:
        Stores voice commands in Redis with TTL support.
        Uses shared Redis instance from Day 23 infrastructure.

    Args:
        redis_client: Optional Redis async client (creates new if None).
        settings: Optional settings instance (defaults to get_settings()).
        key_prefix: Redis key prefix (default "voice:command:").
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        settings: Optional[Settings] = None,
        key_prefix: str = "voice:command:",
    ) -> None:
        self.settings = settings or get_settings()
        self.key_prefix = key_prefix
        self._redis_client = redis_client
        self._owns_client = redis_client is None

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(
                    host=self.settings.redis_host,
                    port=self.settings.redis_port,
                    password=self.settings.redis_password,
                    decode_responses=False,  # We store JSON as bytes
                )
            except Exception as e:
                logger.error(
                    f"Failed to connect to Redis: {e}",
                    extra={
                        "host": self.settings.redis_host,
                        "port": self.settings.redis_port,
                    },
                )
                raise

        return self._redis_client

    def _make_key(self, command_id: UUID) -> str:
        """Generate Redis key for command ID."""
        return f"{self.key_prefix}{command_id}"

    async def save(
        self,
        command: VoiceCommand,
        ttl_seconds: int,
    ) -> None:
        """Save voice command with TTL."""
        try:
            client = await self._get_client()
            now = time.time()
            expires_at = now + ttl_seconds

            # Set expires_at if not already set
            if command.expires_at is None:
                command.expires_at = expires_at
            if command.created_at is None:
                command.created_at = now

            command_dict = _voice_command_to_dict(command)
            key = self._make_key(command.id)

            # Serialize to JSON
            value = json.dumps(command_dict, ensure_ascii=False).encode("utf-8")

            # Save with TTL
            await client.setex(key, ttl_seconds, value)

            logger.debug(
                f"Saved voice command {command.id} to Redis with TTL {ttl_seconds}s",
                extra={"command_id": str(command.id), "ttl_seconds": ttl_seconds},
            )

        except Exception as e:
            logger.error(
                f"Failed to save voice command to Redis: {e}",
                extra={"command_id": str(command.id)},
            )
            raise

    async def get(
        self,
        command_id: UUID,
    ) -> Optional[VoiceCommand]:
        """Get voice command by ID."""
        try:
            client = await self._get_client()
            key = self._make_key(command_id)

            value = await client.get(key)

            if value is None:
                return None

            # Deserialize from JSON
            command_dict = json.loads(value.decode("utf-8"))

            return _dict_to_voice_command(command_dict)

        except Exception as e:
            logger.error(
                f"Failed to get voice command from Redis: {e}",
                extra={"command_id": str(command_id)},
            )
            return None  # Fail gracefully

    async def delete(
        self,
        command_id: UUID,
    ) -> None:
        """Delete voice command by ID."""
        try:
            client = await self._get_client()
            key = self._make_key(command_id)

            await client.delete(key)

            logger.debug(
                f"Deleted voice command {command_id} from Redis",
                extra={"command_id": str(command_id)},
            )

        except Exception as e:
            logger.error(
                f"Failed to delete voice command from Redis: {e}",
                extra={"command_id": str(command_id)},
            )
            # Fail gracefully - command may have already expired

    async def close(self) -> None:
        """Close Redis client connection (if we own it)."""
        if self._redis_client is not None and self._owns_client:
            await self._redis_client.aclose()
            self._redis_client = None
