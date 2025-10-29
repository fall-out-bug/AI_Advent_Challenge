import pytest
from datetime import datetime, time


def test_format_summary_empty():
    from src.workers.summary_worker import SummaryWorker

    text = SummaryWorker._format_summary([], {})
    assert "Good morning" in text


def test_format_summary_with_tasks():
    from src.workers.summary_worker import SummaryWorker

    tasks = [{"title": "Task 1", "priority": "high"}]
    stats = {"total": 1, "high_priority": 1}
    text = SummaryWorker._format_summary(tasks, stats)
    assert "Task 1" in text
    assert "🔴" in text


def test_parse_time_valid():
    from src.workers.summary_worker import SummaryWorker

    t = SummaryWorker._parse_time("09:00")
    assert t == time(9, 0)


def test_parse_time_invalid():
    from src.workers.summary_worker import SummaryWorker

    t = SummaryWorker._parse_time("invalid")
    assert t is None

