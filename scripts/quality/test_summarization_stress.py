#!/usr/bin/env python3
"""Stress test script for summarization system.

Purpose:
    Tests summarization system on large text files with various configurations.
    Measures performance, quality, and stability.

Usage:
    python scripts/quality/test_summarization_stress.py [--file PATH] [--max-sentences N] [--chunk-size N]
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.domain.value_objects.summarization_context import SummarizationContext
from src.infrastructure.config.settings import get_settings
from src.infrastructure.di.container import SummarizationContainer
from src.infrastructure.llm.token_counter import TokenCounter
from src.infrastructure.logging import get_logger

logger = get_logger("stress_test")


async def run_summarization_test(
    text: str,
    max_sentences: int,
    chunk_size: int,
    language: str = "ru",
) -> dict[str, Any]:
    """Run single summarization test.

    Args:
        text: Input text to summarize.
        max_sentences: Maximum sentences in summary.
        chunk_size: Max tokens per chunk for map-reduce.
        language: Language for summarization.

    Returns:
        Dictionary with test results and metrics.
    """
    settings = get_settings()

    # Create DI container with proper LLM URL
    container = SummarizationContainer()
    llm_url = os.getenv("LLM_URL", settings.llm_url)
    container.config.from_dict({"llm_url": llm_url})

    summarizer = container.adaptive_summarizer()
    token_counter = TokenCounter()

    # Calculate text metrics
    total_tokens = token_counter.count_tokens(text)

    context = SummarizationContext(
        time_period_hours=24,
        source_type="documents",  # Use 'documents' for stress test
    )

    # Run summarization
    start_time = time.time()

    try:
        summary_result = await summarizer.summarize_text(
            text=text,
            max_sentences=max_sentences,
            language=language,
            context=context,
        )
        elapsed_time = time.time() - start_time

        # Extract quality metrics if available
        quality_score = (
            summary_result.metadata.get("quality_score", {})
            if summary_result.metadata
            else {}
        )

        # Calculate chunk count from metadata
        chunk_count = (
            summary_result.metadata.get("chunk_count", 0)
            if summary_result.metadata
            else 0
        )

        return {
            "success": True,
            "method": summary_result.method,
            "summary_text": summary_result.text,
            "summary_length": len(summary_result.text),
            "sentences_count": summary_result.sentences_count,
            "total_tokens": total_tokens,
            "chunk_count": chunk_count,
            "elapsed_time": elapsed_time,
            "tokens_per_second": total_tokens / elapsed_time if elapsed_time > 0 else 0,
            "quality_score": (
                quality_score.get("score", 0.0)
                if isinstance(quality_score, dict)
                else 0.0
            ),
            "confidence": summary_result.confidence,
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Summarization failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "elapsed_time": elapsed_time,
            "total_tokens": total_tokens,
        }


async def run_stress_test(
    file_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run complete stress test suite.

    Args:
        file_path: Path to text file.
        output_dir: Directory for output files (default: project_root/stress_test_results).

    Returns:
        Dictionary with all test results.
    """
    logger.info(f"Starting stress test on file: {file_path}")

    # Load text
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    logger.info(f"Loaded text: {len(text)} characters")

    # Setup output directory
    if output_dir is None:
        output_dir = project_root / "stress_test_results"
    output_dir.mkdir(exist_ok=True)

    # Test configurations
    configs = []

    # Different max_sentences
    for max_sent in [5, 8, 10, 15]:
        configs.append(
            {
                "name": f"max_sentences_{max_sent}",
                "max_sentences": max_sent,
                "chunk_size": 3000,  # Default
            }
        )

    # Different chunk sizes (only for map-reduce)
    for chunk_size in [3000, 5000, 8000]:
        configs.append(
            {
                "name": f"chunk_size_{chunk_size}",
                "max_sentences": 8,
                "chunk_size": chunk_size,
            }
        )

    # Run tests
    results = {
        "file_path": str(file_path),
        "file_size_chars": len(text),
        "configs": [],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    logger.info(f"Running {len(configs)} test configurations...")

    for i, config in enumerate(configs, 1):
        logger.info(f"[{i}/{len(configs)}] Running: {config['name']}")

        # Note: chunk_size is not directly configurable in AdaptiveSummarizer
        # It's set in DI container, but we can still test different max_sentences
        result = await run_summarization_test(
            text=text,
            max_sentences=config["max_sentences"],
            chunk_size=config["chunk_size"],  # For reporting only
            language="ru",
        )

        config_result = {
            "config": config,
            "result": result,
        }
        results["configs"].append(config_result)

        if result["success"]:
            logger.info(
                f"  ✓ Success: method={result['method']}, "
                f"time={result['elapsed_time']:.2f}s, "
                f"sentences={result['sentences_count']}"
            )
        else:
            logger.error(f"  ✗ Failed: {result.get('error', 'unknown')}")

    # Save results
    results_file = output_dir / "stress_test_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Results saved to: {results_file}")

    # Generate report
    report_file = output_dir / "stress_test_report.md"
    generate_report(results, report_file)
    logger.info(f"Report saved to: {report_file}")

    return results


