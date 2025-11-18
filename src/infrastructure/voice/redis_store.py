"""Redis voice command store implementation.

Purpose:
    Implements VoiceCommandStore protocol using Redis for temporary storage.
"""

import json
from typing import Optional

import redis.asyncio as redis
from src.domain.interfaces.voice import VoiceCommandStore
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger

logger = get_logger("voice.redis_store")


class RedisVoiceCommandStore:
    """Redis-based voice command store.

    Purpose:
        Implements VoiceCommandStore protocol by storing transcribed commands
        in Redis with TTL for automatic expiration.

    Args:
        host: Redis host (default: from settings).
        port: Redis port (default: from settings).
        password: Redis password (default: from settings).
        db: Redis database number (default: 0).
        key_prefix: Key prefix for stored commands (default: "voice:command:").
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: int = 0,
        key_prefix: str = "voice:command:",
    ) -> None:
        settings = get_settings()
        self.host = host or settings.voice_redis_host
        self.port = port or settings.voice_redis_port
        self.password = password or settings.voice_redis_password
        self.db = db
        self.key_prefix = key_prefix
        self._client: Optional[redis.Redis] = None

        logger.info(
            "RedisVoiceCommandStore initialized",
            extra={
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "key_prefix": self.key_prefix,
                "has_password": self.password is not None,
                "password_length": len(self.password) if self.password else 0,
            },
        )

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client.

        Returns:
            Redis client instance.
        """
        if self._client is None:
            logger.debug(
                "Creating Redis client",
                extra={
                    "host": self.host,
                    "port": self.port,
                    "db": self.db,
                    "has_password": self.password is not None,
                },
            )
            
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=False,  # Store bytes
            )

            # Test connection
            try:
                await self._client.ping()
                logger.debug(
                    "Redis client connected",
                    extra={"host": self.host, "port": self.port},
                )
            except Exception as e:
                logger.error(
                    "Failed to connect to Redis",
                    extra={
                        "host": self.host,
                        "port": self.port,
                        "error": str(e),
                        "has_password": self.password is not None,
                    },
                    exc_info=True,
                )
                raise

        return self._client

    def _get_key(self, command_id: str, user_id: str) -> str:
        """Generate Redis key for command.

        Args:
            command_id: Unique command identifier.
            user_id: User identifier (Telegram user ID).

        Returns:
            Redis key string.
        """
        return f"{self.key_prefix}{user_id}:{command_id}"

    async def save(
        self,
        command_id: str,
        user_id: str,
        text: str,
        ttl_seconds: int = 300,
    ) -> None:
        """Save transcribed command text.

        Purpose:
            Stores command text in Redis with TTL for automatic expiration.

        Args:
            command_id: Unique command identifier.
            user_id: User identifier (Telegram user ID).
            text: Transcribed command text.
            ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes).

        Raises:
            RuntimeError: If save fails.

        Example:
            >>> store = RedisVoiceCommandStore()
            >>> await store.save(
            ...     command_id="12345678-1234-5678-1234-567812345678",
            ...     user_id="123456789",
            ...     text="Привет, мир!",
            ...     ttl_seconds=300,
            ... )
        """
        logger.debug(
            "Saving voice command",
            extra={
                "command_id": command_id,
                "user_id": user_id,
                "text_length": len(text),
                "ttl_seconds": ttl_seconds,
            },
        )

        try:
            client = await self._get_client()
            key = self._get_key(command_id, user_id)

            # Store as JSON
            value = json.dumps({"text": text}).encode("utf-8")

            await client.setex(key, ttl_seconds, value)

            logger.info(
                "Voice command saved",
                extra={
                    "command_id": command_id,
                    "user_id": user_id,
                    "key": key,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to save voice command",
                extra={
                    "command_id": command_id,
                    "user_id": user_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise RuntimeError(f"Failed to save voice command: {str(e)}") from e

    async def get(
        self,
        command_id: str,
        user_id: str,
    ) -> Optional[str]:
        """Get stored command text.

        Purpose:
            Retrieves command text from Redis by command ID and user ID.

        Args:
            command_id: Unique command identifier.
            user_id: User identifier (Telegram user ID).

        Returns:
            Stored command text, or None if not found or expired.

        Example:
            >>> store = RedisVoiceCommandStore()
            >>> text = await store.get(
            ...     command_id="12345678-1234-5678-1234-567812345678",
            ...     user_id="123456789",
            ... )
            >>> text
            'Привет, мир!'
        """
        logger.debug(
            "Getting voice command",
            extra={
                "command_id": command_id,
                "user_id": user_id,
            },
        )

        try:
            client = await self._get_client()
            key = self._get_key(command_id, user_id)

            value = await client.get(key)

            if value is None:
                logger.debug(
                    "Voice command not found",
                    extra={
                        "command_id": command_id,
                        "user_id": user_id,
                        "key": key,
                    },
                )
                return None

            # Parse JSON
            data = json.loads(value.decode("utf-8"))
            text = data.get("text", "")

            logger.debug(
                "Voice command retrieved",
                extra={
                    "command_id": command_id,
                    "user_id": user_id,
                    "text_length": len(text),
                },
            )

            return text

        except Exception as e:
            logger.error(
                "Failed to get voice command",
                extra={
                    "command_id": command_id,
                    "user_id": user_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return None

    async def delete(
        self,
        command_id: str,
        user_id: str,
    ) -> None:
        """Delete stored command.

        Purpose:
            Deletes command text from Redis by command ID and user ID.

        Args:
            command_id: Unique command identifier.
            user_id: User identifier (Telegram user ID).

        Example:
            >>> store = RedisVoiceCommandStore()
            >>> await store.delete(
            ...     command_id="12345678-1234-5678-1234-567812345678",
            ...     user_id="123456789",
            ... )
        """
        logger.debug(
            "Deleting voice command",
            extra={
                "command_id": command_id,
                "user_id": user_id,
            },
        )

        try:
            client = await self._get_client()
            key = self._get_key(command_id, user_id)

            await client.delete(key)

            logger.debug(
                "Voice command deleted",
                extra={
                    "command_id": command_id,
                    "user_id": user_id,
                    "key": key,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to delete voice command",
                extra={
                    "command_id": command_id,
                    "user_id": user_id,
                    "error": str(e),
                },
                exc_info=True,
            )

