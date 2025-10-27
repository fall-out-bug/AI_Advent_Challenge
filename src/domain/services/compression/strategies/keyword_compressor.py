"""Keywords compression strategy.

Following the Zen of Python:
- Simple is better than complex
- Beautiful is better than ugly
"""

from typing import List

from src.domain.services.compression.strategies.base_compressor import BaseCompressor


class KeywordCompressor(BaseCompressor):
    """
    Keywords compression strategy.

    Extracts words longer than 4 characters and keeps
    first N keywords to fit within token limit.
    """

    def _perform_compression(self, text: str, max_tokens: int) -> str:
        """
        Perform keywords compression.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens

        Returns:
            Compressed text with keywords only
        """
        keywords = self._extract_keywords(text)
        max_words = self._calculate_word_budget(max_tokens)
        selected = self._select_top_keywords(keywords, max_words)

        return self._join_keywords(selected)

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.

        Keywords are words longer than 4 characters and alphabetic.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        words = text.split()
        return [word for word in words if len(word) > 4 and word.isalpha()]

    def _calculate_word_budget(self, max_tokens: int) -> int:
        """
        Calculate maximum words allowed.

        Args:
            max_tokens: Maximum tokens

        Returns:
            Maximum words allowed (approximate 1.3 tokens per word)
        """
        return int(max_tokens / 1.3)

    def _select_top_keywords(self, keywords: List[str], max_words: int) -> List[str]:
        """
        Select top keywords up to max_words limit.

        Args:
            keywords: List of keywords
            max_words: Maximum word count

        Returns:
            Selected keywords
        """
        return keywords[:max_words]

    def _join_keywords(self, keywords: List[str]) -> str:
        """
        Join keywords into compressed text.

        Args:
            keywords: List of keywords

        Returns:
            Joined keywords as single string
        """
        return " ".join(keywords)

    def _get_strategy_name(self) -> str:
        """Get strategy name."""
        return "keywords"
