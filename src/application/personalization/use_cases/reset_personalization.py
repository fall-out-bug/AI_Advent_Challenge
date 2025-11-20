"""Reset personalization use case."""

from src.application.personalization.dtos import (
    ResetPersonalizationInput,
    ResetPersonalizationOutput,
)
from src.domain.interfaces.personalization import (
    UserMemoryRepository,
    UserProfileRepository,
)
from src.infrastructure.logging import get_logger

logger = get_logger("reset_personalization_use_case")


class ResetPersonalizationUseCase:
    """Use case for resetting user personalization.

    Purpose:
        Reset user profile to defaults and delete all memory events.
        Used for "start fresh" functionality.

    Attributes:
        profile_repo: Repository for user profiles.
        memory_repo: Repository for user memory.

    Example:
        >>> use_case = ResetPersonalizationUseCase(profile_repo, memory_repo)
        >>> input_data = ResetPersonalizationInput(user_id="123")
        >>> output = await use_case.execute(input_data)
    """

    def __init__(
        self,
        profile_repo: UserProfileRepository,
        memory_repo: UserMemoryRepository,
    ) -> None:
        """Initialize use case with repositories.

        Args:
            profile_repo: Repository for user profiles.
            memory_repo: Repository for user memory.
        """
        self.profile_repo = profile_repo
        self.memory_repo = memory_repo
        logger.info("ResetPersonalizationUseCase initialized")

    async def execute(
        self, input_data: ResetPersonalizationInput
    ) -> ResetPersonalizationOutput:
        """Execute personalization reset.

        Purpose:
            Reset profile and delete memory for user.

        Args:
            input_data: Input DTO with user_id.

        Returns:
            ResetPersonalizationOutput with success status.

        Example:
            >>> input_data = ResetPersonalizationInput(user_id="123")
            >>> output = await use_case.execute(input_data)
            >>> output.success
            True
        """
        try:
            # Count events before deletion
            event_count = await self.memory_repo.count_events(input_data.user_id)

            # Reset profile (delete and recreate with defaults)
            await self.profile_repo.reset(input_data.user_id)

            # Delete all memory events (via compression with keep_last_n=0)
            await self.memory_repo.compress(input_data.user_id, "", keep_last_n=0)

            logger.info(
                "Personalization reset successfully",
                extra={
                    "user_id": input_data.user_id,
                    "memory_deleted_count": event_count,
                },
            )

            return ResetPersonalizationOutput(
                success=True,
                profile_reset=True,
                memory_deleted_count=event_count,
            )

        except Exception as e:
            logger.error(
                "Failed to reset personalization",
                extra={"user_id": input_data.user_id, "error": str(e)},
                exc_info=True,
            )

            return ResetPersonalizationOutput(
                success=False,
                profile_reset=False,
                memory_deleted_count=0,
            )
