from datetime import time

from src.workers.formatters import format_summary
from src.workers.summary_worker import SummaryWorker


def test_format_summary_empty():
    text = format_summary([], {})
    assert "Good morning" in text


def test_format_summary_with_tasks():
    tasks = [{"title": "Task 1", "priority": "high"}]
    stats = {"total": 1, "high_priority": 1}
    text = format_summary(tasks, stats)
    assert "Task 1" in text
    assert "🔴" in text


def test_parse_time_valid():
    t = SummaryWorker._parse_time("09:00")
    assert t == time(9, 0)


def test_parse_time_invalid():
    t = SummaryWorker._parse_time("invalid")
    assert t is None
