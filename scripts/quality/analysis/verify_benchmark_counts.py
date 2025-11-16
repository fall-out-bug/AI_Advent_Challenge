#!/usr/bin/env python3
"""Verify Stage 05 benchmark dataset coverage for EP23."""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from pymongo import MongoClient


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that benchmark digests/review reports meet Stage 05 requirements."
    )
    parser.add_argument(
        "--channels",
        required=True,
        help="Comma-separated list of Telegram channel usernames (e.g. @a,@b,@c).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Rolling window (days) for required counts (default: 30).",
    )
    parser.add_argument(
        "--minimum",
        type=int,
        default=30,
        help="Minimum documents per channel (default: 30).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write JSON report. Defaults to data/benchmarks/snapshots/<date>/dataset_audit.json",
    )
    parser.add_argument(
        "--mongodb-url",
        dest="mongodb_url",
        default=os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
        help="MongoDB connection URI (defaults to $MONGODB_URL or localhost).",
    )
    return parser.parse_args()


@dataclass
class ChannelStats:
    channel: str
    digests: int
    review_reports: int
    digests_ok: bool
    reviews_ok: bool


def _fetch_counts(
    client: MongoClient, channels: Sequence[str], days: int, minimum: int
) -> list[ChannelStats]:
    db_name = os.getenv("DB_NAME", "butler")
    db = client[db_name]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    digest_counts = defaultdict(int)
    review_counts = defaultdict(int)

    pipeline = [
        {"$match": {"channel": {"$in": channels}, "created_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$channel", "count": {"$sum": 1}}},
    ]
    for doc in db.digests.aggregate(pipeline):
        digest_counts[doc["_id"]] = doc["count"]

    review_pipeline = [
        {
            "$match": {
                "assignment_id": {"$in": channels},
                "created_at": {"$gte": cutoff},
            }
        },
        {"$group": {"_id": "$assignment_id", "count": {"$sum": 1}}},
    ]

    for doc in db.review_reports.aggregate(review_pipeline):
        review_counts[doc["_id"]] = doc["count"]

    stats: list[ChannelStats] = []
    for channel in channels:
        digests = digest_counts.get(channel, 0)
        reviews = review_counts.get(channel, 0)
        stats.append(
            ChannelStats(
                channel=channel,
                digests=digests,
                review_reports=reviews,
                digests_ok=digests >= minimum,
                reviews_ok=reviews >= minimum,
            )
        )
    return stats


def _validate_documents(
    client: MongoClient, channels: Sequence[str], days: int
) -> dict[str, dict[str, int]]:
    db_name = os.getenv("DB_NAME", "butler")
    db = client[db_name]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    issues: dict[str, dict[str, int]] = {}

    for channel in channels:
        issues[channel] = {
            "digests_missing_fields": 0,
            "review_missing_fields": 0,
        }
        cursor = db.digests.find({"channel": channel, "created_at": {"$gte": cutoff}})
        for doc in cursor:
            if not all(
                key in doc
                for key in (
                    "summary_markdown",
                    "posts",
                    "feature_flags",
                    "created_at",
                )
            ):
                issues[channel]["digests_missing_fields"] += 1
        cursor = db.review_reports.find(
            {"assignment_id": channel, "created_at": {"$gte": cutoff}}
        )
        for doc in cursor:
            report = doc.get("report", {})
            passes = report.get("passes", [])
            if not passes or "synthesis" not in report:
                issues[channel]["review_missing_fields"] += 1
    return issues


def _default_output_path(base: Path) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folder = base / "benchmarks" / "snapshots" / today
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "dataset_audit.json"


if __name__ == "__main__":
    args = _parse_args()
    if not args.channels:
        raise SystemExit("No channels provided.")
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]
    client = MongoClient(args.mongodb_url)
    try:
        stats = _fetch_counts(client, channels, args.days, args.minimum)
        issues = _validate_documents(client, channels, args.days)
    finally:
        client.close()

    report_path = args.output or _default_output_path(Path("data"))
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "days_window": args.days,
        "minimum_required": args.minimum,
        "channels": [
            {
                "channel": s.channel,
                "digests": s.digests,
                "review_reports": s.review_reports,
                "digests_ok": s.digests_ok,
                "review_reports_ok": s.reviews_ok,
                **issues[s.channel],
            }
            for s in stats
        ],
    }
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))

