#!/usr/bin/env python3
"""Export RU channel digest benchmarks to JSONL datasets."""

from __future__ import annotations

import argparse
import asyncio
import json
<<<<<<< HEAD
=======
import time
>>>>>>> origin/master
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.config.settings import get_settings

<<<<<<< HEAD
=======
try:
    from src.infrastructure.metrics.observability_metrics import (
        benchmark_export_duration_seconds,
    )
except Exception:  # pragma: no cover - metrics optional
    benchmark_export_duration_seconds = None

>>>>>>> origin/master

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export digest benchmarks.")
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
        help="Time window in hours to sample digests.",
    )
    parser.add_argument(
        "--channel",
        help="Optional Telegram channel username filter.",
    )
    parser.add_argument(
        "--language",
        default="ru",
        help="Language filter (default: ru).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum digests to export.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output JSONL file path.",
    )
    return parser.parse_args()


async def fetch_digests(args: argparse.Namespace) -> Iterable[dict[str, Any]]:
    """Query MongoDB for digests within the specified window."""

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
    collection = db["digests"]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    query: dict[str, Any] = {
        "created_at": {"$gte": cutoff},
    }
    if args.language and args.language.lower() not in {"any", "all"}:
        query["language"] = args.language
    if args.channel:
        query["channel"] = args.channel

    cursor = (
        collection.find(query)
        .sort("created_at", -1)
        .limit(max(args.limit, 0) or 0)
    )
    results: list[dict[str, Any]] = []
    async for document in cursor:
        results.append(document)
    client.close()
    return results


def build_source_text(posts: Iterable[dict[str, Any]]) -> str:
    """Render concatenated source text for benchmark evaluation."""

    parts: list[str] = []
    for post in posts:
        title = post.get("title")
        summary = post.get("summary")
        text = post.get("text") or post.get("content") or post.get("message")
        bullet = []
        if title:
            bullet.append(str(title).strip())
        if summary:
            bullet.append(str(summary).strip())
        if text:
            bullet.append(str(text).strip())
        if bullet:
            parts.append(" ".join(bullet))
    return "\n".join(parts)


def normalise_digest(document: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Convert raw digest document into benchmark dataset record."""

    posts = document.get("posts") or document.get("items") or []
    feature_flags = document.get("feature_flags") or document.get("metadata", {}).get(
        "feature_flags", {}
    )
    ground_truth = document.get("quality") or document.get("ground_truth")
    llm_judge = ground_truth.get("llm_judge") if isinstance(ground_truth, dict) else {}

    timestamp = document.get("created_at")
    if isinstance(timestamp, datetime):
        timestamp_str = timestamp.isoformat()
    elif timestamp is not None:
        timestamp_str = str(timestamp)
    else:
        timestamp_str = None

    summary = (
        document.get("summary_markdown")
        or document.get("summary")
        or document.get("digest")
        or ""
    )
    source_text = build_source_text(posts)
    if not source_text:
        raw_posts = document.get("posts_text") or document.get("raw_posts")
        if isinstance(raw_posts, list):
            source_text = "\n".join(str(item).strip() for item in raw_posts if item)
        elif isinstance(raw_posts, str):
            source_text = raw_posts.strip()

    dataset_record: dict[str, Any] = {
        "sample_id": str(document.get("digest_id") or document.get("_id")),
        "channel": document.get("channel"),
        "language": document.get("language", args.language),
        "timestamp": timestamp_str,
        "source_text": source_text,
        "summary_markdown": summary,
        "metadata": {
            "posts_count": len(posts),
            "time_range_hours": document.get("time_range_hours", args.hours),
            "llm_model": document.get("llm_model")
            or document.get("metadata", {}).get("llm_model"),
            "feature_flags": feature_flags,
        },
        "ground_truth": {"llm_judge": llm_judge} if llm_judge else {},
    }
    latency = (
        document.get("latency_seconds")
        or document.get("metrics", {}).get("latency_seconds")
    )
    if latency is not None:
        dataset_record["latency_seconds"] = float(latency)
    return dataset_record


def write_output(output_path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Persist dataset records to JSONL file."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


async def main_async() -> None:
    args = parse_args()
    documents = await fetch_digests(args)
    if not documents:
        raise RuntimeError("No digests found for the specified filters.")
    records = [normalise_digest(doc, args) for doc in documents]
    write_output(args.output, records)
    print(
        f"Exported {len(records)} digest samples to {args.output}",
        flush=True,
    )


def main() -> None:
<<<<<<< HEAD
    try:
        asyncio.run(main_async())
    except Exception as exc:  # pragma: no cover - CLI error path
=======
    start_time = time.perf_counter()
    exporter_name = "digests"
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
>>>>>>> origin/master
        raise SystemExit(f"Export failed: {exc}") from exc


if __name__ == "__main__":
    main()
