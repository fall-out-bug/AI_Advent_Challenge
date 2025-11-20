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

        Purpose:
            Calculates overlap between query and title tokens, handling:
            - Russian declensions (Алексея vs Алексей, Гладкова vs Гладков)
            - Multi-word names (partial matches)
            - Case-insensitive matching

        Args:
            query: Original query string
            title: Original title string

        Returns:
            Score contribution from token overlap.
        """
        query_tokens = set(self._normalizer.tokenize(query))
        title_tokens = set(self._normalizer.tokenize(title))
        if query_tokens and title_tokens:
            # Exact token match (case-insensitive)
            query_tokens_lower = {t.lower() for t in query_tokens}
            title_tokens_lower = {t.lower() for t in title_tokens}
            exact_overlap = len(query_tokens_lower & title_tokens_lower)

            # Substring match (for declensions like "Гладкову" vs "Гладков", "Набоки" vs "Набока")
            # Also handles "Алексея" vs "Алексей", "Гладкова" vs "Гладков"
            substring_matches = 0
            matched_query_tokens = set()

            for query_token in query_tokens:
                query_lower = query_token.lower()
                # Normalize for Russian declensions: remove common endings
                # This handles "Набоки" (множественное) vs "Набока" (единственное)
                # Also "Алексея" (родительный) vs "Алексей" (именительный)
                # Common Russian endings: ея, ия, ова, ева, ина, ына, ая, яя
                query_stem = query_lower.rstrip("еиыаяуюеяияоваеваинаына")

                for title_token in title_tokens:
                    title_lower = title_token.lower()
                    title_stem = title_lower.rstrip("еиыаяуюеяияоваеваинаына")

                    # Check multiple matching strategies
                    match_found = False

                    # 1. Exact match (case-insensitive)
                    if query_lower == title_lower:
                        match_found = True

                    # 2. Substring match (one contains the other)
                    elif query_lower in title_lower or title_lower in query_lower:
                        match_found = True

                    # 3. Stem match (after removing declension endings)
                    elif (
                        query_stem
                        and title_stem
                        and (
                            query_stem == title_stem
                            or query_stem in title_stem
                            or title_stem in query_stem
                        )
                        and len(query_stem) >= 3  # Minimum stem length
                    ):
                        match_found = True

                    # 4. Fuzzy match for similar stems (handles typos)
                    elif len(query_stem) >= 4 and len(title_stem) >= 4:
                        # Check if stems are similar (Levenshtein distance <= 1)
                        if abs(len(query_stem) - len(title_stem)) <= 1:
                            # Simple similarity check
                            common_chars = len(set(query_stem) & set(title_stem))
                            if common_chars >= min(len(query_stem), len(title_stem)) * 0.8:
                                match_found = True

                    if match_found:
                        substring_matches += 1
                        matched_query_tokens.add(query_token)
                        break

            # Calculate overlap: how many query tokens matched
            # For multi-word queries, partial matches are still valuable
            total_matches = max(exact_overlap, substring_matches)
            if total_matches > 0:
                # Overlap ratio: matched tokens / total query tokens
                overlap = total_matches / len(query_tokens)

                # Bonus for matching all tokens (perfect match)
                if total_matches == len(query_tokens) and total_matches == len(
                    title_tokens
                ):
                    overlap = 1.0  # Perfect match

                # Bonus for matching most tokens in multi-word names
                # (e.g., "Алексея Гладкова" matches "Алексей Гладков" even if declensions differ)
                elif total_matches >= len(query_tokens) * 0.7:
                    overlap = min(1.0, overlap * 1.2)  # 20% bonus

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
