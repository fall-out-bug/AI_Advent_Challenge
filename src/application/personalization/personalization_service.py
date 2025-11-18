"""Personalization service implementation."""

from src.application.personalization.templates import (
    format_full_prompt,
    format_memory_context,
    format_persona_section,
)
from src.domain.interfaces.personalization import (
    PersonalizationService,
    UserProfileRepository,
)
from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.personalized_prompt import PersonalizedPrompt
from src.domain.personalization.user_profile import UserProfile
from src.infrastructure.logging import get_logger

logger = get_logger("personalization_service")

# Token limits for prompt sections
TOKEN_LIMIT_TOTAL = 2000
TOKEN_LIMIT_PERSONA = 200
TOKEN_LIMIT_MEMORY = 800
TOKEN_LIMIT_MESSAGE = 200


class PersonalizationServiceImpl:
    """Service for building personalized prompts.

    Purpose:
        Implements PersonalizationService protocol.
        Loads profiles and assembles prompts with token limits.

    Attributes:
        profile_repo: Repository for user profiles.

    Example:
        >>> service = PersonalizationServiceImpl(profile_repo)
        >>> profile = await service.load_profile("123")
        >>> prompt = await service.build_personalized_prompt(profile, memory, "Hi")
    """

    def __init__(self, profile_repo: UserProfileRepository) -> None:
        """Initialize service with profile repository.

        Args:
            profile_repo: Repository for user profiles.
        """
        self.profile_repo = profile_repo
        logger.info("PersonalizationServiceImpl initialized")

    async def load_profile(self, user_id: str) -> UserProfile:
        """Load user profile (create default if missing).

        Purpose:
            Get or create user profile with default Alfred persona.

        Args:
            user_id: User identifier.

        Returns:
            UserProfile (newly created if didn't exist).

        Example:
            >>> profile = await service.load_profile("123")
            >>> profile.persona
            'Alfred-style дворецкий'
        """
        profile = await self.profile_repo.get(user_id)

        # Repository auto-creates profile if missing, so this should never be None
        # But we check for type safety
        if profile is None:
            # Fallback: create default profile (should not happen with auto-creation)
            profile = UserProfile.create_default_profile(user_id)
            await self.profile_repo.save(profile)

        logger.info(
            "Profile loaded",
            extra={
                "user_id": user_id,
                "persona": profile.persona,
                "language": profile.language,
                "has_summary": profile.memory_summary is not None,
            },
        )

        return profile

    async def build_personalized_prompt(
        self,
        profile: UserProfile,
        memory_slice: MemorySlice,
        new_message: str,
    ) -> PersonalizedPrompt:
        """Build personalized prompt for LLM.

        Purpose:
            Assemble persona + memory + message into complete prompt.
            Applies token limits and truncation if needed.

        Args:
            profile: User profile with persona settings.
            memory_slice: Memory context (events + summary).
            new_message: Current user message.

        Returns:
            PersonalizedPrompt ready for LLM generation.

        Example:
            >>> prompt = await service.build_personalized_prompt(
            ...     profile, memory_slice, "Hello"
            ... )
            >>> prompt.estimate_tokens() <= 2000
            True
        """
        # Build persona section
        persona_section = format_persona_section(
            persona=profile.persona,
            tone=profile.tone,
            language=profile.language,
            preferred_topics=profile.preferred_topics,
        )

        # Build memory context (initial attempt with all events)
        memory_context = self._build_memory_context(memory_slice, max_events=20)

        # Build full prompt
        full_prompt = format_full_prompt(
            persona_section=persona_section,
            memory_context=memory_context,
            new_message=new_message,
        )

        # Check token limit
        estimated_tokens = len(full_prompt) // 4

        if estimated_tokens > TOKEN_LIMIT_TOTAL:
            logger.warning(
                "Prompt exceeds token limit, truncating",
                extra={
                    "user_id": profile.user_id,
                    "estimated_tokens": estimated_tokens,
                    "limit": TOKEN_LIMIT_TOTAL,
                },
            )

            # Truncate: keep summary + last 5 events
            memory_context = self._build_memory_context(memory_slice, max_events=5)
            full_prompt = format_full_prompt(
                persona_section=persona_section,
                memory_context=memory_context,
                new_message=new_message,
            )
            estimated_tokens = len(full_prompt) // 4

        prompt = PersonalizedPrompt(
            persona_section=persona_section,
            memory_context=memory_context,
            new_message=new_message,
            full_prompt=full_prompt,
        )

        logger.info(
            "Personalized prompt built",
            extra={
                "user_id": profile.user_id,
                "persona": profile.persona,
                "memory_events_used": len(memory_slice.events),
                "has_summary": memory_slice.summary is not None,
                "estimated_tokens": estimated_tokens,
            },
        )

        return prompt

    def _build_memory_context(self, memory_slice: MemorySlice, max_events: int) -> str:
        """Build memory context with event limit.

        Args:
            memory_slice: Memory slice with events and summary.
            max_events: Maximum events to include.

        Returns:
            Formatted memory context string.
        """
        # Format events
        event_strings = []
        for event in memory_slice.events[-max_events:]:
            role_label = "User" if event.role == "user" else "Butler"
            content_preview = event.content[:200]
            if len(event.content) > 200:
                content_preview += "..."
            event_strings.append(f"- {role_label}: {content_preview}")

        # Format context
        return format_memory_context(
            summary=memory_slice.summary,
            events=event_strings,
        )
