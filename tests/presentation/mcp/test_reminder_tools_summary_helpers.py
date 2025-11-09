from datetime import datetime, timezone

import pytest

from src.presentation.mcp.tools._summary_helpers import (
    _build_summary_query,
    _compute_task_stats,
)

pytestmark = pytest.mark.skip(
    reason=(
        "Reminder summary helpers scheduled for archival after Stage 02_01; "
        "see EP04 coordination plan."
    )
)


def test_build_summary_query_today_and_tomorrow() -> None:
    now = datetime(2025, 1, 2, 10, 0, 0, tzinfo=timezone.utc)

    q_today = _build_summary_query(user_id=42, timeframe="today", now=now)
    assert q_today["user_id"] == 42
    assert "deadline" in q_today
    assert q_today["deadline"]["$gte"].startswith("2025-01-02")
    assert q_today["deadline"]["$lt"].startswith("2025-01-03")

    q_tomorrow = _build_summary_query(user_id=42, timeframe="tomorrow", now=now)
    assert q_tomorrow["deadline"]["$gte"].startswith("2025-01-03")
    assert q_tomorrow["deadline"]["$lt"].startswith("2025-01-04")


def test_compute_task_stats_counts_completed_overdue_and_priority() -> None:
    now_iso = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc).isoformat()

    tasks = [
        {
            "completed": True,
            "deadline": "2025-01-02T10:00:00+00:00",
            "priority": "high",
        },
        {
            "completed": False,
            "deadline": "2025-01-03T10:00:00+00:00",
            "priority": "medium",
        },
        {
            "completed": False,
            "deadline": "2025-01-01T10:00:00+00:00",
            "priority": "high",
        },
    ]

    stats = _compute_task_stats(tasks, now_iso)
    assert stats["total"] == 3
    assert stats["completed"] == 1
    assert stats["overdue"] == 1
    assert stats["high_priority"] == 2
