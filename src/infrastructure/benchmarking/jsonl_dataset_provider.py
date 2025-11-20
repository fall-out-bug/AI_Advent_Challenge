"""JSONL-backed dataset provider for benchmarks."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Sequence

from src.application.benchmarking.models import BenchmarkSample, BenchmarkScenarioConfig
from src.application.benchmarking.protocols import BenchmarkDatasetProvider


class JsonlBenchmarkDatasetProvider(BenchmarkDatasetProvider):
    """Load benchmark samples from JSON Lines files.

    Purpose:
        Provide a simple filesystem-backed implementation for Stage 05 datasets
        while remaining compatible with the application-level protocol.

    Args:
        encoding: File encoding, defaults to UTF-8.

    Returns:
        Instance ready to load JSONL benchmark datasets.

    Raises:
        None.

    Example:
        >>> provider = JsonlBenchmarkDatasetProvider()
        >>> samples = await provider.load_samples(scenario)
    """

    def __init__(self, encoding: str = "utf-8") -> None:
        self._encoding = encoding

    async def load_samples(
        self, scenario: BenchmarkScenarioConfig
    ) -> Sequence[BenchmarkSample]:
        """Load samples for the given scenario.

        Purpose:
            Parse JSON Lines content into BenchmarkSample instances.

        Args:
            scenario: Benchmark scenario configuration.

        Returns:
            Sequence of BenchmarkSample entries.

        Raises:
            RuntimeError: If required fields are missing or file cannot be read.

        Example:
            >>> await provider.load_samples(scenario)
            [BenchmarkSample(...)]
        """

        raw_lines = await asyncio.to_thread(
            scenario.dataset_path.read_text, encoding=self._encoding
        )
        samples: list[BenchmarkSample] = []
        for idx, line in enumerate(raw_lines.splitlines(), start=1):
            if not line.strip():
                continue
            data = self._parse_line(line, scenario.dataset_path, idx)
            samples.append(self._build_sample(data))
        return samples

    def _parse_line(self, line: str, path: Path, line_number: int) -> dict[str, Any]:
        try:
            return json.loads(line)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Invalid JSON in dataset {path} at line {line_number}: {error}"
            ) from error

    def _build_sample(self, data: dict[str, Any]) -> BenchmarkSample:
        sample_id = data.get("sample_id")
        source_text = data.get("source_text")
        summary_text = data.get("summary_markdown") or data.get("summary_text")
        metadata = self._ensure_mapping(data.get("metadata", {}))
        baseline = None
        if isinstance(data.get("ground_truth"), dict):
            llm_judge = data["ground_truth"].get("llm_judge") or {}
            baseline_scores = llm_judge.get("scores")
            if isinstance(baseline_scores, dict):
                baseline = {
                    key: float(value)
                    for key, value in baseline_scores.items()
                    if isinstance(value, (int, float))
                }
        latency_value = data.get("latency_seconds")
        if isinstance(latency_value, (int, float)):
            baseline = baseline or {}
            baseline["latency_seconds"] = float(latency_value)
            metadata.setdefault("latency_seconds", float(latency_value))

        if not sample_id or not source_text or not summary_text:
            raise RuntimeError(
                "Dataset sample missing required fields "
                f"(sample_id/source_text/summary_text). Received: {data.keys()}"
            )
        return BenchmarkSample(
            sample_id=str(sample_id),
            source_text=str(source_text),
            summary_text=str(summary_text),
            metadata=metadata,
            baseline_scores=baseline,
        )

    @staticmethod
    def _ensure_mapping(metadata: Any) -> dict[str, Any]:
        if isinstance(metadata, dict):
            return metadata
        return {}
