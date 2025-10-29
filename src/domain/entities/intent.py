"""Intent parsing domain models."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ClarificationQuestion(BaseModel):
    """Clarification prompt for the user.

    Args:
        text: Question to ask the user
        key: Field this question clarifies (e.g., "deadline")
    """

    text: str = Field(min_length=1)
    key: str = Field(min_length=1)


class IntentParseResult(BaseModel):
    """Parsed intent for task creation.

    Args:
        title: Task title (<=256)
        description: Optional description
        deadline: Optional ISO-8601 datetime string
        priority: low | medium | high
        tags: List of tags
        needs_clarification: Whether clarifications are required
        questions: List of clarification questions
    """

    title: str = Field(min_length=1, max_length=256)
    description: str = ""
    deadline: Optional[str] = None
    priority: str = Field(default="medium")
    tags: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    questions: List[ClarificationQuestion] = Field(default_factory=list)

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, v: str) -> str:
        allowed = {"low", "medium", "high"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return v


