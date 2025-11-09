from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskSummary(BaseModel):
    """Aggregated task summary stats for a timeframe.

    Purpose:
        Represents counts used in brief user-facing summaries.

    Args:
        total: Total tasks
        completed: Completed tasks
        overdue: Overdue (incomplete and past deadline)
        high_priority: High priority tasks
        timeframe: Optional label for the period
    """

    total: int = Field(ge=0)
    completed: int = Field(ge=0)
    overdue: int = Field(ge=0)
    high_priority: int = Field(ge=0)
    timeframe: Optional[str] = None

    @field_validator("completed", "overdue", "high_priority")
    @classmethod
    def not_exceed_total(cls, v: int, info):  # type: ignore[override]
        # This validator does not know total; cross-field checks can be added in model_validate
        return v

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        if self.completed > self.total:
            raise ValueError("completed cannot exceed total")
        if self.overdue > self.total:
            raise ValueError("overdue cannot exceed total")
        if self.high_priority > self.total:
            raise ValueError("high_priority cannot exceed total")


class DigestItem(BaseModel):
    """Represents a single channel digest item."""

    channel: str
    summary: str
    post_count: int = Field(ge=0)
    tags: List[str] = Field(default_factory=list)


class DigestMessage(BaseModel):
    """Digest result containing multiple channel summaries."""

    items: List[DigestItem] = Field(default_factory=list)
    generated_at_iso: Optional[str] = None
