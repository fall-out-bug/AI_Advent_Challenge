"""Truncation compression strategy.

Following the Zen of Python:
- Simple is better than complex
- Beautiful is better than ugly
"""

import re
from typing import List

from src.domain.services.compression.strategies.base_compressor import BaseCompressor


class TruncationCompressor(BaseCompressor):
    """
    Truncation compression strategy.

    Keeps first sentence, middle portion, and last sentence
    to preserve context while reducing token count.
    """

    def _perform_compression(self, text: str, max_tokens: int) -> str:
        """
        Perform truncation compression.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens

        Returns:
            Compressed text
        """
        sentences = self._split_sentences(text)
        max_words = self._calculate_word_budget(max_tokens)

        if len(sentences) <= 2:
            return self._truncate_by_words(text, max_words)

        return self._truncate_by_sentences(sentences, max_words)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _calculate_word_budget(self, max_tokens: int) -> int:
        """
        Calculate maximum words allowed.

        Args:
            max_tokens: Maximum tokens

        Returns:
            Maximum words allowed (approximate 1.3 tokens per word)
        """
        return int(max_tokens / 1.3)

    def _truncate_by_words(self, text: str, max_words: int) -> str:
        """
        Truncate text by word count.

        Args:
            text: Text to truncate
            max_words: Maximum word count

        Returns:
            Truncated text
        """
        words = text.split()

        if len(words) <= max_words:
            return text

        return " ".join(words[:max_words]) + "..."

    def _truncate_by_sentences(self, sentences: List[str], max_words: int) -> str:
        """
        Truncate text by keeping first, middle, and last sentences.

        Args:
            sentences: List of sentences
            max_words: Maximum word count

        Returns:
            Compressed text
        """
        first_sentence = sentences[0]
        last_sentence = sentences[-1]

        # Calculate words for middle portion
        first_words = len(first_sentence.split())
        last_words = len(last_sentence.split())
        middle_words = max_words - first_words - last_words - 10

        if middle_words > 0:
            return self._build_with_middle(
                first_sentence, last_sentence, sentences[1:-1], middle_words
            )

        return f"{first_sentence}... {last_sentence}"

    def _build_with_middle(
        self, first: str, last: str, middle_sentences: List[str], middle_words: int
    ) -> str:
        """
        Build compressed text with middle portion.

        Args:
            first: First sentence
            last: Last sentence
            middle_sentences: Middle sentences
            middle_words: Maximum words for middle

        Returns:
            Compressed text with middle portion
        """
        middle_text = " ".join(middle_sentences)
        middle_words_list = middle_text.split()[:middle_words]
        middle_part = " ".join(middle_words_list)

        return f"{first}... {middle_part}... {last}"

    def _get_strategy_name(self) -> str:
        """Get strategy name."""
        return "truncation"
