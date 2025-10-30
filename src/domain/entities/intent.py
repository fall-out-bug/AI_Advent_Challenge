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
    """Structured result of parsing a natural language task intent.

    Purpose:
        Represents the extracted fields from user text and tracks whether
        clarification is required to complete task creation.

    Args:
        title: Short task title extracted from text
        description: Optional longer description
        deadline_iso: ISO8601 datetime string or None
        priority: One of "low"|"medium"|"high"
        tags: Optional list of tags
        needs_clarification: Whether more info is required
        questions: List of clarifying question prompts

    Example:
        IntentParseResult(
            title="Call mom",
            description=None,
            deadline_iso="2025-12-01T15:00:00Z",
            priority="high",
            tags=["family"],
            needs_clarification=False,
            questions=[],
        )
    """

    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    deadline_iso: Optional[str] = Field(None, description="ISO8601 deadline")
    priority: str = Field("medium", description='Priority: "low"|"medium"|"high"')
    tags: List[str] = Field(default_factory=list, description="Task tags")

    needs_clarification: bool = Field(False, description="Whether more info is needed")
    questions: List[str] = Field(default_factory=list, description="Clarifying questions")


