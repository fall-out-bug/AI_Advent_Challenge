"""Benchmark-specific value objects."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from pydantic import BaseModel, Field, model_validator


def _has_cyrillic(text: str) -> bool:
    """Return True when text contains at least one Cyrillic character."""

    for char in text:
        code = ord(char)
        if 0x0400 <= code <= 0x052F:
            return True
    return False


def _build_posts(raw_posts: tuple[str, ...]) -> list[dict[str, str]]:
    """Construct exporter-friendly posts list."""

    posts: list[dict[str, str]] = []
    for index, content in enumerate(raw_posts, start=1):
        posts.append(
            {
                "title": f"Пост {index}",
                "summary": content,
                "text": content,
            }
        )
    return posts


class DigestSample(BaseModel):
    """Value object describing seeded digest samples.

    Purpose:
        Represent digest artefacts stored in MongoDB while enforcing RU
        localisation constraints and latency metadata requirements.

    Attributes:
        digest_id: Unique identifier derived from channel and timestamp.
        channel: Telegram channel username (includes @ prefix).
        language: Locale marker, defaults to `ru`.
        summary_markdown: Markdown summary stored alongside digests.
        posts: Tuple of raw RU posts forming the digest.
        feature_flags: Applied feature flags for traceability.
        latency_seconds: Measured processing latency.
        created_at: Creation timestamp.
        llm_model: Summarisation model reference.
        quality_scores: Judge metrics for exporter compatibility.

    Example:
        >>> DigestSample(
        ...     digest_id=\"demo\",
        ...     channel=\"@demo\",
        ...     summary_markdown=\"- Пример.\",
        ...     posts=(\"RU текст\", \"Второй\", \"Третий\"),
        ...     feature_flags={\"enable_quality_evaluation\": True},
        ...     latency_seconds=120.0,
        ...     created_at=datetime.now(),
        ...     llm_model=\"qwen-7b\",
        ... )
    """

    digest_id: str
    channel: str
    language: str = "ru"
    summary_markdown: str
    posts: tuple[str, ...]
    feature_flags: Mapping[str, bool] = Field(default_factory=dict)
    latency_seconds: float
    created_at: datetime
    llm_model: str
    quality_scores: Mapping[str, float] = Field(
        default_factory=lambda: {
            "coverage": 0.92,
            "accuracy": 0.9,
            "coherence": 0.9,
            "informativeness": 0.91,
        }
    )

    @model_validator(mode="after")
    def validate_localisation(self) -> "DigestSample":
        """Enforce Day 23 localisation rules."""

        if not _has_cyrillic(self.summary_markdown):
            msg = "summary_markdown must contain Cyrillic characters."
            raise ValueError(msg)
        if len(self.posts) < 3:
            msg = "At least three raw posts required."
            raise ValueError(msg)
        if any(not _has_cyrillic(post) for post in self.posts):
            msg = "Raw posts must contain Cyrillic sentences."
            raise ValueError(msg)
        if self.latency_seconds <= 0:
            msg = "Latency must be positive."
            raise ValueError(msg)
        return self

    def to_document(self) -> dict[str, Any]:
        """Serialize sample into Mongo document shape.

        Purpose:
            Provide exporter-compatible structure for repository writes.

        Args:
            None.

        Returns:
            Dictionary following the existing digests schema.

        Raises:
            None.

        Example:
            >>> DigestSample(
            ...     digest_id=\"demo\",
            ...     channel=\"@demo\",
            ...     summary_markdown=\"- Пример.\",
            ...     posts=(\"RU\", \"RU\", \"RU\"),
            ...     feature_flags={\"enable_quality_evaluation\": True},
            ...     latency_seconds=120.0,
            ...     created_at=datetime.now(),
            ...     llm_model=\"qwen\",
            ... ).to_document()
        """

        return {
            "digest_id": self.digest_id,
            "channel": self.channel,
            "language": self.language,
            "summary_markdown": self.summary_markdown,
            "posts": _build_posts(self.posts),
            "feature_flags": dict(self.feature_flags),
            "latency_seconds": self.latency_seconds,
            "created_at": self.created_at,
            "metadata": {
                "feature_flags": dict(self.feature_flags),
                "llm_model": self.llm_model,
                "time_range_hours": 24,
            },
            "quality": {
                "llm_judge": {
                    "judge_model": "gpt-4o",
                    "prompt_version": "benchmark-2025-11-v1",
                    "scores": dict(self.quality_scores),
                    "verdict": "MEETS_EXPECTATIONS",
                }
            },
        }


class ReviewReportSample(BaseModel):
    """Value object describing modular reviewer outputs.

    Purpose:
        Capture reviewer synthesis data with enough metadata for exporter
        round-trips.

    Attributes:
        report_id: Unique identifier for the review.
        assignment_id: Original assignment/channel identifier.
        language: Locale marker, defaults to `ru`.
        summary_markdown: Reviewer synthesis summary.
        passes: Tuple of RU sentences used to build individual passes.
        feature_flags: Applied reviewer feature flags.
        latency_seconds: Processing latency metric.
        created_at: Creation timestamp.
        llm_model: Model responsible for the review.

    Example:
        >>> ReviewReportSample(
        ...     report_id=\"r1\",
        ...     assignment_id=\"@demo\",
        ...     summary_markdown=\"Результаты.\",
        ...     passes=(\"Проверка 1\", \"Проверка 2\", \"Проверка 3\"),
        ...     feature_flags={\"structured_review\": True},
        ...     latency_seconds=90.0,
        ...     created_at=datetime.now(),
        ...     llm_model=\"gpt-4o-mini\",
        ... )
    """

    report_id: str
    assignment_id: str
    language: str = "ru"
    summary_markdown: str
    passes: tuple[str, ...]
    feature_flags: Mapping[str, bool] = Field(default_factory=dict)
    latency_seconds: float
    created_at: datetime
    llm_model: str

    @model_validator(mode="after")
    def validate_passes(self) -> "ReviewReportSample":
        """Ensure reviewer passes comply with localisation rules."""

        if not self.passes:
            msg = "At least one review pass is required."
            raise ValueError(msg)
        if not _has_cyrillic(self.summary_markdown):
            msg = "Review summary must contain Cyrillic text."
            raise ValueError(msg)
        if any(not _has_cyrillic(section) for section in self.passes):
            msg = "Review passes must contain Cyrillic sentences."
            raise ValueError(msg)
        if self.latency_seconds <= 0:
            msg = "Latency must be positive."
            raise ValueError(msg)
        return self

    def to_document(self) -> dict[str, Any]:
        """Serialize review report into Mongo document shape.

        Purpose:
            Generate exporter-compatible documents for Mongo repositories.

        Args:
            None.

        Returns:
            Dictionary matching the existing review_reports schema.

        Raises:
            None.

        Example:
            >>> ReviewReportSample(
            ...     report_id=\"r1\",
            ...     assignment_id=\"@demo\",
            ...     summary_markdown=\"Результаты.\",
            ...     passes=(\"Проверка 1\", \"Проверка 2\", \"Проверка 3\"),
            ...     feature_flags={\"structured_review\": True},
            ...     latency_seconds=90.0,
            ...     created_at=datetime.now(),
            ...     llm_model=\"gpt-4o-mini\",
            ... ).to_document()
        """

        pass_documents = [
            {
                "pass_name": f"pass_{index}",
                "summary": section,
                "recommendations": [section],
                "findings": [
                    {
                        "title": f"Наблюдение {index}",
                        "description": section,
                    }
                ],
            }
            for index, section in enumerate(self.passes, start=1)
        ]
        return {
            "report_id": self.report_id,
            "assignment_id": self.assignment_id,
            "language": self.language,
            "created_at": self.created_at,
            "report": {
                "synthesis": self.summary_markdown,
                "passes": pass_documents,
                "metadata": {
                    "llm_model": self.llm_model,
                    "feature_flags": dict(self.feature_flags),
                    "latency_seconds": self.latency_seconds,
                    "llm_judge": {
                        "judge_model": "gpt-4o",
                        "scores": {"coverage": 0.92, "accuracy": 0.9},
                    },
                },
            },
        }


class ChannelSnapshot(BaseModel):
    """Channel-level counters captured after seeding completes.

    Purpose:
        Provide structured data for seeding snapshots and downstream evidence.

    Attributes:
        channel: Telegram channel identifier.
        digests: Total digests observed after seeding.
        review_reports: Total review reports observed after seeding.
    """

    channel: str
    digests: int
    review_reports: int


class BenchmarkSeedingResult(BaseModel):
    """Outcome returned by SeedBenchmarkDataUseCase.

    Purpose:
        Share snapshot path and per-channel counts with presentation layers.

    Attributes:
        snapshot_path: Absolute path to `channel_counts.json`.
        generated_channels: Mapping of channel to ChannelSnapshot.
    """

    snapshot_path: str
    generated_channels: dict[str, ChannelSnapshot]

