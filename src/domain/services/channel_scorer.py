"""Channel matching score calculation service.

Following Clean Architecture: Domain service for scoring channel matches.
Following Python Zen: Simple is better than complex.
"""

from __future__ import annotations

import logging
from typing import Dict

from rapidfuzz import fuzz

from src.domain.services.channel_normalizer import ChannelNormalizer
from src.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


class ChannelScorer:
    """Service for scoring channel matches.

    Purpose:
        Calculates similarity scores between user queries and channel metadata
        using multiple features (exact match, prefix, token overlap, Levenshtein).

    Attributes:
        normalizer: ChannelNormalizer for text normalization
        weights: Dictionary of feature weights for scoring
    """

    def __init__(
        self,
        normalizer: ChannelNormalizer | None = None,
        weights: Dict[str, float] | None = None,
    ) -> None:
        """Initialize channel scorer.

        Args:
            normalizer: ChannelNormalizer instance (creates if None)
            weights: Feature weights dict (uses settings if None)
        """
        self._normalizer = normalizer or ChannelNormalizer()
        self._weights = weights or self._get_default_weights()

    def _get_default_weights(self) -> Dict[str, float]:
        """Get default weights from settings.

        Returns:
            Dictionary of feature weights.
        """
        settings = get_settings()
        return {
            "exact_username": settings.channel_resolution_exact_username_weight,
            "exact_title": settings.channel_resolution_exact_title_weight,
            "prefix_username": settings.channel_resolution_prefix_username_weight,
            "prefix_title": settings.channel_resolution_prefix_title_weight,
            "token_overlap": settings.channel_resolution_token_overlap_weight,
            "levenshtein_username": (
                settings.channel_resolution_levenshtein_username_weight
            ),
            "levenshtein_title": (settings.channel_resolution_levenshtein_title_weight),
            "description_mention": (
                settings.channel_resolution_description_mention_weight
            ),
        }

    def score(self, query: str, channel: Dict[str, str]) -> float:
        """Calculate match score between query and channel.

        Purpose:
            Computes weighted similarity score using multiple features.

        Args:
            query: User query string
            channel: Channel dict with username, title, description

        Returns:
            Score between 0.0 and 1.0 (higher = better match)

        Example:
            >>> scorer = ChannelScorer()
            >>> channel = {"username": "onaboka", "title": "Набока", "description": ""}
            >>> score = scorer.score("Набока", channel)
            >>> score > 0.5
            True
        """
        if not query or not channel:
            return 0.0

        username = channel.get("username", "").lower()
        title = channel.get("title", "").lower()
        description = channel.get("description", "").lower()

        query_norm = self._normalizer.normalize(query)
        username_norm = self._normalizer.normalize(username)
        title_norm = self._normalizer.normalize(title)

        total_score = self._score_exact_matches(query_norm, username_norm, title_norm)
        total_score += self._score_prefix_matches(query_norm, username_norm, title_norm)
        total_score += self._score_token_overlap(query, title)
        # Also check token overlap with description
        if description:
            desc_token_score = self._score_token_overlap(query, description)
            total_score += desc_token_score * 0.5  # Lower weight for description
        total_score += self._score_levenshtein(query_norm, username_norm, title_norm)
        total_score += self._score_description_mention(query_norm, description)

        final_score = min(1.0, max(0.0, total_score))

        logger.debug(
            f"Channel score: query='{query}', username='{username}', "
            f"title='{title}', score={final_score:.3f}, "
            f"exact={self._score_exact_matches(query_norm, username_norm, title_norm):.3f}, "
            f"prefix={self._score_prefix_matches(query_norm, username_norm, title_norm):.3f}, "
            f"token_overlap={self._score_token_overlap(query, title):.3f}, "
            f"levenshtein={self._score_levenshtein(query_norm, username_norm, title_norm):.3f}, "
            f"description={self._score_description_mention(query_norm, description):.3f}"
        )

        return final_score

    def _score_exact_matches(
        self, query_norm: str, username_norm: str, title_norm: str
    ) -> float:
        """Score exact matches.

        Args:
            query_norm: Normalized query
            username_norm: Normalized username
            title_norm: Normalized title

        Returns:
            Score contribution from exact matches.
        """
        score = 0.0
        if query_norm == username_norm:
            score += self._weights["exact_username"]
        if query_norm == title_norm:
            score += self._weights["exact_title"]
        return score

    def _score_prefix_matches(
        self, query_norm: str, username_norm: str, title_norm: str
    ) -> float:
        """Score prefix matches.

        Args:
            query_norm: Normalized query
            username_norm: Normalized username
            title_norm: Normalized title

        Returns:
            Score contribution from prefix matches.
        """
        score = 0.0
        if username_norm.startswith(query_norm):
            score += self._weights["prefix_username"]
        if title_norm.startswith(query_norm):
            score += self._weights["prefix_title"]
        return score

    def _score_token_overlap(self, query: str, title: str) -> float:
        """Score token overlap.

        Args:
            query: Original query string
            title: Original title string

        Returns:
            Score contribution from token overlap.
        """
        query_tokens = set(self._normalizer.tokenize(query))
        title_tokens = set(self._normalizer.tokenize(title))
        if query_tokens and title_tokens:
            # Exact token match
            exact_overlap = len(query_tokens & title_tokens)

            # Substring match (for declensions like "Гладкову" vs "Гладков", "Набоки" vs "Набока")
            # Check if any query token is contained in any title token
            substring_matches = 0
            for query_token in query_tokens:
                for title_token in title_tokens:
                    # Normalize for Russian declensions: remove common endings
                    # This handles "Набоки" (множественное) vs "Набока" (единственное)
                    query_stem = query_token.rstrip("еиыаяую")
                    title_stem = title_token.rstrip("еиыаяую")

                    # Check if query token contains title token or vice versa
                    # (handles Russian declensions)
                    if (
                        query_token in title_token
                        or title_token in query_token
                        or query_stem in title_stem
                        or title_stem in query_stem
                        or (len(query_stem) >= 4 and query_stem == title_stem)
                        or (len(title_stem) >= 4 and title_stem == query_stem)
                    ):
                        substring_matches += 1
                        break

            # Use best match (exact or substring)
            total_matches = max(exact_overlap, substring_matches)
            overlap = total_matches / len(query_tokens)
            return self._weights["token_overlap"] * overlap
        return 0.0

    def _score_levenshtein(
        self, query_norm: str, username_norm: str, title_norm: str
    ) -> float:
        """Score Levenshtein similarity.

        Args:
            query_norm: Normalized query
            username_norm: Normalized username
            title_norm: Normalized title

        Returns:
            Score contribution from Levenshtein distance.
        """
        score = 0.0
        if username_norm:
            ratio_username = fuzz.ratio(query_norm, username_norm) / 100.0
            score += self._weights["levenshtein_username"] * ratio_username
        if title_norm:
            ratio_title = fuzz.ratio(query_norm, title_norm) / 100.0
            score += self._weights["levenshtein_title"] * ratio_title
        return score

    def _score_description_mention(self, query_norm: str, description: str) -> float:
        """Score description mention.

        Args:
            query_norm: Normalized query
            description: Channel description

        Returns:
            Score contribution from description mention.
        """
        if not description:
            return 0.0

        desc_lower = description.lower()
        query_lower = query_norm.lower()

        # Exact match
        if query_lower in desc_lower:
            return self._weights["description_mention"]

        # Check if all query tokens are in description (for multi-word queries)
        query_tokens = set(query_lower.split())
        desc_tokens = set(self._normalizer.tokenize(description))
        if query_tokens and desc_tokens:
            # Count how many query tokens are found in description
            found_tokens = len(query_tokens & desc_tokens)
            if found_tokens > 0:
                # Partial score based on ratio of found tokens
                ratio = found_tokens / len(query_tokens)
                return (
                    self._weights["description_mention"] * ratio * 0.5
                )  # Lower weight for partial

        return 0.0
