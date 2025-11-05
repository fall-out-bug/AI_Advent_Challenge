"""Use case for searching channels for subscription.

Following Clean Architecture: Application layer orchestrates domain services.
"""

from __future__ import annotations

from typing import List

from src.domain.services.channel_resolver import ChannelResolver
from src.domain.services.channel_scorer import ChannelScorer
from src.domain.value_objects.channel_resolution import ChannelSearchResult
from src.infrastructure.clients.telegram_utils import search_channels_by_name
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger

logger = get_logger("use_cases.search_channel_for_subscription")


class SearchChannelForSubscriptionUseCase:
    """Use case for searching channels for subscription.

    Purpose:
        Searches Telegram for channels matching user query and returns top-N
        candidates ranked by similarity score.

    Attributes:
        scorer: ChannelScorer for ranking candidates
        resolver: Optional ChannelResolver for LLM re-ranking
    """

    def __init__(
        self,
        scorer: ChannelScorer | None = None,
        resolver: ChannelResolver | None = None,
    ) -> None:
        """Initialize search channel for subscription use case.

        Args:
            scorer: ChannelScorer instance (creates if None)
            resolver: Optional ChannelResolver for LLM re-ranking
        """
        self._scorer = scorer or ChannelScorer()
        self._resolver = resolver
        self._settings = get_settings()

    async def execute(
        self,
        user_id: int,
        query: str,
    ) -> List[ChannelSearchResult]:
        """Execute channel search for subscription.

        Purpose:
            Search Telegram for channels and return top-N candidates ranked by score.

        Args:
            user_id: Telegram user ID
            query: User search query

        Returns:
            List of ChannelSearchResult candidates (sorted by score, descending)

        Example:
            >>> use_case = SearchChannelForSubscriptionUseCase()
            >>> results = await use_case.execute(123, "крупнокалиберный")
            >>> len(results) > 0
            True
            >>> results[0].username
            'bolshiepushki'
        """
        max_candidates = self._settings.channel_discovery_max_candidates

        # Search Telegram
        limit = max_candidates * 2
        search_results = await search_channels_by_name(query, limit=limit)

        logger.debug(
            f"Raw search results from Telegram: query='{query}', "
            f"count={len(search_results)}, results={search_results[:3] if search_results else []}",
            extra={"user_id": user_id, "query": query},
        )

        if not search_results:
            logger.info(
                f"No channels found in Telegram search: "
                f"user_id={user_id}, query={query}",
                extra={"user_id": user_id, "query": query},
            )
            return []

        # Filter out channels without username (can't subscribe to private channels/groups)
        valid_results = []
        for ch in search_results:
            username = ch.get("username", "").strip()
            title = ch.get("title", "").strip()
            if not username:
                logger.debug(
                    f"Skipping channel without username: title='{title}', query='{query}'",
                    extra={"user_id": user_id, "query": query},
                )
                continue
            if not title:
                logger.debug(
                    f"Skipping channel without title: username='{username}', query='{query}'",
                    extra={"user_id": user_id, "query": query},
                )
                continue
            valid_results.append(ch)

        if not valid_results:
            logger.info(
                f"No valid channels found (all missing username or title): "
                f"user_id={user_id}, query={query}, total_results={len(search_results)}",
                extra={"user_id": user_id, "query": query},
            )
            return []

        logger.debug(
            f"Filtered search results: total={len(search_results)}, "
            f"valid={len(valid_results)}, query='{query}'"
        )

        # Score all candidates
        scored_candidates = []
        for ch in valid_results:
            score = self._scorer.score(query, ch)
            scored_candidates.append((score, ch))

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Take top-N
        top_candidates = scored_candidates[:max_candidates]

        # Convert to ChannelSearchResult
        # Filter out invalid results (must have username and title)
        results = []
        for score, ch in top_candidates:
            # Get values with fallback to empty string, handle None
            username_raw = ch.get("username")
            title_raw = ch.get("title")
            username = (username_raw if username_raw else "").strip()
            title = (title_raw if title_raw else "").strip()

            # Skip if username or title is empty
            if not username or not title:
                logger.warning(
                    f"Skipping invalid search result: username='{username}', "
                    f"title='{title}', query='{query}', raw_username={username_raw}, "
                    f"raw_title={title_raw}, score={score:.2f}",
                    extra={"user_id": user_id, "query": query},
                )
                continue

            description_raw = ch.get("description")
            description = description_raw if description_raw else None
            chat_id = ch.get("chat_id", 0)

            # Create ChannelSearchResult with validation
            try:
                result = ChannelSearchResult(
                    username=username,
                    title=title,
                    description=description,
                    chat_id=chat_id,
                )
                results.append(result)
                logger.debug(
                    f"Added valid search result: username='{username}', "
                    f"title='{title}', score={score:.2f}, query='{query}'"
                )
            except ValueError as e:
                logger.warning(
                    f"Failed to create ChannelSearchResult: username='{username}', "
                    f"title='{title}', error={e}, query='{query}'",
                    extra={"user_id": user_id, "query": query},
                )
                continue

        # Final check: if no valid results after filtering, return empty list
        if not results:
            logger.warning(
                f"No valid results after filtering: user_id={user_id}, query='{query}', "
                f"top_candidates_count={len(top_candidates)}, "
                f"valid_results_before_scoring={len(valid_results)}",
                extra={
                    "user_id": user_id,
                    "query": query,
                    "top_candidates_count": len(top_candidates),
                    "valid_results_before_scoring": len(valid_results),
                },
            )
            return []

        logger.info(
            f"Channel search completed: user_id={user_id}, query={query}, "
            f"results_count={len(results)}, "
            f"top_score={top_candidates[0][0] if top_candidates else 0.0:.2f}",
            extra={
                "user_id": user_id,
                "query": query,
                "results_count": len(results),
                "top_score": top_candidates[0][0] if top_candidates else 0.0,
            },
        )

        return results
