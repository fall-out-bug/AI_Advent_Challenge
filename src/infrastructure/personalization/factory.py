"""Factory for creating personalization use cases."""

from typing import TYPE_CHECKING, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorClient

from src.application.personalization.personalization_service import (
    PersonalizationServiceImpl,
)
from src.application.personalization.use_cases.personalized_reply import (
    LLMClient,
    PersonalizedReplyUseCase,
)
from src.application.personalization.use_cases.reset_personalization import (
    ResetPersonalizationUseCase,
)
from src.infrastructure.config.settings import Settings
from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository,
)
from src.infrastructure.personalization.profile_repository import (
    MongoUserProfileRepository,
)
from src.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from src.infrastructure.clients.llm_client import LLMClient as InfrastructureLLMClient
    from src.application.personalization.interest_extraction_service import (
        InterestExtractionService,
    )

logger = get_logger("personalization_factory")


def create_personalized_use_cases(
    settings: Settings,
    mongo_client: AsyncIOMotorClient,
    llm_client: LLMClient,
) -> Tuple[PersonalizedReplyUseCase, ResetPersonalizationUseCase]:
    """Create personalization use cases with dependencies.

    Purpose:
        Factory function for dependency injection.
        Creates all required repositories, services, and use cases.

    Args:
        settings: Application settings.
        mongo_client: MongoDB async client.
        llm_client: LLM client for generation (must implement generate method).

    Returns:
        Tuple of (PersonalizedReplyUseCase, ResetPersonalizationUseCase).

    Example:
        >>> from motor.motor_asyncio import AsyncIOMotorClient
        >>> from src.infrastructure.clients.llm_client import get_llm_client
        >>> client = AsyncIOMotorClient("mongodb://localhost")
        >>> llm = get_llm_client()
        >>> reply_uc, reset_uc = create_personalized_use_cases(
        ...     settings, client, llm
        ... )

    Raises:
        Exception: If initialization fails.
    """
    try:
        logger.info("Creating personalization use cases...")

        # Create repositories
        profile_repo = MongoUserProfileRepository(
            mongo_client, settings.db_name
        )
        memory_repo = MongoUserMemoryRepository(
            mongo_client, settings.db_name
        )

        logger.info("Repositories created")

        # Create service
        personalization_service = PersonalizationServiceImpl(profile_repo)

        logger.info("PersonalizationService created")

        # Create interest extraction service if enabled
        interest_extraction_service: Optional["InterestExtractionService"] = None
        if settings.interest_extraction_enabled:
            try:
                from src.application.personalization.interest_extraction_service import (
                    InterestExtractionService,
                )

                interest_extraction_service = InterestExtractionService(
                    llm_client=llm_client,
                    max_topics=settings.interest_extraction_max_topics,
                )

                logger.info(
                    "InterestExtractionService created",
                    extra={"max_topics": settings.interest_extraction_max_topics},
                )
            except Exception as e:
                logger.warning(
                    "Failed to create InterestExtractionService, continuing without it",
                    extra={"error": str(e)},
                )

        # Create use cases
        personalized_reply_use_case = PersonalizedReplyUseCase(
            personalization_service=personalization_service,
            memory_repo=memory_repo,
            profile_repo=profile_repo,
            llm_client=llm_client,
            interest_extraction_service=interest_extraction_service,
        )

        reset_use_case = ResetPersonalizationUseCase(
            profile_repo=profile_repo,
            memory_repo=memory_repo,
        )

        logger.info("Personalization use cases created successfully")

        return personalized_reply_use_case, reset_use_case

    except Exception as e:
        logger.error(
            "Failed to create personalization use cases",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise

