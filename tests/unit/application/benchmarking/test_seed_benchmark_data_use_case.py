"""Unit tests for SeedBenchmarkDataUseCase."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.benchmarking.seed_benchmark_data import SeedBenchmarkDataUseCase


def _fixed_now() -> datetime:
    return datetime(2025, 11, 15, 12, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_seed_use_case_populates_missing_records(tmp_path: Path) -> None:
    """Seeds digests and review reports when channel is below threshold."""

    repository = AsyncMock()
    repository.count_digests_since = AsyncMock(return_value=10)
    repository.count_review_reports_since = AsyncMock(return_value=8)
    repository.insert_digest_samples = AsyncMock()
    repository.insert_review_reports = AsyncMock()
    metrics = Mock()

    use_case = SeedBenchmarkDataUseCase(
        repository=repository,
        dataset_dir=tmp_path,
        metrics=metrics,
        now_provider=_fixed_now,
    )

    result = await use_case.execute(
        channels=("@tech_radar_ru",),
        days=30,
        minimum_per_channel=30,
    )

    repository.insert_digest_samples.assert_awaited_once()
    repository.insert_review_reports.assert_awaited_once()
    digest_samples = repository.insert_digest_samples.await_args.args[0]
    review_samples = repository.insert_review_reports.await_args.args[0]
    assert len(digest_samples) == 20
    assert len(review_samples) == 22

    metrics.record_digest_ingest.assert_called_with("@tech_radar_ru", 20)
    metrics.record_review_report_ingest.assert_called_with("@tech_radar_ru", 22)

    snapshot_path = Path(result.snapshot_path)
    assert snapshot_path.exists()
    snapshot = json.loads(snapshot_path.read_text())
    assert snapshot["channels"][0]["channel"] == "@tech_radar_ru"
    assert snapshot["channels"][0]["digests"] == 30
    assert snapshot["channels"][0]["review_reports"] == 30


@pytest.mark.asyncio
async def test_seed_use_case_skips_channels_that_meet_threshold(tmp_path: Path) -> None:
    """Skips data generation when channel already satisfies minimum."""

    repository = AsyncMock()
    repository.count_digests_since = AsyncMock(return_value=35)
    repository.count_review_reports_since = AsyncMock(return_value=40)
    repository.insert_digest_samples = AsyncMock()
    repository.insert_review_reports = AsyncMock()
    metrics = Mock()

    use_case = SeedBenchmarkDataUseCase(
        repository=repository,
        dataset_dir=tmp_path,
        metrics=metrics,
        now_provider=_fixed_now,
    )

    result = await use_case.execute(
        channels=("@startup_digest_ru",),
        days=30,
        minimum_per_channel=30,
    )

    repository.insert_digest_samples.assert_not_called()
    repository.insert_review_reports.assert_not_called()
    metrics.record_digest_ingest.assert_called_with("@startup_digest_ru", 0)
    metrics.record_review_report_ingest.assert_called_with("@startup_digest_ru", 0)

    snapshot_path = Path(result.snapshot_path)
    snapshot = json.loads(snapshot_path.read_text())
    assert snapshot["channels"][0]["digests"] == 35
    assert result.generated_channels["@startup_digest_ru"].digests == 35

