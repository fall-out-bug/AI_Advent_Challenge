"""Personalization domain protocols."""

from typing import List, Optional, Protocol

from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.personalized_prompt import PersonalizedPrompt
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.domain.personalization.user_profile import UserProfile


class UserProfileRepository(Protocol):
    """Repository for user profiles.

    Purpose:
        Persistence interface for UserProfile value objects.
        Implementations handle storage details (Mongo, etc.).
    """

    async def get(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID.

        Args:
            user_id: User identifier.

        Returns:
            UserProfile if found, None otherwise.
        """
        ...

    async def save(self, profile: UserProfile) -> None:
        """Save (upsert) user profile.

        Args:
            profile: Profile to save.
        """
        ...

    async def reset(self, user_id: str) -> None:
        """Delete profile and recreate with defaults.

        Args:
            user_id: User identifier.
        """
        ...


class UserMemoryRepository(Protocol):
    """Repository for user memory events.

    Purpose:
        Persistence interface for UserMemoryEvent value objects.
        Supports chronological queries and memory compression.
    """

    async def append_events(self, events: List[UserMemoryEvent]) -> None:
        """Append new memory events.

        Args:
            events: List of events to append.
        """
        ...

    async def get_recent_events(
        self, user_id: str, limit: int
    ) -> List[UserMemoryEvent]:
        """Get recent events in chronological order.

        Args:
            user_id: User identifier.
            limit: Maximum events to return.

        Returns:
            List of recent events (oldest first).
        """
        ...

    async def compress(self, user_id: str, summary: str, keep_last_n: int) -> None:
        """Compress memory by deleting old events.

        Args:
            user_id: User identifier.
            summary: Summary of deleted events (stored in profile).
            keep_last_n: Number of recent events to retain.
        """
        ...

    async def count_events(self, user_id: str) -> int:
        """Count total events for user.

        Args:
            user_id: User identifier.

        Returns:
            Total event count.
        """
        ...


class PersonalizationService(Protocol):
    """Service for building personalized prompts.

    Purpose:
        Domain service for loading profiles and assembling prompts.
        Orchestrates profile + memory into LLM-ready prompts.
    """

    async def load_profile(self, user_id: str) -> UserProfile:
        """Load user profile (create default if missing).

        Args:
            user_id: User identifier.

        Returns:
            UserProfile (newly created if didn't exist).
        """
        ...

    async def build_personalized_prompt(
        self,
        profile: UserProfile,
        memory_slice: MemorySlice,
        new_message: str,
    ) -> PersonalizedPrompt:
        """Build personalized prompt for LLM.

        Args:
            profile: User profile with persona settings.
            memory_slice: Memory context (events + summary).
            new_message: Current user message.

        Returns:
            PersonalizedPrompt ready for LLM generation.
        """
        ...
