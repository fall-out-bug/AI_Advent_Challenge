"""Rate limiting utilities for review execution."""

from __future__ import annotations

from dataclasses import dataclass

from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository


class ReviewRateLimitExceeded(RuntimeError):
    """Raised when review execution exceeds configured rate limits."""

    def __init__(self, scope: str, limit: int) -> None:
        message = f"Review rate limit exceeded for {scope}. Limit: {limit} per window."
        super().__init__(message)
        self.scope = scope
        self.limit = limit


@dataclass
class ReviewRateLimiterConfig:
    """Configuration container for review rate limiting."""

    window_seconds: int
    per_student: int
    per_assignment: int


class ReviewRateLimiter:
    """Rate limiter guarding review execution per student and assignment."""

    def __init__(
        self,
        repository: LongTasksRepository,
        config: ReviewRateLimiterConfig,
    ) -> None:
        self._repository = repository
        self._config = config

    async def ensure_within_limits(self, student_id: str, assignment_id: str) -> None:
        """Ensure review execution complies with configured rate limits."""

        window = self._config.window_seconds
        student_count = await self._repository.count_reviews_in_window(
            user_id=int(student_id),
            window_seconds=window,
        )
        if student_count >= self._config.per_student:
            raise ReviewRateLimitExceeded("student", self._config.per_student)

        assignment_count = await self._repository.count_reviews_in_window(
            assignment_id=assignment_id,
            window_seconds=window,
        )
        if assignment_count >= self._config.per_assignment:
            raise ReviewRateLimitExceeded("assignment", self._config.per_assignment)
