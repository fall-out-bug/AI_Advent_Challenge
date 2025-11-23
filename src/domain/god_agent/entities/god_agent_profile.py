"""GodAgentProfile domain entity."""

from dataclasses import dataclass, field
from typing import List

from src.domain.god_agent.value_objects.skill import SkillType


@dataclass
class GodAgentProfile:
    """God Agent profile domain entity.

    Purpose:
        Extends UserProfile with God Agent specific preferences including
        preferred skills, permissions, and language.

    Attributes:
        user_id: Unique user identifier.
        preferred_skills: List of preferred skill types.
        language: ISO 639-1 language code (e.g., "ru", "en").
        permissions: Optional permissions dictionary.

    Example:
        >>> profile = GodAgentProfile(
        ...     user_id="user1",
        ...     preferred_skills=[SkillType.CONCIERGE, SkillType.RESEARCH],
        ...     language="en",
        ... )
        >>> len(profile.preferred_skills)
        2
    """

    user_id: str
    preferred_skills: List[SkillType] = field(default_factory=list)
    language: str = "en"
    permissions: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate GodAgentProfile attributes."""
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        if not self.language:
            raise ValueError("language cannot be empty")
