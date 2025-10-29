"""Date parsing service using dateparser with locale/timezone support."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import dateparser
import pytz


class DateParser:
    """Locale-aware date parser that converts natural language to ISO-8601.

    Purpose:
        Parse free-form date strings with explicit locale and timezone.

    Args:
        tz: Default timezone (e.g., "UTC", "Europe/Moscow")
        locale: Language code (e.g., "en", "ru")
    """

    def __init__(self, tz: str = "UTC", locale: str = "en") -> None:
        self._default_tz = pytz.timezone(tz)
        self._locale = locale

    def parse_datetime(self, text: str, tz: str | None = None) -> Optional[str]:
        """Parse text to ISO-8601 datetime string.

        Args:
            text: Date string (ISO or natural language)
            tz: Override timezone (defaults to instance default)

        Returns:
            ISO-8601 string with timezone offset, or None if parsing fails
        """
        target_tz = pytz.timezone(tz) if tz else self._default_tz

        # Try ISO first
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = target_tz.localize(dt)
            return dt.isoformat()
        except (ValueError, AttributeError):
            pass

        # Use dateparser with future preference and relative base in target timezone
        now_tz = datetime.now(target_tz)
        parsed = dateparser.parse(
            text,
            languages=[self._locale],
            settings={
                "RETURN_AS_TIMEZONE_AWARE": True,
                "TIMEZONE": target_tz.zone,
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": now_tz.replace(tzinfo=None),  # naive for dateparser
            },
        )
        if parsed is None:
            return None

        # Normalize to target timezone
        if parsed.tzinfo is None:
            parsed = target_tz.localize(parsed)
        else:
            parsed = parsed.astimezone(target_tz)

        # Guardrail: if parsed ended up in the past, roll to the next day
        # This helps inputs like "at 5pm" when it's already past 5pm
        if parsed < now_tz:
            try:
                parsed = parsed + timedelta(days=1)
            except Exception:
                pass

        return parsed.isoformat()

