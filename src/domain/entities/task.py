"""Task domain models with validation (Pydantic)."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TaskIn(BaseModel):
    """Input model for creating a task.

    Args:
        user_id: Telegram user ID
        title: Task title (max 256 chars)
        description: Optional description
        deadline: Optional ISO datetime string
        priority: low | medium | high
        tags: list of strings

    Example:
        TaskIn(user_id=1, title="Buy milk", priority="low")
    """

    user_id: int
    title: str = Field(min_length=1, max_length=256)
    description: str = ""
    deadline: Optional[str] = None
    priority: str = Field(default="medium")
    tags: List[str] = Field(default_factory=list)

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, v: str) -> str:
        allowed = {"low", "medium", "high"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return v


class TaskUpdate(BaseModel):
    """Update model for tasks.

    Args:
        title, description, deadline, priority, tags, completed

    Example:
        TaskUpdate(completed=True)
    """

    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    completed: Optional[bool] = None

    @field_validator("priority")
    @classmethod
    def _validate_priority_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"low", "medium", "high"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return v


