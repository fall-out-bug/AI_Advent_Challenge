"""Channel resolution value objects.

Following Python Zen: Simple is better than complex.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ChannelResolutionResult:
    """Result of channel name resolution.

    Purpose:
        Represents the result of resolving a user input to a channel.

    Attributes:
        found: Whether a matching channel was found
        channel_username: Resolved channel username (without @)
        channel_title: Channel title/name
        confidence_score: Confidence score from 0.0 to 1.0
        source: Source of resolution ("subscription" or "search")
        reason: Optional explanation of the match
    """

    found: bool
    channel_username: str | None
    channel_title: str | None
    confidence_score: float
    source: str  # "subscription" or "search"
    reason: str | None = None
    features_used: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate result data."""
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            raise ValueError(
                f"Confidence score must be between 0.0 and 1.0, got {self.confidence_score}"
            )

        if self.source not in ("subscription", "search"):
            raise ValueError(
                f"Source must be 'subscription' or 'search', got {self.source}"
            )

        if self.found and not self.channel_username:
            raise ValueError("channel_username must be provided when found=True")


@dataclass
class ChannelSearchResult:
    """Result of channel search in Telegram.

    Purpose:
        Represents a channel found via Telegram search.

    Attributes:
        username: Channel username (without @)
        title: Channel title/name
        description: Optional channel description
        chat_id: Telegram chat ID
    """

    username: str
    title: str
    description: str | None
    chat_id: int

    def __post_init__(self) -> None:
        """Validate search result data."""
        # Convert None to empty string for validation
        if self.username is None:
            raise ValueError("username cannot be None")
        if self.title is None:
            raise ValueError("title cannot be None")
        if not self.username or not self.username.strip():
            raise ValueError("username cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("title cannot be empty")
