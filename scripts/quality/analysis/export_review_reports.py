#!/usr/bin/env python3
"""Export modular reviewer synthesis outputs for benchmarking."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.config.settings import get_settings

try:
    from src.infrastructure.metrics.observability_metrics import (
        benchmark_export_duration_seconds,
    )
except Exception:  # pragma: no cover - metrics optional
    benchmark_export_duration_seconds = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export reviewer benchmarks.")
    parser.add_argument(
        "--mongo",
        required=False,
        help="MongoDB connection URI. Defaults to Settings.mongodb_url.",
    )
    parser.add_argument(
        "--database",
        required=False,
        help="Database name override. Defaults to Settings.db_name.",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Time window in hours to sample review reports.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum review reports to export.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output JSONL file path.",
    )
    return parser.parse_args()


async def fetch_reports(args: argparse.Namespace) -> Iterable[dict[str, Any]]:
    """Fetch review reports within the configured time window."""

    settings = get_settings()
    mongo_uri = args.mongo or settings.mongodb_url
    db_name = args.database or settings.db_name
    client = AsyncIOMotorClient(
        mongo_uri,
        serverSelectionTimeoutMS=settings.mongo_timeout_ms,
        socketTimeoutMS=settings.mongo_timeout_ms,
        connectTimeoutMS=settings.mongo_timeout_ms,
    )
    db = client[db_name]
    collection = db["review_reports"]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)

    cursor = (
        collection.find({"created_at": {"$gte": cutoff}})
        .sort("created_at", -1)
        .limit(max(args.limit, 0) or 0)
    )
    results: list[dict[str, Any]] = []
    async for document in cursor:
        results.append(document)
    client.close()
    return results


def render_source_from_passes(passes: Iterable[dict[str, Any]]) -> str:
    """Concatenate pass findings into a single text blob."""

    segments: list[str] = []
    for index, review_pass in enumerate(passes, start=1):
        pass_name = review_pass.get("pass_name") or review_pass.get("name") or f"pass_{index}"
        summary = review_pass.get("summary") or ""
        recommendations = review_pass.get("recommendations") or []
        findings = review_pass.get("findings") or []
        segment_parts = [f"[{pass_name}] {summary}".strip()]
        for rec in recommendations:
            segment_parts.append(f"Recommendation: {rec}")
        for finding in findings:
            title = finding.get("title") or finding.get("message")
            description = finding.get("description") or finding.get("details")
            if title or description:
                segment_parts.append(f"Finding: {title or ''} {description or ''}".strip())
        join = "\n".join(part for part in segment_parts if part)
        if join:
            segments.append(join)
    return "\n\n".join(segments)


def normalise_report(document: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Normalise modular reviewer document for benchmarking."""

    report = document.get("report") or {}
    passes = report.get("passes") or document.get("passes") or []
    final_summary = (
        report.get("synthesis")
        or report.get("summary_markdown")
        or report.get("summary")
        or ""
    )
    metadata = report.get("metadata") or {}
    llm_judge = metadata.get("llm_judge") or {}

    timestamp = document.get("created_at")
    if isinstance(timestamp, datetime):
        timestamp_str = timestamp.isoformat()
    elif timestamp is not None:
        timestamp_str = str(timestamp)
    else:
        timestamp_str = None

    return {
        "sample_id": str(document.get("report_id") or document.get("_id")),
        "channel": document.get("assignment_id"),
        "language": document.get("language", "ru"),
        "timestamp": timestamp_str,
        "source_text": render_source_from_passes(passes),
        "summary_markdown": final_summary,
        "metadata": {
            "student_id": document.get("student_id"),
            "assignment_id": document.get("assignment_id"),
            "passes_count": len(passes),
            "llm_model": metadata.get("llm_model"),
            "feature_flags": metadata.get("feature_flags") or {},
        },
        "ground_truth": {"llm_judge": llm_judge} if llm_judge else {},
        "latency_seconds": metadata.get("latency_seconds"),
    }


def write_output(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


async def main_async() -> None:
    args = parse_args()
    documents = await fetch_reports(args)
    if not documents:
        raise RuntimeError("No review reports found for the specified filters.")
    records = [normalise_report(doc, args) for doc in documents]
    write_output(args.output, records)
    print(f"Exported {len(records)} review reports to {args.output}", flush=True)


def main() -> None:
    start_time = time.perf_counter()
    exporter_name = "review_reports"
    try:
        asyncio.run(main_async())
        if benchmark_export_duration_seconds:
            benchmark_export_duration_seconds.labels(exporter=exporter_name).observe(
                time.perf_counter() - start_time
            )
    except Exception as exc:  # pragma: no cover - CLI error path
        if benchmark_export_duration_seconds:
            benchmark_export_duration_seconds.labels(exporter=exporter_name).observe(
                time.perf_counter() - start_time
            )
        raise SystemExit(f"Export failed: {exc}") from exc


if __name__ == "__main__":
    main()