def generate_report(results: dict[str, Any], output_file: Path) -> None:
    """Generate human-readable markdown report.

    Args:
        results: Test results dictionary.
        output_file: Output file path.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Stress Test Report\n\n")
        f.write(f"**File:** `{results['file_path']}`\n")
        f.write(f"**Size:** {results['file_size_chars']:,} characters\n")
        f.write(f"**Timestamp:** {results['timestamp']}\n\n")

        f.write("## Test Results\n\n")

        # Summary statistics
        successful = [r for r in results["configs"] if r["result"]["success"]]
        failed = [r for r in results["configs"] if not r["result"]["success"]]

        f.write(f"**Total Tests:** {len(results['configs'])}\n")
        f.write(f"**Successful:** {len(successful)}\n")
        f.write(f"**Failed:** {len(failed)}\n\n")

        if successful:
            avg_time = sum(r["result"]["elapsed_time"] for r in successful) / len(
                successful
            )
            f.write(f"**Average Time:** {avg_time:.2f}s\n\n")

        # Detailed results
        f.write("### Detailed Results\n\n")
        f.write(
            "| Config | Method | Sentences | Time (s) | Tokens/s | Quality | Status |\n"
        )
        f.write(
            "|--------|--------|-----------|----------|----------|---------|--------|\n"
        )

        for config_result in results["configs"]:
            config = config_result["config"]
            result = config_result["result"]

            if result["success"]:
                f.write(
                    f"| {config['name']} | {result['method']} | "
                    f"{result['sentences_count']} | {result['elapsed_time']:.2f} | "
                    f"{result['tokens_per_second']:.0f} | {result['quality_score']:.2f} | ✅ |\n"
                )
            else:
                f.write(
                    f"| {config['name']} | - | - | - | - | - | ❌ {result.get('error', 'unknown')} |\n"
                )

        # Sample summaries
        f.write("\n### Sample Summaries\n\n")
        for config_result in results["configs"][:3]:  # First 3
            if config_result["result"]["success"]:
                config = config_result["config"]
                result = config_result["result"]
                f.write(f"#### {config['name']}\n\n")
                f.write(f"**Method:** {result['method']}\n\n")
                f.write(f"{result['summary_text'][:500]}...\n\n")


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Stress test summarization system")
    parser.add_argument(
        "--file",
        type=Path,
        default=Path.home()
        / "010000_000060_ART-456646aa-282f-42dd-973e-0d51304b5076-Анна_Каренина.txt",
        help="Path to text file for testing",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for results",
    )

    args = parser.parse_args()

    if not args.file.exists():
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    try:
        results = await run_stress_test(args.file, args.output_dir)

        # Print summary
        successful = sum(1 for r in results["configs"] if r["result"]["success"])
        total = len(results["configs"])

        print(f"\n{'='*60}")
        print(f"Stress Test Complete: {successful}/{total} tests passed")
        print(f"{'='*60}\n")

    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
