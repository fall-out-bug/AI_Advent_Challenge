"""Benchmark repository interface definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from src.domain.benchmark.value_objects import DigestSample, ReviewReportSample


class BenchmarkRepository(Protocol):
    """Repository interface for benchmark datasets.

    Purpose:
        Define the contract for reading/writing seeded digests and review
        reports stored in MongoDB.

    Args:
        Protocol has no arguments; concrete implementations accept their own.

    Returns:
        Protocol methods return awaitable objects documented below.

    Raises:
        NotImplementedError: When concrete implementations fail to override a
            defined method.

    Example:
        >>> repo: BenchmarkRepository
        >>> await repo.count_digests_since("@channel", datetime.utcnow())
        42
    """

    async def count_digests_since(self, channel: str, since: datetime) -> int:
        """Return digest count for the channel within the window."""

    async def count_review_reports_since(self, channel: str, since: datetime) -> int:
        """Return review report count for the channel within the window."""

    async def insert_digest_samples(self, samples: Sequence[DigestSample]) -> None:
        """Insert digest samples into storage."""

    async def insert_review_reports(
        self, samples: Sequence[ReviewReportSample]
    ) -> None:
        """Insert review report samples into storage."""
