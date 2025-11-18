"""Personalized reply use case."""

import time
from typing import TYPE_CHECKING, Optional, Protocol

from src.application.personalization.dtos import (
    PersonalizedReplyInput,
    PersonalizedReplyOutput,
)
from src.domain.interfaces.personalization import (
    PersonalizationService,
    UserMemoryRepository,
    UserProfileRepository,
)
from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.domain.personalization.user_profile import UserProfile
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.metrics import (
    personalized_prompt_tokens_total,
    personalized_requests_total,
    user_interests_count,
    user_interests_updated_total,
    user_memory_compression_duration_seconds,
    user_memory_compressions_total,
)

if TYPE_CHECKING:
    from src.application.personalization.interest_extraction_service import (
        InterestExtractionService,
    )

logger = get_logger("personalized_reply_use_case")

# Memory cap: compress when exceeds this threshold
MEMORY_CAP = 50
# Keep this many events after compression
KEEP_AFTER_COMPRESSION = 20
# Max events to load for context
MAX_CONTEXT_EVENTS = 20


class LLMClient(Protocol):
    """Protocol for LLM client.

    Purpose:
        Defines interface for LLM text generation.
        Compatible with infrastructure LLM clients.
    """

    async def generate(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 256
    ) -> str:
        """Generate text from prompt.

        Args:
            prompt: Input prompt text.
            temperature: Sampling temperature (default: 0.2).
            max_tokens: Maximum tokens to generate (default: 256).

        Returns:
            Generated text response.
        """
        ...


