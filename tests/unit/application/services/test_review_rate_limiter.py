"""Unit tests for review rate limiter service."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.application.services.review_rate_limiter import (
    ReviewRateLimitExceeded,
    ReviewRateLimiter,
    ReviewRateLimiterConfig,
)


@pytest.fixture()
def limiter_config() -> ReviewRateLimiterConfig:
    return ReviewRateLimiterConfig(window_seconds=3600, per_student=3, per_assignment=10)


@pytest.mark.asyncio
async def test_allows_within_limits(limiter_config: ReviewRateLimiterConfig) -> None:
    repository = AsyncMock()
    repository.count_reviews_in_window = AsyncMock(side_effect=[1, 2])

    limiter = ReviewRateLimiter(repository, limiter_config)

    await limiter.ensure_within_limits("123", "hw-1")

    repository.count_reviews_in_window.assert_any_call(user_id=123, window_seconds=3600)
    repository.count_reviews_in_window.assert_any_call(assignment_id="hw-1", window_seconds=3600)


@pytest.mark.asyncio
async def test_raises_when_student_limit_reached(limiter_config: ReviewRateLimiterConfig) -> None:
    repository = AsyncMock()
    repository.count_reviews_in_window = AsyncMock(side_effect=[3, 0])

    limiter = ReviewRateLimiter(repository, limiter_config)

    with pytest.raises(ReviewRateLimitExceeded) as exc_info:
        await limiter.ensure_within_limits("123", "hw-1")

    assert exc_info.value.scope == "student"


@pytest.mark.asyncio
async def test_raises_when_assignment_limit_reached(limiter_config: ReviewRateLimiterConfig) -> None:
    repository = AsyncMock()
    repository.count_reviews_in_window = AsyncMock(side_effect=[0, 10])

    limiter = ReviewRateLimiter(repository, limiter_config)

    with pytest.raises(ReviewRateLimitExceeded) as exc_info:
        await limiter.ensure_within_limits("123", "hw-1")

    assert exc_info.value.scope == "assignment"
