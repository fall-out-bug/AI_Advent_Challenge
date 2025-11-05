"""Use case for generating channel digests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.application.dtos.digest_dtos import ChannelDigest
from src.application.use_cases.generate_channel_digest_by_name import (
    GenerateChannelDigestByNameUseCase,
)
from src.domain.services.summarizer import SummarizerService
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger
from src.infrastructure.repositories.post_repository import PostRepository

logger = get_logger("use_cases.generate_channel_digest")


class GenerateChannelDigestUseCase:
    """Use case for generating channel digests.

    Purpose:
        Fetches posts for user's active channels and generates summaries.
        This is a simplified version that will be expanded later.

    Args:
        post_repository: Optional PostRepository.
        summarizer: SummarizerService for generating summaries.
        settings: Optional settings (will use get_settings if not provided).
    """

    def __init__(
        self,
        post_repository: PostRepository | None = None,
        summarizer: SummarizerService | None = None,
        settings: Any = None,
    ) -> None:
        self._post_repository = post_repository
        self._summarizer = summarizer
        self._settings = settings or get_settings()

    async def execute(
        self, user_id: int, hours: int = 24
    ) -> list[ChannelDigest]:
        """Execute channel digest generation.

        Purpose:
            Gets active channels for user and generates digests for each channel.
            Limits to max_channels from settings.

        Args:
            user_id: Telegram user ID.
            hours: Time window in hours.

        Returns:
            List of ChannelDigest objects, sorted by post count (descending).
        """
        logger.info(f"Generating channel digests for user: user_id={user_id}, hours={hours}")

        # Get active channels for user
        db = await get_db()
        channels = await db.channels.find(
            {"user_id": user_id, "active": True}
        ).to_list(length=self._settings.digest_max_channels)

        if not channels:
            logger.info(f"No active channels found: user_id={user_id}")
            return []

        # Generate digest for each channel
        digests = []
        
        # Reuse single digest-by-name use case
        digest_by_name_use_case = GenerateChannelDigestByNameUseCase(
            post_repository=self._post_repository,
            summarizer=self._summarizer,
            settings=self._settings,
        )

        for channel in channels:
            channel_username = channel.get("channel_username")
            if not channel_username:
                continue

            try:
                digest = await digest_by_name_use_case.execute(
                    user_id=user_id,
                    channel_username=channel_username,
                    hours=hours,
                )
                
                # Only include channels with posts
                if digest.post_count > 0:
                    digests.append(digest)
                    logger.debug(
                        f"Digest generated for channel: {channel_username}, posts={digest.post_count}"
                    )
            except Exception as e:
                logger.error(
                    f"Error generating digest for channel: {channel_username}, error={str(e)}",
                    exc_info=True,
                )
                # Continue with other channels

        # Sort by post count (descending)
        digests.sort(key=lambda d: d.post_count, reverse=True)

        logger.info(
            f"Channel digests generated: user_id={user_id}, channels={len(digests)}, "
            f"total_posts={sum(d.post_count for d in digests)}"
        )

        return digests
