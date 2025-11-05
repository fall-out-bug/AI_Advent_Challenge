"""Value objects for post content."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PostContent:
    """Content of a single post.

    Purpose:
        Represents a post with its text and metadata
        for use in summarization.

    Args:
        text: Post text content.
        date: Post publication date (optional).
        message_id: Post message ID (optional).
        channel_username: Channel username (optional).
    """

    text: str
    date: datetime | None = None
    message_id: int | None = None
    channel_username: str | None = None

    def __post_init__(self) -> None:
        """Validate post content."""
        if not self.text or not self.text.strip():
            raise ValueError("Post text cannot be empty")
