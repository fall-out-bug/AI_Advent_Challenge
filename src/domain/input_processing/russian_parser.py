"""Russian input parsing WITHOUT LLM.

Provides regex + heuristics to extract intents and parameters
from Russian user text.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


class RussianInputParser:
    """Parse Russian user input using regex + heuristics."""

    @staticmethod
    def parse_digest_request(text: str) -> Optional[Dict[str, Any]]:
        """Parse "дайджест по ХХ за N дней" format.

        Args:
            text: e.g., "Создай дайджест по Набока за 3 дня"

        Returns:
            {"action": "digest", "channel": "onaboka", "days": 3}
            or None if not detected.
        """
        if not text:
            return None

        text_lower = text.lower()

        # Find channel: "по Набока", "по каналу Набока", "канал Набока"
        channel_match = re.search(
            r"(?:по|канал)\s+(?:каналу\s+)?([а-яa-z0-9_@]+)", text_lower
        )
        channel = channel_match.group(1) if channel_match else None

        # Find days: "3 дня", "за 7 дней"
        days_match = re.search(r"(\d+)\s*(?:дн|день|дня|дней)", text_lower)
        days = int(days_match.group(1)) if days_match else 3

        if not channel and (
            "дайджест" not in text_lower and "digest" not in text_lower
        ):
            return None

        return {
            "action": "digest",
            "channel": channel or "onaboka",
            "days": days,
        }

    @staticmethod
    def parse_list_request(text: str) -> bool:
        """Detect if this is a list-channels request."""
        if not text:
            return False
        keywords = ["список", "какие", "каналы", "подписан", "all channels"]
        return any(kw in text.lower() for kw in keywords)

    @staticmethod
    def normalize_channel_name(channel: str) -> str:
        """Normalize human channel name to username when known.

        Examples:
            "Набока" → "onaboka"
            "python" → "pythonru"
        """
        if not channel:
            return channel
        mapping = {
            "набока": "onaboka",
            "@набока": "onaboka",
            "onaboka": "onaboka",
            "python": "pythonru",
            "@python": "pythonru",
        }
        normalized = channel.strip().lower().lstrip("@")
        return mapping.get(normalized, channel.lstrip("@"))
