"""Mongo implementation of BenchmarkRepository."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.benchmark.value_objects import DigestSample, ReviewReportSample
from src.domain.interfaces.benchmark_repository import BenchmarkRepository


class MongoBenchmarkRepository(BenchmarkRepository):
    """Persist seeded benchmark data in MongoDB collections.

    Purpose:
        Provide MongoDB-backed implementation of BenchmarkRepository with
        minimal assumptions about document shape.

    Args:
        db: AsyncIOMotorDatabase connected to the target Mongo instance.

    Example:
        >>> repo = MongoBenchmarkRepository(db)
        >>> await repo.count_digests_since("@demo", datetime.utcnow())  # doctest: +SKIP
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Store database dependency.

        Purpose:
            Keep reference to Mongo database for later CRUD operations.

        Args:
            db: AsyncIOMotorDatabase handle.
        """

        self._db = db

    async def count_digests_since(self, channel: str, since: datetime) -> int:
        """Return digest count for channel since timestamp.

        Purpose:
            Compute how many digests exist for validation windows.

        Args:
            channel: Telegram channel identifier.
            since: Inclusive lower bound timestamp.

        Returns:
            Number of matching digests.
        """

        query = {"channel": channel, "created_at": {"$gte": since}}
        return await self._db.digests.count_documents(query)

    async def count_review_reports_since(self, channel: str, since: datetime) -> int:
        """Return review report count for channel since timestamp.

        Purpose:
            Determine whether review reports satisfy the minimum threshold.

        Args:
            channel: Telegram channel identifier.
            since: Inclusive lower bound timestamp.

        Returns:
            Number of matching review reports.
        """

        query = {"assignment_id": channel, "created_at": {"$gte": since}}
        return await self._db.review_reports.count_documents(query)

    async def insert_digest_samples(self, samples: Sequence[DigestSample]) -> None:
        """Insert digest samples into the digests collection.

        Purpose:
            Persist generated digests using the exporter-compatible schema.

        Args:
            samples: Iterable of DigestSample records ready for insertion.
        """

        if not samples:
            return
        documents = [sample.to_document() for sample in samples]
        await self._db.digests.insert_many(documents)

    async def insert_review_reports(
        self, samples: Sequence[ReviewReportSample]
    ) -> None:
        """Insert review reports into the review_reports collection.

        Purpose:
            Persist reviewer outputs to support exporter tests.

        Args:
            samples: Iterable of ReviewReportSample records ready for insertion.
        """

        if not samples:
            return
        documents = [sample.to_document() for sample in samples]
        await self._db.review_reports.insert_many(documents)

