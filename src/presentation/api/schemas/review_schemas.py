"""Pydantic schemas for review API."""

from pydantic import BaseModel, Field


class CreateReviewRequest(BaseModel):
    """Request model for creating review task."""

    student_id: str = Field(..., description="Student identifier")
    assignment_id: str = Field(..., description="Assignment identifier")
    new_submission_path: str = Field(..., description="Path to new submission ZIP")
    previous_submission_path: str | None = Field(
        None, description="Optional path to previous submission"
    )


class ReviewStatusResponse(BaseModel):
    """Response model for review status."""

    task_id: str
    status: str
    student_id: str | None = None
    assignment_id: str | None = None
    created_at: str | None = None
    finished_at: str | None = None
    result: dict | None = None
    error: str | None = None
