"""Voice command store interface and implementations.

Purpose:
    Defines interface and implementations (Redis, in-memory) for storing
    transient voice commands with TTL support.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.voice.value_objects import VoiceCommand
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class VoiceCommandStore(ABC):
    """Abstract interface for voice command storage.

    Purpose:
        Defines methods for saving, retrieving, and deleting voice commands
        with TTL support. Enables Redis primary and in-memory fallback.
    """

    @abstractmethod
    async def save(
        self,
        command: VoiceCommand,
        ttl_seconds: int,
    ) -> None:
        """Save voice command with TTL.

        Args:
            command: Voice command to save.
            ttl_seconds: Time-to-live in seconds.
        """

    @abstractmethod
    async def get(
        self,
        command_id: UUID,
    ) -> Optional[VoiceCommand]:
        """Get voice command by ID.

        Args:
            command_id: Command UUID.

        Returns:
            VoiceCommand if found, None otherwise.
        """

    @abstractmethod
    async def delete(
        self,
        command_id: UUID,
    ) -> None:
        """Delete voice command by ID.

        Args:
            command_id: Command UUID.
        """


def _voice_command_to_dict(command: VoiceCommand) -> dict:
    """Convert VoiceCommand to dictionary for serialization."""
    return {
        "id": str(command.id),
        "user_id": command.user_id,
        "transcription": {
            "text": command.transcription.text,
            "confidence": command.transcription.confidence,
            "language": command.transcription.language,
            "duration_ms": command.transcription.duration_ms,
        },
        "state": command.state.value,
        "created_at": command.created_at,
        "expires_at": command.expires_at,
    }


def _dict_to_voice_command(data: dict) -> VoiceCommand:
    """Convert dictionary to VoiceCommand."""
    from src.domain.voice.value_objects import (
        TranscriptionResult,
        VoiceCommandState,
    )

    return VoiceCommand(
        id=UUID(data["id"]),
        user_id=data["user_id"],
        transcription=TranscriptionResult(
            text=data["transcription"]["text"],
            confidence=data["transcription"]["confidence"],
            language=data["transcription"]["language"],
            duration_ms=data["transcription"]["duration_ms"],
        ),
        state=VoiceCommandState(data["state"]),
        created_at=data.get("created_at"),
        expires_at=data.get("expires_at"),
    )


class InMemoryVoiceCommandStore(VoiceCommandStore):
    """In-memory voice command store (fallback for dev/Redis outage).

    Purpose:
        Thread-safe in-memory storage with TTL expiration.
        Used when Redis is unavailable or for local development.

    Attributes:
        _storage: Dictionary mapping command_id -> (command_data, expires_at).
    """

    def __init__(self) -> None:
        """Initialize in-memory store."""
        self._storage: dict[str, tuple[dict, float]] = {}

    async def save(
        self,
        command: VoiceCommand,
        ttl_seconds: int,
    ) -> None:
        """Save voice command with TTL."""
        now = time.time()
        expires_at = now + ttl_seconds

        # Set expires_at if not already set
        if command.expires_at is None:
            command.expires_at = expires_at
        if command.created_at is None:
            command.created_at = now

        command_dict = _voice_command_to_dict(command)
        self._storage[str(command.id)] = (command_dict, expires_at)

        logger.debug(
            f"Saved voice command {command.id} with TTL {ttl_seconds}s",
            extra={"command_id": str(command.id), "ttl_seconds": ttl_seconds},
        )

    async def get(
        self,
        command_id: UUID,
    ) -> Optional[VoiceCommand]:
        """Get voice command by ID (check expiration)."""
        command_key = str(command_id)

        if command_key not in self._storage:
            return None

        command_dict, expires_at = self._storage[command_key]

        # Check expiration
        now = time.time()
        if now >= expires_at:
            # Expired, remove and return None
            del self._storage[command_key]
            logger.debug(
                f"Voice command {command_id} expired",
                extra={"command_id": str(command_id)},
            )
            return None

        return _dict_to_voice_command(command_dict)

    async def delete(
        self,
        command_id: UUID,
    ) -> None:
        """Delete voice command by ID."""
        command_key = str(command_id)
        if command_key in self._storage:
            del self._storage[command_key]
            logger.debug(
                f"Deleted voice command {command_id}",
                extra={"command_id": str(command_id)},
            )
