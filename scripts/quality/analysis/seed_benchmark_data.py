#!/usr/bin/env python3
"""Seed benchmark datasets into MongoDB."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Sequence

from src.application.benchmarking.seed_benchmark_data import SeedBenchmarkDataUseCase
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import close_client, get_db
from src.infrastructure.metrics.benchmark_metrics import (
    PrometheusBenchmarkSeedingMetrics,
)
from src.infrastructure.repositories.mongo_benchmark_repository import (
    MongoBenchmarkRepository,
)


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Seed benchmark datasets.")
    parser.add_argument(
        "--channels",
        required=True,
        help="Comma-separated list of Telegram channels (e.g. @one,@two).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Rolling window in days to validate counts.",
    )
    parser.add_argument(
        "--minimum",
        type=int,
        default=30,
        help="Minimum documents required per channel.",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        help="Override Settings.benchmark_dataset_dir for snapshot output.",
    )
    return parser.parse_args()


def _parse_channels(raw: str) -> Sequence[str]:
    """Split channel string into sanitized identifiers."""

    return [item.strip() for item in raw.split(",") if item.strip()]


async def main_async() -> None:
    """Entrypoint for async execution."""

    args = _parse_args()
    channels = _parse_channels(args.channels)
    if not channels:
        raise SystemExit("At least one channel must be provided.")

    db = await get_db()
    settings = get_settings()
    dataset_dir = args.dataset_dir or settings.benchmark_dataset_dir

    use_case = SeedBenchmarkDataUseCase(
        repository=MongoBenchmarkRepository(db),
        dataset_dir=dataset_dir,
        metrics=PrometheusBenchmarkSeedingMetrics(),
    )
    result = await use_case.execute(
        channels=channels,
        days=args.days,
        minimum_per_channel=args.minimum,
    )
    print(f"Benchmark snapshot written to {result.snapshot_path}", flush=True)


def main() -> None:
    """CLI entrypoint."""

    try:
        asyncio.run(main_async())
    finally:
        try:
            asyncio.run(close_client())
        except RuntimeError:
            # Event loop already closed; ignore.
            pass


if __name__ == "__main__":
    main()

