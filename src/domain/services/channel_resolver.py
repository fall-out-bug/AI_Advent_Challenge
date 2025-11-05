"""Channel name resolution service.

Following Clean Architecture: Domain service with LLM integration.
Following Python Zen: Simple is better than complex.
"""

from __future__ import annotations

import json
import logging
from typing import List

from src.domain.interfaces.llm_client import LLMClientProtocol
from src.domain.services.channel_scorer import ChannelScorer
from src.domain.value_objects.channel_resolution import ChannelResolutionResult
from src.infrastructure.config.settings import get_settings
from src.infrastructure.llm.prompts.channel_matching_prompts import (
    get_channel_matching_prompt,
    get_channel_matching_prompt_ru,
)

logger = logging.getLogger(__name__)


class ChannelResolver:
    """Service for resolving channel names using scorer and optional LLM.

    Purpose:
        Resolves user input to channel by:
        1. Scoring candidates using ChannelScorer
        2. Optionally using LLM for re-ranking close matches

    Attributes:
        scorer: ChannelScorer for scoring matches
        llm_client: Optional LLM client for re-ranking
        language: Language for prompts ("ru" or "en")
    """

    def __init__(
        self,
        scorer: ChannelScorer | None = None,
        llm_client: LLMClientProtocol | None = None,
        language: str = "ru",
    ) -> None:
        """Initialize channel resolver.

        Args:
            scorer: ChannelScorer instance (creates if None)
            llm_client: Optional LLM client for re-ranking
            language: Language for prompts ("ru" or "en", default "ru")
        """
        self._scorer = scorer or ChannelScorer()
        self._llm_client = llm_client
        self._language = language
        self._settings = get_settings()

    async def resolve_from_subscriptions(
        self, user_id: int, input_name: str, channels_list: List[dict]
    ) -> ChannelResolutionResult:
        """Resolve channel name from user's subscriptions.

        Purpose:
            Score candidates using ChannelScorer, optionally re-rank with LLM.

        Args:
            user_id: Telegram user ID
            input_name: User input (channel name, title, or username)
            channels_list: List of channel dictionaries

        Returns:
            ChannelResolutionResult with match information

        Example:
            >>> channels = [{"username": "onaboka", "title": "Набока"}]
            >>> result = await resolver.resolve_from_subscriptions(
            ...     123, "Набока", channels
            ... )
            >>> result.found
            True
        """
        if not channels_list:
            logger.debug(
                f"No channels to match against: user_id={user_id}",
                extra={"user_id": user_id},
            )
            return ChannelResolutionResult(
                found=False,
                channel_username=None,
                channel_title=None,
                confidence_score=0.0,
                source="subscription",
                reason="No subscribed channels available",
            )

        # Score all candidates
        scored_candidates = []
        for ch in channels_list:
            score = self._scorer.score(input_name, ch)
            scored_candidates.append((score, ch))

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Get threshold from settings
        threshold = self._settings.channel_resolution_threshold

        # Check if top candidate meets threshold
        if scored_candidates and scored_candidates[0][0] >= threshold:
            top_score, top_channel = scored_candidates[0]

            # Check if LLM re-ranking is needed (score in 0.6-0.8 range)
            needs_rerank = (
                self._settings.enable_llm_rerank
                and self._llm_client
                and 0.6 <= top_score <= 0.8
                and len(scored_candidates) > 1
            )

            if needs_rerank:
                result = await self._rerank_with_llm(
                    user_id, input_name, scored_candidates[:3]
                )
                if result.found:
                    return result

            # Use top scorer result
            username = top_channel.get("username") or top_channel.get(
                "channel_username"
            )
            return ChannelResolutionResult(
                found=True,
                channel_username=username,
                channel_title=top_channel.get("title"),
                confidence_score=top_score,
                source="subscription",
                reason=f"Matched with score {top_score:.2f}",
                features_used={"scorer": top_score},
            )

        # No match found
        top_scores = (
            [
                (ch.get("channel_username", "unknown"), score)
                for score, ch in scored_candidates[:3]
            ]
            if scored_candidates
            else []
        )
        logger.info(
            f"Channel resolution: no match found above threshold {threshold}",
            extra={
                "user_id": user_id,
                "query": input_name,
                "top_score": scored_candidates[0][0] if scored_candidates else 0.0,
                "top_candidates": top_scores,
            },
        )
        return ChannelResolutionResult(
            found=False,
            channel_username=None,
            channel_title=None,
            confidence_score=scored_candidates[0][0] if scored_candidates else 0.0,
            source="subscription",
            reason="No match found with sufficient confidence",
        )

    async def _rerank_with_llm(
        self,
        user_id: int,
        input_name: str,
        top_candidates: List[tuple[float, dict]],
    ) -> ChannelResolutionResult:
        """Re-rank close matches using LLM.

        Purpose:
            Use LLM to choose best match from top candidates.

        Args:
            user_id: Telegram user ID
            input_name: User query
            top_candidates: List of (score, channel) tuples

        Returns:
            ChannelResolutionResult with LLM-selected match
        """
        if not self._llm_client:
            return ChannelResolutionResult(
                found=False,
                channel_username=None,
                channel_title=None,
                confidence_score=0.0,
                source="subscription",
                reason="LLM client not available",
            )

        channels_list = [ch for _, ch in top_candidates]

        if self._language == "ru":
            prompt = get_channel_matching_prompt_ru(input_name, channels_list)
        else:
            prompt = get_channel_matching_prompt(input_name, channels_list)

        try:
            response = await self._llm_client.generate(
                prompt=prompt, temperature=0.2, max_tokens=256
            )

            result = self._parse_llm_response(response, input_name)

            logger.info(
                f"LLM re-ranking result: user_id={user_id}, input={input_name}, "
                f"found={result.found}, username={result.channel_username}",
                extra={
                    "user_id": user_id,
                    "query": input_name,
                    "found": result.found,
                    "username": result.channel_username,
                },
            )

            return result

        except Exception as e:
            logger.warning(
                f"LLM re-ranking failed: {e}",
                extra={"user_id": user_id, "query": input_name},
            )
            # Fall back to scorer result
            top_score, top_channel = top_candidates[0]
            return ChannelResolutionResult(
                found=True,
                channel_username=top_channel.get("username")
                or top_channel.get("channel_username"),
                channel_title=top_channel.get("title"),
                confidence_score=top_score,
                source="subscription",
                reason=f"Matched with score {top_score:.2f} (LLM rerank failed)",
                features_used={"scorer": top_score},
            )

    def _parse_llm_response(
        self, response: str, input_name: str
    ) -> ChannelResolutionResult:
        """Parse LLM JSON response into ChannelResolutionResult.

        Purpose:
            Extract JSON from LLM response and validate it.

        Args:
            response: LLM response text
            input_name: Original user input

        Returns:
            ChannelResolutionResult
        """
        response_clean = response.strip()

        # Remove markdown code blocks
        if response_clean.startswith("```"):
            first_newline = response_clean.find("\n")
            if first_newline > 0:
                response_clean = response_clean[first_newline:].strip()
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3].strip()

        # Find JSON object
        json_start = response_clean.find("{")
        json_end = response_clean.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            response_clean = response_clean[json_start:json_end]

        try:
            data = json.loads(response_clean)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse LLM response as JSON: {response[:200]}, error={e}"
            )
            return ChannelResolutionResult(
                found=False,
                channel_username=None,
                channel_title=None,
                confidence_score=0.0,
                source="subscription",
                reason="Invalid JSON response from LLM",
            )

        matched = data.get("matched", False)
        channel_username = data.get("channel_username")
        confidence = float(data.get("confidence", 0.0))
        reason = data.get("reason", "")

        confidence = max(0.0, min(1.0, confidence))

        if matched and channel_username and confidence >= 0.5:
            return ChannelResolutionResult(
                found=True,
                channel_username=channel_username,
                channel_title=None,
                confidence_score=confidence,
                source="subscription",
                reason=reason,
                features_used={"llm_rerank": confidence},
            )
        else:
            return ChannelResolutionResult(
                found=False,
                channel_username=None,
                channel_title=None,
                confidence_score=confidence,
                source="subscription",
                reason=reason or "No match found with sufficient confidence",
            )
