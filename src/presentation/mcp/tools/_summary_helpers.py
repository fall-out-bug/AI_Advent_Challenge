from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict


def _build_summary_query(user_id: int, timeframe: str, now: datetime) -> Dict[str, Any]:
    """Build Mongo query for summary based on timeframe.

    Purpose:
        Constructs MongoDB query filter for task summary queries based on
        timeframe selection (today, tomorrow, week, last_24h, last_7d).

    Args:
        user_id: Telegram user ID (must be > 0)
        timeframe: Time period selector - "today"|"tomorrow"|"week"|"last_24h"|"last_7d"
        now: Current datetime (timezone-aware UTC)

    Returns:
        MongoDB query dict with user_id and optional deadline filter.
        For "last_24h", returns empty query (filters applied in memory).

    Example:
        >>> query = _build_summary_query(123, "today", datetime.now(timezone.utc))
        >>> assert "user_id" in query
        >>> assert "deadline" in query
    """
    query: Dict[str, Any] = {"user_id": int(user_id)}

    if timeframe == "today":
        start_dt = datetime(now.year, now.month, now.day, 0, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=1)
        query["deadline"] = {"$gte": start_dt.isoformat(), "$lt": end_dt.isoformat()}
    elif timeframe == "tomorrow":
        start_dt = datetime(now.year, now.month, now.day, 0, 0, 0, 0, tzinfo=timezone.utc) + timedelta(days=1)
        end_dt = start_dt + timedelta(days=1)
        query["deadline"] = {"$gte": start_dt.isoformat(), "$lt": end_dt.isoformat()}
    elif timeframe == "week":
        start_dt = datetime(now.year, now.month, now.day, 0, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=7)
        query["deadline"] = {"$gte": start_dt.isoformat(), "$lt": end_dt.isoformat()}
    elif timeframe == "last_7d":
        start = (now - timedelta(days=7)).isoformat()
        end = now.isoformat()
        query["deadline"] = {"$gte": start, "$lt": end}
    elif timeframe == "last_24h":
        pass
    else:
        pass

    return query


def _compute_task_stats(tasks: list[dict], now_iso: str) -> Dict[str, int]:
    """Compute basic stats from tasks using string deadline comparison.

    Purpose:
        Calculates aggregate statistics (total, completed, overdue, high_priority)
        from a list of task dictionaries. Uses string-based ISO datetime comparison
        to avoid timezone conversion issues.

    Args:
        tasks: List of task dicts (each with 'completed', 'deadline', 'priority' keys)
        now_iso: Current time as ISO string (e.g., "2025-01-01T12:00:00+00:00")

    Returns:
        Dict with keys: total, completed, overdue, high_priority (all ints)

    Example:
        >>> tasks = [
        ...     {"completed": True, "deadline": "2025-01-02T10:00:00+00:00", "priority": "high"},
        ...     {"completed": False, "deadline": "2025-01-01T10:00:00+00:00", "priority": "medium"},
        ... ]
        >>> stats = _compute_task_stats(tasks, "2025-01-02T12:00:00+00:00")
        >>> assert stats["total"] == 2
        >>> assert stats["completed"] == 1
    """
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed"))

    overdue = 0
    for t in tasks:
        deadline_str = t.get("deadline")
        if deadline_str and isinstance(deadline_str, str) and not t.get("completed"):
            if deadline_str.replace("Z", "+00:00") < now_iso:
                overdue += 1

    high_priority = sum(1 for t in tasks if t.get("priority") == "high")

    return {
        "total": total,
        "completed": completed,
        "overdue": overdue,
        "high_priority": high_priority,
    }
