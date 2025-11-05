"""Use case for resolving channel names.

Following Clean Architecture: Application layer orchestrates domain services.
"""

from __future__ import annotations

from typing import List

from src.domain.services.channel_resolver import ChannelResolver
from src.domain.value_objects.channel_resolution import (
    ChannelResolutionResult,
    ChannelSearchResult,
)
from src.infrastructure.clients.telegram_utils import search_channels_by_name
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger

logger = get_logger("use_cases.resolve_channel_name")


class ResolveChannelNameUseCase:
    """Use case for resolving channel names.

    Purpose:
        Resolves user input to a channel by:
        1. Matching against subscribed channels using LLM
        2. Searching Telegram if not found (optional)

    Attributes:
        channel_resolver: ChannelResolver service for LLM matching
        allow_telegram_search: Whether to search Telegram if not found in subscriptions
    """

    def __init__(
        self,
        channel_resolver: ChannelResolver | None = None,
        allow_telegram_search: bool = True,
    ) -> None:
        """Initialize resolve channel name use case.

        Args:
            channel_resolver: ChannelResolver service (will create if None)
            allow_telegram_search: Whether to search Telegram if not found
        """
        self._channel_resolver = channel_resolver
        self._allow_telegram_search = allow_telegram_search

    async def execute(
        self,
        user_id: int,
        input_name: str,
        allow_telegram_search: bool | None = None,
    ) -> ChannelResolutionResult:
        """Execute channel name resolution.

        Purpose:
            Resolve user input to a channel by matching against subscriptions
            and optionally searching Telegram.

        Args:
            user_id: Telegram user ID
            input_name: User input (channel name, title, or username)
            allow_telegram_search: Override default allow_telegram_search setting

        Returns:
            ChannelResolutionResult with resolution information

        Example:
            >>> use_case = ResolveChannelNameUseCase()
            >>> result = await use_case.execute(123, "Набока")
            >>> if result.found:
            ...     print(f"Found: @{result.channel_username}")
        """
        allow_search = (
            allow_telegram_search
            if allow_telegram_search is not None
            else self._allow_telegram_search
        )

        # Get user's subscribed channels
        db = await get_db()
        channels_cursor = db.channels.find({"user_id": user_id, "active": True})
        channels_list = await channels_cursor.to_list(length=100)

        if not channels_list:
            logger.info(f"No subscribed channels for user: user_id={user_id}")
            # If no subscriptions and search allowed, go directly to search
            if allow_search:
                return await self._search_in_telegram(input_name)
            return ChannelResolutionResult(
                found=False,
                channel_username=None,
                channel_title=None,
                confidence_score=0.0,
                source="subscription",
                reason="No subscribed channels available",
            )

        # Enrich channels with fresh metadata from Telegram API if missing
        # This ensures we have real title and description from Telegram parsing
        from src.presentation.mcp.tools.channels.channel_metadata import (
            get_channel_metadata,
        )

        for ch in channels_list:
            channel_username = ch.get("channel_username")
            current_title = ch.get("title")
            current_description = ch.get("description")

            # If title or description is missing, fetch from Telegram API
            if not current_title or not current_description:
                try:
                    logger.debug(
                        f"Enriching channel metadata for resolution: "
                        f"channel={channel_username}, has_title={bool(current_title)}, "
                        f"has_description={bool(current_description)}"
                    )
                    metadata = await get_channel_metadata(
                        channel_username, user_id=user_id
                    )
                    if metadata.get("success"):
                        # Update channel document in memory
                        if not current_title and metadata.get("title"):
                            ch["title"] = metadata.get("title")
                        if not current_description and metadata.get("description"):
                            ch["description"] = metadata.get("description")
                except Exception as e:
                    logger.debug(
                        f"Failed to enrich metadata for {channel_username}: {e}"
                    )

        # Format channels for resolver
        channels_for_resolver = []
        for ch in channels_list:
            channels_for_resolver.append(
                {
                    "channel_username": ch.get("channel_username", ""),
                    "username": ch.get(
                        "channel_username", ""
                    ),  # Alias for compatibility
                    "title": ch.get("title", ""),
                    "description": ch.get(
                        "description", ""
                    ),  # Include description for better matching
                }
            )

        # Resolve using scorer + optional LLM
        resolver = self._channel_resolver
        if resolver is None:
            # Create resolver with scorer and optional LLM client
            from src.infrastructure.di.container import SummarizationContainer

            container = SummarizationContainer()
            llm_client_wrapper = container.llm_client()
            from src.domain.services.channel_scorer import ChannelScorer

            scorer = ChannelScorer()
            resolver = ChannelResolver(
                scorer=scorer, llm_client=llm_client_wrapper, language="ru"
            )

        result = await resolver.resolve_from_subscriptions(
            user_id=user_id,
            input_name=input_name,
            channels_list=channels_for_resolver,
        )

        # If found, enrich with title and description from enriched channels_list
        if result.found and result.channel_username:
            # Find title and description from channels_list
            for ch in channels_list:
                if ch.get("channel_username") == result.channel_username:
                    result.channel_title = ch.get("title")
                    # Note: description is not in ChannelResolutionResult, but we ensure it's in DB
                    break

        # If not found and search allowed, try Telegram search
        if not result.found and allow_search:
            logger.info(
                f"Channel not found in subscriptions, searching Telegram: "
                f"user_id={user_id}, input={input_name}"
            )
            search_result = await self._search_in_telegram(input_name)
            return search_result

        return result

    async def _search_in_telegram(self, input_name: str) -> ChannelResolutionResult:
        """Search for channel in Telegram using Pyrogram.

        Purpose:
            Search user's dialogs for matching channels, or try direct resolve.

        Args:
            input_name: Search query

        Returns:
            ChannelResolutionResult with search result (top-1 match)
        """
        try:
            # First, try searching in dialogs
            search_results = await search_channels_by_name(input_name, limit=1)

            # Filter out results without username or title
            valid_results = []
            for result in search_results:
                username = result.get("username", "").strip()
                title = result.get("title", "").strip()
                if username and title:
                    valid_results.append(result)

            if valid_results:
                top_result = valid_results[0]
                logger.info(
                    f"Found channel in Telegram search: input={input_name}, "
                    f"username={top_result['username']}, title={top_result['title']}"
                )

                return ChannelResolutionResult(
                    found=True,
                    channel_username=top_result["username"],
                    channel_title=top_result["title"],
                    confidence_score=0.8,  # Medium confidence for search results
                    source="search",
                    reason=f"Found in Telegram search: {top_result['title']}",
                )

            # If search in dialogs didn't work, try direct resolve via get_channel_metadata
            # This works if we can guess the username from the input
            logger.debug(
                f"No channels found in dialogs search, trying direct resolve: input={input_name}"
            )
            from src.presentation.mcp.tools.channels.channel_metadata import (
                get_channel_metadata,
            )

            # Try to resolve directly (only if input looks like a username)
            # For now, skip this - search_channels_by_name should handle it
            # But we can add fallback logic here if needed

            logger.info(f"No channels found in Telegram search: input={input_name}")
            return ChannelResolutionResult(
                found=False,
                channel_username=None,
                channel_title=None,
                confidence_score=0.0,
                source="search",
                reason="No matching channels found in Telegram",
            )

        except Exception as e:
            logger.error(
                f"Error searching Telegram for channel: input={input_name}, error={e}",
                exc_info=True,
            )
            return ChannelResolutionResult(
                found=False,
                channel_username=None,
                channel_title=None,
                confidence_score=0.0,
                source="search",
                reason=f"Error during Telegram search: {str(e)}",
            )
