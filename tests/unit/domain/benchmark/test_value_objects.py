"""Unit tests for benchmark domain value objects."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.benchmark.value_objects import DigestSample


def test_digest_sample_requires_cyrillic_summary() -> None:
    """Summary must contain Cyrillic characters for RU localisation."""

    with pytest.raises(ValueError):
        DigestSample(
            digest_id="digest-1",
            channel="@tech_radar_ru",
            language="ru",
            summary_markdown="Summary without locale markers",
            posts=("Post about AI", "Second sentence", "Third sentence"),
            feature_flags={"enable_quality_evaluation": True},
            latency_seconds=120.0,
            created_at=datetime.now(timezone.utc),
            llm_model="qwen-7b",
        )


def test_digest_sample_to_document_matches_exporter_shape() -> None:
    """Digest sample serializes into exporter-compatible schema."""

    sample = DigestSample(
        digest_id="digest-2",
        channel="@startup_digest_ru",
        language="ru",
        summary_markdown="- Пилот.\n- Экспорт.",
        posts=(
            "Пост про ИИ.",
            "Компания запустила сервис.",
            "Стартап нашел инвестиции.",
        ),
        feature_flags={"enable_quality_evaluation": True},
        latency_seconds=150.0,
        created_at=datetime(2025, 11, 10, tzinfo=timezone.utc),
        llm_model="qwen-7b",
    )

    document = sample.to_document()

    assert document["digest_id"] == "digest-2"
    assert document["channel"] == "@startup_digest_ru"
    assert len(document["posts"]) == 3
    assert document["quality"]["llm_judge"]["scores"]["coverage"] == 0.92
