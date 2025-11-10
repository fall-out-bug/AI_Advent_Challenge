#!/usr/bin/env python3
"""CLI for executing benchmark scenarios."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Mapping

from src.application.benchmarking.models import (
    BenchmarkDirection,
    BenchmarkJudgeResult,
    BenchmarkMetricRule,
    BenchmarkScenarioConfig,
    BenchmarkSample,
)
from src.application.benchmarking.protocols import BenchmarkJudge
from src.application.benchmarking.runner import BenchmarkEvaluationRunner
from src.infrastructure.benchmarking.factory import create_benchmark_runner
from src.infrastructure.benchmarking.jsonl_dataset_provider import (
    JsonlBenchmarkDatasetProvider,
)
from src.infrastructure.benchmarking.metrics_recorder import (
    PrometheusBenchmarkRecorder,
)
from src.infrastructure.config.settings import get_settings


SCENARIO_REGISTRY: Mapping[str, dict[str, object]] = {
    "channel_digest_ru": {
        "dataset_id": "benchmark_digest_ru_v1",
        "prompt_version": "benchmark-2025-11-v1",
        "model_name": "gpt-4o",
        "metrics": (
            BenchmarkMetricRule(
                name="coverage",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.88,
                warn_value=0.80,
            ),
            BenchmarkMetricRule(
                name="accuracy",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.90,
                warn_value=0.85,
            ),
            BenchmarkMetricRule(
                name="coherence",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.90,
                warn_value=0.85,
            ),
            BenchmarkMetricRule(
                name="informativeness",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.88,
                warn_value=0.82,
            ),
            BenchmarkMetricRule(
                name="latency_seconds",
                direction=BenchmarkDirection.LOWER_IS_BETTER,
                pass_value=210.0,
                warn_value=240.0,
            ),
        ),
    },
    "review_summary_ru": {
        "dataset_id": "benchmark_review_ru_v1",
        "prompt_version": "benchmark-2025-11-v1",
        "model_name": "gpt-4o",
        "metrics": (
            BenchmarkMetricRule(
                name="coverage",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.87,
                warn_value=0.80,
            ),
            BenchmarkMetricRule(
                name="accuracy",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.90,
                warn_value=0.85,
            ),
            BenchmarkMetricRule(
                name="coherence",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.88,
                warn_value=0.82,
            ),
            BenchmarkMetricRule(
                name="informativeness",
                direction=BenchmarkDirection.HIGHER_IS_BETTER,
                pass_value=0.88,
                warn_value=0.82,
            ),
            BenchmarkMetricRule(
                name="latency_seconds",
                direction=BenchmarkDirection.LOWER_IS_BETTER,
                pass_value=300.0,
                warn_value=360.0,
            ),
        ),
    },
}


class GroundTruthJudge(BenchmarkJudge):
    """Return baseline scores from dataset for dry-run execution."""

    async def evaluate(
        self, sample: BenchmarkSample, scenario: BenchmarkScenarioConfig
    ) -> BenchmarkJudgeResult:
        scores = dict(sample.baseline_scores or {})
        if "latency_seconds" not in scores:
            latency = sample.metadata.get("latency_seconds")
            if isinstance(latency, (int, float)):
                scores["latency_seconds"] = float(latency)
        if not scores:
            scores = {rule.name: 1.0 for rule in scenario.metrics}
        return BenchmarkJudgeResult(scores=scores)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run benchmark scenario.")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=SCENARIO_REGISTRY.keys(),
        help="Scenario identifier (see Stage 05 plan).",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        help="Path to dataset JSONL file. Defaults to dataset directory in "
        "settings.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON file to store benchmark run results.",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Override LLM judge concurrency.",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Exit with non-zero code when overall outcome is WARN.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use stored benchmark scores instead of calling LLM judge (CI mode).",
    )
    return parser.parse_args()


def build_scenario_config(
    scenario_key: str,
    dataset_path: Path | None,
) -> BenchmarkScenarioConfig:
    """Construct scenario configuration with dataset path resolution."""

    settings = get_settings()
    definition = SCENARIO_REGISTRY[scenario_key]
    dataset_id = str(definition["dataset_id"])
    default_path = settings.benchmark_dataset_dir / dataset_id / "latest.jsonl"
    resolved_path = dataset_path or default_path
    if not resolved_path.exists():
        if dataset_path is not None:
            raise FileNotFoundError(
                f"Dataset file not found: {resolved_path}."
            )
        candidates = sorted((settings.benchmark_dataset_dir / dataset_id).glob("*.jsonl"))
        if not candidates:
            raise FileNotFoundError(
                "No dataset files found. Generate datasets via export scripts or "
                "provide --dataset explicitly."
            )
        resolved_path = candidates[-1]
    return BenchmarkScenarioConfig(
        scenario_id=scenario_key,
        dataset_path=resolved_path,
        dataset_id=dataset_id,
        model_name=str(definition["model_name"]),
        prompt_version=str(definition["prompt_version"]),
        metrics=definition["metrics"],  # type: ignore[arg-type]
    )


def serialise_result(run_result) -> dict:
    """Convert run result to JSON serialisable dictionary."""

    return {
        "scenario_id": run_result.scenario_id,
        "dataset_id": run_result.dataset_id,
        "overall": run_result.overall.value,
        "metrics": [
            {"name": metric.name, "value": metric.value, "outcome": metric.outcome.value}
            for metric in run_result.metrics
        ],
        "samples": [
            {
                "sample_id": sample.sample_id,
                "metrics": [
                    {
                        "name": metric.name,
                        "value": metric.value,
                        "outcome": metric.outcome.value,
                    }
                    for metric in sample.metrics
                ],
                "verdict": sample.verdict,
                "notes": sample.notes,
            }
            for sample in run_result.samples
        ],
        "metadata": dict(run_result.metadata),
    }


async def execute() -> int:
    args = parse_args()
    scenario = build_scenario_config(args.scenario, args.dataset)
    if args.dry_run:
        runner = BenchmarkEvaluationRunner(
            dataset_provider=JsonlBenchmarkDatasetProvider(),
            judge=GroundTruthJudge(),
            metrics_recorder=PrometheusBenchmarkRecorder(),
            max_concurrency=1,
        )
    else:
        runner = create_benchmark_runner(args.max_concurrency)
    run_result = await runner.run(scenario)
    result_json = serialise_result(run_result)
    print(json.dumps(result_json, indent=2, ensure_ascii=False))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result_json, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if run_result.overall.value == "fail":
        return 2
    if args.fail_on_warn and run_result.overall.value == "warn":
        return 3
    return 0


def main() -> None:
    """Entry point for CLI."""

    try:
        exit_code = asyncio.run(execute())
    except KeyboardInterrupt:
        print("Benchmark interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"Benchmark execution failed: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
