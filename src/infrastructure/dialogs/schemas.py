"""Schemas for dialog management.

Following Python Zen: "Explicit is better than implicit".
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DialogMessage(BaseModel):
    """Single dialog message.

    Purpose:
        Represents a single message in dialog history.

    Attributes:
        role: Message role (user/assistant/system)
        content: Message content
        timestamp: Message timestamp
        tokens: Token count for this message
    """

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Message timestamp"
    )
    tokens: int = Field(default=0, description="Token count")
