#!/usr/bin/env python3
"""Export fine-tuning dataset from evaluations.

Purpose:
    Export high-quality evaluation samples from MongoDB to JSONL format
    suitable for Hugging Face Transformers fine-tuning.

Usage:
    python scripts/export_fine_tuning_dataset.py
    python scripts/export_fine_tuning_dataset.py --min-score 0.8 --limit 500
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.repositories.summarization_evaluation_repository import (
    SummarizationEvaluationRepository,
)


async def main() -> None:
    """Export fine-tuning dataset."""
    parser = argparse.ArgumentParser(
        description="Export fine-tuning dataset from evaluations"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Minimum score threshold (default: from settings)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of samples to export (default: 1000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/fine_tuning_dataset.jsonl",
        help="Output file path (default: data/fine_tuning_dataset.jsonl)",
    )

    args = parser.parse_args()

    settings = get_settings()
    min_score = args.min_score or settings.evaluation_min_score_for_dataset

    print(f"Exporting fine-tuning dataset...")
    print(f"  Min score: {min_score}")
    print(f"  Limit: {args.limit}")
    print(f"  Output: {args.output}")

    # Get repository
    db = await get_db()
    repo = SummarizationEvaluationRepository(db)

    # Count available samples
    total_count = await repo.count_evaluations(min_score=min_score)
    print(f"  Available samples with score >= {min_score}: {total_count}")

    if total_count == 0:
        print("No samples found matching criteria.")
        return

    # Export high-quality samples
    dataset = await repo.export_fine_tuning_dataset(
        min_score=min_score,
        limit=args.limit,
    )

    if not dataset:
        print("No samples exported.")
        return

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to JSONL file
    with open(output_path, "w", encoding="utf-8") as f:
        for sample in dataset:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    # Calculate statistics
    avg_score = sum(s["score"] for s in dataset) / len(dataset)
    min_exported = min(s["score"] for s in dataset)
    max_exported = max(s["score"] for s in dataset)

    print(f"\n✅ Exported {len(dataset)} samples to {args.output}")
    print(f"  Average score: {avg_score:.2f}")
    print(f"  Score range: {min_exported:.2f} - {max_exported:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
