"""User profile value object for personalization."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class UserProfile:
    """User profile with personalization preferences.

    Purpose:
        Stores user preferences for personalized interactions including
        language, persona, tone, and memory summary.

    Attributes:
        user_id: Unique user identifier (Telegram user ID as string).
        language: ISO 639-1 language code (e.g., "ru", "en").
        persona: Persona name (e.g., "Alfred-style дворецкий").
        tone: Conversation tone (e.g., "witty", "formal", "casual").
        preferred_topics: List of user's preferred topics.
        memory_summary: Compressed summary of past interactions.
        created_at: Profile creation timestamp.
        updated_at: Last profile update timestamp.

    Example:
        >>> profile = UserProfile.create_default_profile("123456789")
        >>> profile.persona
        'Alfred-style дворецкий'
        >>> profile.language
        'ru'
    """

    user_id: str
    language: str
    persona: str
    tone: str
    preferred_topics: List[str] = field(default_factory=list)
    memory_summary: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate profile data.

        Raises:
            ValueError: If user_id is empty or language is invalid.
        """
        if not self.user_id:
            raise ValueError("user_id cannot be empty")

        if not self.language:
            raise ValueError("language cannot be empty")

        # Valid ISO 639-1 codes (extend as needed)
        valid_languages = {"ru", "en", "es", "de", "fr"}
        if self.language not in valid_languages:
            raise ValueError(f"language must be one of {valid_languages}")

    @staticmethod
    def create_default_profile(user_id: str) -> "UserProfile":
        """Create default profile with Alfred persona and Russian language.

        Purpose:
            Factory method to create new user profiles with sensible defaults.
            All users start with "Alfred-style дворецкий" persona.

        Args:
            user_id: Unique user identifier.

        Returns:
            UserProfile with default settings.

        Example:
            >>> profile = UserProfile.create_default_profile("123")
            >>> profile.persona
            'Alfred-style дворецкий'
        """
        now = datetime.utcnow()
        return UserProfile(
            user_id=user_id,
            language="ru",
            persona="Alfred-style дворецкий",
            tone="witty",
            preferred_topics=[],
            memory_summary=None,
            created_at=now,
            updated_at=now,
        )

    def with_summary(self, summary: str) -> "UserProfile":
        """Create new profile with updated memory summary.

        Purpose:
            Immutable update pattern for memory summary.

        Args:
            summary: New memory summary text.

        Returns:
            New UserProfile with updated summary and timestamp.

        Example:
            >>> profile = UserProfile.create_default_profile("123")
            >>> updated = profile.with_summary("User asked about Python")
            >>> updated.memory_summary
            'User asked about Python'
        """
        return UserProfile(
            user_id=self.user_id,
            language=self.language,
            persona=self.persona,
            tone=self.tone,
            preferred_topics=self.preferred_topics,
            memory_summary=summary,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def with_topics(self, topics: List[str]) -> "UserProfile":
        """Create new profile with updated preferred_topics.

        Purpose:
            Immutable update pattern for preferred topics.
            Used during interest extraction to update user interests.

        Args:
            topics: New list of preferred topics (3-7 items recommended).

        Returns:
            New UserProfile with updated topics and timestamp.

        Example:
            >>> profile = UserProfile.create_default_profile("123")
            >>> updated = profile.with_topics(["Python", "Docker"])
            >>> updated.preferred_topics
            ['Python', 'Docker']
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
