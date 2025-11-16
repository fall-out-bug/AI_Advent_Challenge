"""Seed benchmark datasets for Epic 23."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Protocol, Sequence

from src.domain.benchmark.value_objects import (
    BenchmarkSeedingResult,
    ChannelSnapshot,
    DigestSample,
    ReviewReportSample,
)
from src.domain.interfaces.benchmark_repository import BenchmarkRepository


class BenchmarkSeedingMetrics(Protocol):
    """Metrics recording contract for seeding operations.

    Purpose:
        Allow the application layer to emit observability signals without
        depending on Prometheus primitives.

    Args:
        Protocol has no constructor arguments.

    Returns:
        Implementations do not return values; methods update metrics backends.

    Exceptions:
        NotImplementedError: Raised when concrete adapters omit a method.

    Example:
        >>> metrics: BenchmarkSeedingMetrics
        >>> metrics.record_digest_ingest("@demo", 5)
    """

    def record_digest_ingest(self, channel: str, inserted: int) -> None:
        """Record number of digests inserted for a channel."""

    def record_review_report_ingest(self, channel: str, inserted: int) -> None:
        """Record number of review reports inserted for a channel."""


class SyntheticDigestFactory:
    """Generate deterministic digest samples for RU localisation checks.

    Purpose:
        Provide repeatable seed data so Mongo can satisfy exporter thresholds
        even when production dumps are unavailable.

    Args:
        None.

    Example:
        >>> factory = SyntheticDigestFactory()
        >>> factory.build("@demo", 2, datetime.now(), datetime.now())  # doctest: +SKIP
    """

    _topics = (
        "ИИ-сервисы",
        "финтех",
        "образование",
        "госуслуги",
        "кибербезопасность",
    )

    def build(
        self,
        channel: str,
        count: int,
        since: datetime,
        now: datetime,
    ) -> tuple[DigestSample, ...]:
        """Create digest samples with timestamps within the window.

        Purpose:
            Generate `count` digest samples per channel that satisfy localisation
            rules and exporter schema expectations.

        Args:
            channel: Telegram channel identifier beginning with `@`.
            count: Number of samples to create.
            since: Earliest timestamp allowed for seeded records.
            now: Current timestamp used to derive record ordering.

        Returns:
            Tuple of DigestSample instances ready for repository insertion.

        Raises:
            ValueError: Propagated from DigestSample validation if inputs are invalid.

        Example:
            >>> factory = SyntheticDigestFactory()
            >>> factory.build("@demo", 1, datetime.now(), datetime.now())  # doctest: +SKIP
        """

        samples: list[DigestSample] = []
        for index in range(count):
            topic = self._topics[index % len(self._topics)]
            created_at = now - timedelta(days=(index % max(1, (now - since).days or 1)))
            summary = "\n".join(
                [
                    f"- {topic} обновление {index + 1}.",
                    f"- Канал {channel} освещает инициативу.",
                    "- Локализация подтверждена.",
                ]
            )
            posts = (
                f"{topic} усиливает продукты в регионе.",
                "Компания делится метриками роста.",
                "Эксперты обсуждают внедрение решения.",
            )
            samples.append(
                DigestSample(
                    digest_id=f"{channel}-{created_at:%Y%m%d}-{index}",
                    channel=channel,
                    summary_markdown=summary,
                    posts=posts,
                    feature_flags={
                        "enable_quality_evaluation": True,
                        "enable_async_long_summarization": True,
                    },
                    latency_seconds=120.0 + float(index),
                    created_at=created_at,
                    llm_model="qwen-7b",
                )
            )
        return tuple(samples)


class SyntheticReviewReportFactory:
    """Generate deterministic review reports per channel.

    Purpose:
        Ensure reviewer datasets track digests one-to-one so exporter tests have
        consistent coverage per channel.

    Args:
        None.
    """

    def build(
        self,
        channel: str,
        count: int,
        since: datetime,
        now: datetime,
    ) -> tuple[ReviewReportSample, ...]:
        """Create review reports with RU localisation metadata.

        Purpose:
            Generate reviewer outputs mirroring production schema to unblock
            exporter validation.

        Args:
            channel: Telegram channel identifier used as assignment_id.
            count: Number of synthetic reports to produce.
            since: Minimum allowed timestamp for generated documents.
            now: Reference timestamp for distribution across the window.

        Returns:
            Tuple of ReviewReportSample instances.

        Raises:
            ValueError: Propagated from ReviewReportSample validation.

        Example:
            >>> SyntheticReviewReportFactory().build("@demo", 1, datetime.now(), datetime.now())
            ... # doctest: +SKIP
        """

        samples: list[ReviewReportSample] = []
        for index in range(count):
            created_at = now - timedelta(days=(index % max(1, (now - since).days or 1)))
            passes = (
                "Проверка структуры задания прошла успешно.",
                "Найдены области для улучшения ясности требований.",
                "Рекомендовано усилить контроль качества.",
            )
            samples.append(
                ReviewReportSample(
                    report_id=f"{channel}-report-{created_at:%Y%m%d}-{index}",
                    assignment_id=channel,
                    summary_markdown="Отчёт подтверждает RU локализацию и метрики.",
                    passes=passes,
                    feature_flags={"structured_review": True},
                    latency_seconds=95.0 + float(index),
                    created_at=created_at,
                    llm_model="gpt-4o-mini",
                )
            )
        return tuple(samples)


class SeedBenchmarkDataUseCase:
    """Application use case for seeding benchmark datasets.

    Purpose:
        Guarantee that MongoDB contains enough digests and review reports per
        RU channel so Stage 05 exporters and benchmarks can run deterministically.

    Args:
        repository: Persistence adapter satisfying BenchmarkRepository.
        dataset_dir: Directory where channel snapshots should be written.
        metrics: Metrics adapter for observability requirements.
        now_provider: Optional callable returning timezone-aware datetime.
        digest_factory: Optional factory overriding the default generator.
        review_factory: Optional factory overriding the default generator.

    Example:
        >>> use_case = SeedBenchmarkDataUseCase(repo, Path(\"data\"), metrics)
        >>> await use_case.execute([\"@demo\"], 30, 30)  # doctest: +SKIP
    """

    def __init__(
        self,
        repository: BenchmarkRepository,
        dataset_dir: Path,
        metrics: BenchmarkSeedingMetrics,
        now_provider: Callable[[], datetime] | None = None,
        digest_factory: SyntheticDigestFactory | None = None,
        review_factory: SyntheticReviewReportFactory | None = None,
    ) -> None:
        """Initialize use case dependencies.

        Purpose:
            Store injected dependencies for later execution.

        Args:
            repository: BenchmarkRepository implementation.
            dataset_dir: Base path for snapshot artefacts.
            metrics: Metrics adapter for Prometheus counters.
            now_provider: Optional callable returning a datetime (defaults UTC).
            digest_factory: Optional custom digest factory.
            review_factory: Optional custom review factory.

        Returns:
            None.

        Example:
            >>> SeedBenchmarkDataUseCase(repo, Path(\"data\"), metrics)  # doctest: +SKIP
        """

        self._repository = repository
        self._dataset_dir = dataset_dir
        self._metrics = metrics
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self._digest_factory = digest_factory or SyntheticDigestFactory()
        self._review_factory = review_factory or SyntheticReviewReportFactory()

    async def execute(
        self,
        channels: Sequence[str],
        days: int,
        minimum_per_channel: int,
    ) -> BenchmarkSeedingResult:
        """Run seeding workflow for provided channels.

        Purpose:
            Populate MongoDB collections so every channel meets the minimum
            document requirement within the rolling window.

        Args:
            channels: Sequence of channel usernames (e.g., \"@tech\").
            days: Rolling window length used for validation.
            minimum_per_channel: Required minimum per channel.

        Returns:
            BenchmarkSeedingResult describing counts and snapshot path.

        Raises:
            ValueError: If no channels are supplied.

        Example:
            >>> await use_case.execute([\"@demo\"], 30, 30)  # doctest: +SKIP
        """

        if not channels:
            msg = "At least one channel is required for seeding."
            raise ValueError(msg)

        now = self._now_provider()
        since = now - timedelta(days=days)
        channel_snapshots: dict[str, ChannelSnapshot] = {}
        for channel in dict.fromkeys(channels):
            normalized = channel.strip()
            if not normalized:
                continue
            snapshot = await self._process_channel(
                normalized, since, now, minimum_per_channel
            )
            channel_snapshots[normalized] = snapshot
        snapshot_path = self._write_snapshot(now, days, tuple(channel_snapshots.values()))
        return BenchmarkSeedingResult(
            snapshot_path=str(snapshot_path),
            generated_channels=channel_snapshots,
        )

    async def _process_channel(
        self,
        channel: str,
        since: datetime,
        now: datetime,
        minimum: int,
    ) -> ChannelSnapshot:
        """Seed digests and review reports for a single channel."""

        digest_total = await self._seed_digests(channel, since, now, minimum)
        review_total = await self._seed_review_reports(channel, since, now, minimum)
        return ChannelSnapshot(
            channel=channel,
            digests=digest_total,
            review_reports=review_total,
        )

    async def _seed_digests(
        self,
        channel: str,
        since: datetime,
        now: datetime,
        minimum: int,
    ) -> int:
        """Seed digest samples when channel is below threshold."""

        existing = await self._repository.count_digests_since(channel, since)
        missing = max(0, minimum - existing)
        if missing:
            samples = self._digest_factory.build(channel, missing, since, now)
            await self._repository.insert_digest_samples(samples)
        self._metrics.record_digest_ingest(channel, missing)
        return existing + missing

    async def _seed_review_reports(
        self,
        channel: str,
        since: datetime,
        now: datetime,
        minimum: int,
    ) -> int:
        """Seed review report samples when below threshold."""

        existing = await self._repository.count_review_reports_since(channel, since)
        missing = max(0, minimum - existing)
        if missing:
            samples = self._review_factory.build(channel, missing, since, now)
            await self._repository.insert_review_reports(samples)
        self._metrics.record_review_report_ingest(channel, missing)
        return existing + missing

    def _write_snapshot(
        self,
        now: datetime,
        days: int,
        snapshots: Sequence[ChannelSnapshot],
    ) -> Path:
        """Persist channel counts to benchmark_dataset_dir."""

        snapshot_dir = self._dataset_dir / "snapshots" / now.strftime("%Y-%m-%d")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": now.isoformat(),
            "window_days": days,
            "channels": [snapshot.model_dump() for snapshot in snapshots],
        }
        path = snapshot_dir / "channel_counts.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
