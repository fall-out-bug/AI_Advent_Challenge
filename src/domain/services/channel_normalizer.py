"""Channel name normalization service.

Following Clean Architecture: Domain service for text normalization.
Following Python Zen: Simple is better than complex.
"""

from __future__ import annotations

import re
import string
from typing import List

from transliterate import translit


class ChannelNormalizer:
    """Service for normalizing channel names and text.

    Purpose:
        Normalizes text for channel matching by:
        - Converting to lowercase
        - Removing punctuation
        - Handling dashes/hyphens
        - Tokenizing text
        - Transliterating between Russian and Latin

    Example:
        >>> normalizer = ChannelNormalizer()
        >>> normalizer.normalize("HELLO, World!")
        'hello world'
        >>> normalizer.tokenize("Набока орёт")
        ['набока', 'орёт']
    """

    def normalize(self, text: str) -> str:
        """Normalize text for matching.

        Purpose:
            Normalizes text by converting to lowercase, removing punctuation,
            and handling dashes/hyphens.

        Args:
            text: Input text to normalize.

        Returns:
            Normalized text string.

        Example:
            >>> normalizer = ChannelNormalizer()
            >>> normalizer.normalize("Hello, World!")
            'hello world'
        """
        if not text:
            return ""

        # Convert to lowercase
        normalized = text.lower()

        # Replace all dash types with space
        normalized = re.sub(r"[-–—]", " ", normalized)

        # Remove punctuation except spaces
        normalized = re.sub(rf"[{re.escape(string.punctuation)}]", " ", normalized)

        # Remove extra spaces
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.strip()

<<<<<<< HEAD
=======
    def to_canonical_form(self, channel_username: str) -> str:
        """Convert channel username to canonical form per E.1 policy.

        Purpose:
            Ensures channel username is in canonical form: lowercase, without @ prefix.
            This is the standard format for DB, indexes, and domain logic.

        Args:
            channel_username: Channel username (may contain @ prefix, uppercase, etc.).

        Returns:
            Canonical form: lowercase, without @ prefix.
            Example: "onaboka" (not "@onaboka" or "Onaboka").

        Example:
            >>> normalizer = ChannelNormalizer()
            >>> normalizer.to_canonical_form("@onaboka")
            'onaboka'
            >>> normalizer.to_canonical_form("Onaboka")
            'onaboka'
            >>> normalizer.to_canonical_form("onaboka")
            'onaboka'
        """
        if not channel_username:
            return ""

        # Remove whitespace, then @ prefix, then convert to lowercase
        canonical = channel_username.strip().lstrip("@").lower().strip()

        return canonical

>>>>>>> origin/master
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words.

        Purpose:
            Splits text into tokens (words) after normalization.

        Args:
            text: Input text to tokenize.

        Returns:
            List of token strings.

        Example:
            >>> normalizer = ChannelNormalizer()
            >>> normalizer.tokenize("Hello, World!")
            ['hello', 'world']
        """
        normalized = self.normalize(text)
        if not normalized:
            return []

        return [token for token in normalized.split() if token]

    def transliterate_ru_to_lat(self, text: str) -> str:
        """Transliterate Russian text to Latin.

        Purpose:
            Converts Cyrillic characters to Latin equivalents.

        Args:
            text: Russian text to transliterate.

        Returns:
            Transliterated Latin text.

        Example:
            >>> normalizer = ChannelNormalizer()
            >>> normalizer.transliterate_ru_to_lat("Набока")
            'naboka'
        """
        if not text:
            return ""

        try:
            return translit(text, "ru", reversed=True)
        except Exception:
            # Fallback: return original text if transliteration fails
            return text

    def transliterate_lat_to_ru(self, text: str) -> str:
        """Transliterate Latin text to Russian.

        Purpose:
            Attempts to convert Latin text to Cyrillic (heuristic).

        Args:
            text: Latin text to transliterate.

        Returns:
            Transliterated Russian text (best effort).

        Example:
            >>> normalizer = ChannelNormalizer()
            >>> result = normalizer.transliterate_lat_to_ru("naboka")
            >>> len(result) > 0
            True
        """
        if not text:
            return ""

        try:
            return translit(text, "ru", reversed=False)
        except Exception:
            # Fallback: return original text if transliteration fails
            return text