class PersonalizedReplyUseCase:
    """Use case for generating personalized replies.

    Purpose:
        Orchestrates profile loading, memory management, prompt assembly,
        and LLM generation for personalized interactions.

    Attributes:
        personalization_service: Service for profile and prompt operations.
        memory_repo: Repository for user memory.
        profile_repo: Repository for user profiles.
        llm_client: Client for LLM generation.
        interest_extraction_service: Optional service for interest extraction.

    Example:
        >>> use_case = PersonalizedReplyUseCase(
        ...     personalization_service,
        ...     memory_repo,
        ...     profile_repo,
        ...     llm_client,
        ...     interest_extraction_service
        ... )
        >>> input_data = PersonalizedReplyInput(user_id="123", text="Hello")
        >>> output = await use_case.execute(input_data)
    """

    def __init__(
        self,
        personalization_service: PersonalizationService,
        memory_repo: UserMemoryRepository,
        profile_repo: UserProfileRepository,
        llm_client: LLMClient,
        interest_extraction_service: Optional["InterestExtractionService"] = None,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            personalization_service: Service for personalization operations.
            memory_repo: Repository for user memory.
            profile_repo: Repository for user profiles.
            llm_client: Client for LLM generation.
            interest_extraction_service: Optional service for interest extraction.
        """
        self.personalization_service = personalization_service
        self.memory_repo = memory_repo
        self.profile_repo = profile_repo
        self.llm_client = llm_client
        self.interest_extraction_service = interest_extraction_service
        logger.info(
            "PersonalizedReplyUseCase initialized",
            extra={
                "interest_extraction_enabled": interest_extraction_service is not None
            },
        )

    async def execute(
        self, input_data: PersonalizedReplyInput
    ) -> PersonalizedReplyOutput:
        """Execute personalized reply generation.

        Purpose:
            Main orchestration method that:
            1. Loads profile (auto-create if missing)
            2. Checks memory count and compresses if needed
            3. Loads recent memory
            4. Builds personalized prompt
            5. Calls LLM
            6. Saves interaction to memory

        Args:
            input_data: Input DTO with user_id, text, source.

        Returns:
            PersonalizedReplyOutput with reply and metadata.

        Example:
            >>> input_data = PersonalizedReplyInput("123", "Hello")
            >>> output = await use_case.execute(input_data)
            >>> output.reply
            'Good day, sir. How may I assist you?'
        """
        try:
            start_time = time.time()

            # 1. Load profile (auto-create if missing)
            profile = await self.personalization_service.load_profile(
                input_data.user_id
            )

            # 2. Check memory count and compress if needed
            event_count = await self.memory_repo.count_events(input_data.user_id)
            compressed = False

            if event_count > MEMORY_CAP:
                logger.info(
                    "Memory exceeds cap, triggering compression",
                    extra={
                        "user_id": input_data.user_id,
                        "event_count": event_count,
                        "cap": MEMORY_CAP,
                    },
                )
                updated_profile = await self._compress_memory(
                    input_data.user_id, profile
                )
                compressed = True
                # Use updated profile from compression
                profile = updated_profile

            # 3. Load recent memory
            recent_events = await self.memory_repo.get_recent_events(
                input_data.user_id, limit=MAX_CONTEXT_EVENTS
            )

            memory_slice = MemorySlice(
                events=recent_events,
                summary=profile.memory_summary,
                total_events=event_count,
            )

            # 4. Build personalized prompt
            prompt = await self.personalization_service.build_personalized_prompt(
                profile=profile,
                memory_slice=memory_slice,
                new_message=input_data.text,
            )

            prompt_tokens = prompt.estimate_tokens()
            personalized_prompt_tokens_total.observe(prompt_tokens)

            logger.info(
                "Built personalized prompt",
                extra={
                    "user_id": input_data.user_id,
                    "persona": profile.persona,
                    "memory_events_used": len(recent_events),
                    "prompt_tokens": prompt_tokens,
                    "source": input_data.source,
                },
            )

            # 5. Call LLM
            reply = await self.llm_client.generate(
                prompt.full_prompt, temperature=0.7, max_tokens=512
            )

            # 6. Save interaction to memory
            user_event = UserMemoryEvent.create_user_event(
                input_data.user_id, input_data.text
            )
            assistant_event = UserMemoryEvent.create_assistant_event(
                input_data.user_id, reply
            )
            await self.memory_repo.append_events([user_event, assistant_event])

            elapsed = time.time() - start_time

            logger.info(
                "Personalized reply generated",
                extra={
                    "user_id": input_data.user_id,
                    "reply_length": len(reply),
                    "source": input_data.source,
                    "compressed": compressed,
                    "elapsed_seconds": round(elapsed, 2),
                },
            )

            personalized_requests_total.labels(
                source=input_data.source, status="success"
            ).inc()

            return PersonalizedReplyOutput(
                reply=reply,
                used_persona=True,
                memory_events_used=len(recent_events),
                compressed=compressed,
            )

        except Exception as e:
            logger.error(
                "Failed to generate personalized reply",
                extra={
                    "user_id": input_data.user_id,
                    "error": str(e),
                    "source": input_data.source,
                },
                exc_info=True,
            )

            personalized_requests_total.labels(
                source=input_data.source, status="error"
            ).inc()

            # Graceful fallback
            return PersonalizedReplyOutput(
                reply="Извините, временные технические проблемы. Попробуйте позже.",
                used_persona=False,
                memory_events_used=0,
                compressed=False,
            )

    async def _compress_memory(
        self, user_id: str, profile: UserProfile
    ) -> UserProfile:
        """Compress user memory and extract interests.

        Purpose:
            Summarize old events, extract user interests, and keep only recent ones.
            Updates profile with summary and interests.

        Args:
            user_id: User identifier.
            profile: Current user profile.

        Returns:
            Updated profile with summary and interests.
        """
        start_time = time.time()

        try:
            logger.info(
                "Starting memory compression", extra={"user_id": user_id}
            )

            # Load all events for summarization
            all_events = await self.memory_repo.get_recent_events(
                user_id, limit=1000
            )

            # Use interest extraction service if available
            if self.interest_extraction_service:
                # Extract summary + interests
                summary, interests = (
                    await self.interest_extraction_service.extract_interests(
                        events=all_events,
                        existing_topics=profile.preferred_topics,
                    )
                )

                # Update profile with summary + interests
                updated_profile = profile.with_summary(summary).with_topics(
                    interests
                )

                # Track metrics
                user_interests_updated_total.inc()
                user_interests_count.observe(len(interests))

                logger.info(
                    "Memory compressed with interest extraction",
                    extra={
                        "user_id": user_id,
                        "new_interests": interests,
                        "existing_interests": profile.preferred_topics,
                    },
                )
            else:
                # Fallback: simple summarization (backward compatibility)
                events_text = "\n".join([
                    f"{e.role}: {e.content[:200]}" for e in all_events
                ])

                summary_prompt = (
                    f"Summarise the following conversation history in Russian "
                    f"(max 300 tokens):\n\n{events_text}"
                )
                summary = await self.llm_client.generate(
                    summary_prompt, temperature=0.3, max_tokens=300
                )

                # Update profile with summary only
                updated_profile = profile.with_summary(summary)

            # Compress: keep last N events
            await self.memory_repo.compress(
                user_id, updated_profile.memory_summary or "", keep_last_n=KEEP_AFTER_COMPRESSION
            )

            # Save updated profile
            await self.profile_repo.save(updated_profile)

            elapsed = time.time() - start_time
            user_memory_compression_duration_seconds.observe(elapsed)
            user_memory_compressions_total.labels(status="success").inc()

            logger.info(
                "Memory compressed successfully",
                extra={
                    "user_id": user_id,
                    "total_events_before": len(all_events),
                    "kept_events": KEEP_AFTER_COMPRESSION,
                    "summary_length": len(updated_profile.memory_summary or ""),
                    "interests_count": len(updated_profile.preferred_topics),
                    "elapsed_seconds": round(elapsed, 2),
                },
            )

            return updated_profile

        except Exception as e:
            elapsed = time.time() - start_time
            user_memory_compression_duration_seconds.observe(elapsed)
            user_memory_compressions_total.labels(status="error").inc()

            logger.error(
                "Memory compression failed",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            # Don't fail the whole request on compression failure
            # Return original profile
            return profile

