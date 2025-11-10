"""Tests for JSONL benchmark dataset provider."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.application.benchmarking.models import (
    BenchmarkMetricRule,
    BenchmarkDirection,
    BenchmarkScenarioConfig,
)
from src.infrastructure.benchmarking.jsonl_dataset_provider import (
    JsonlBenchmarkDatasetProvider,
)


@pytest.mark.asyncio
async def test_jsonl_provider_loads_samples(tmp_path: Path) -> None:
    """Provider parses JSON Lines file into benchmark samples."""

    dataset_file = tmp_path / "samples.jsonl"
    dataset_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "sample_id": "sample-1",
                        "source_text": "Original A",
                        "summary_markdown": "Summary A",
                        "metadata": {"language": "ru"},
                        "ground_truth": {
                            "llm_judge": {
                                "scores": {
                                    "coverage": 0.9,
                                    "accuracy": 0.85,
                                }
                            }
                        },
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "sample_id": "sample-2",
                        "source_text": "Original B",
                        "summary_markdown": "Summary B",
                        "metadata": {"language": "ru"},
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )

    scenario = BenchmarkScenarioConfig(
        scenario_id="digest_ru",
        dataset_path=dataset_file,
        dataset_id="benchmark_digest_ru_v1",
        model_name="gpt-4o",
        prompt_version="benchmark-2025-11-v1",
        metrics=(
            BenchmarkMetricRule(
                name="coverage",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.9,
                warn_value=0.85,
            ),
        ),
    )

    provider = JsonlBenchmarkDatasetProvider()
    samples = await provider.load_samples(scenario)

    assert len(samples) == 2
    assert samples[0].sample_id == "sample-1"
    assert samples[0].source_text == "Original A"
    assert samples[0].summary_text == "Summary A"
    assert samples[0].baseline_scores == {"coverage": 0.9, "accuracy": 0.85}


@pytest.mark.asyncio
async def test_jsonl_provider_requires_fields(tmp_path: Path) -> None:
    """Provider raises error when required fields missing."""

    dataset_file = tmp_path / "invalid.jsonl"
    dataset_file.write_text('{"sample_id": "sample-1"}', encoding="utf-8")

    scenario = BenchmarkScenarioConfig(
        scenario_id="invalid",
        dataset_path=dataset_file,
        dataset_id="invalid",
        model_name="gpt-4o",
        prompt_version="benchmark-2025-11-v1",
        metrics=tuple(),
    )

    provider = JsonlBenchmarkDatasetProvider()

    with pytest.raises(RuntimeError):
        await provider.load_samples(scenario)
