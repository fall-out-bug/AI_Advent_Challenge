from src.infrastructure.formatters.telegram_formatter import TelegramFormatter
from src.domain.value_objects.task_summary import TaskSummary, DigestMessage, DigestItem
import pytest


def test_format_task_summary_basic() -> None:
    fmt = TelegramFormatter()
    txt = fmt.format_task_summary(
        TaskSummary(total=5, completed=2, overdue=1, high_priority=1, timeframe="today")
    )
    assert "Summary (today)" in txt
    assert "Total: 5" in txt
    assert "Completed: 2" in txt
    assert "Overdue: 1" in txt


def test_format_digest_top_items() -> None:
    fmt = TelegramFormatter()
    digest = DigestMessage(
        items=[DigestItem(channel="news", summary="top", post_count=3)]
    )
    txt = fmt.format_digest(digest)
    assert "📰 news: top" in txt


def test_task_summary_validation_prevents_exceeding() -> None:
    with pytest.raises(ValueError):
        TaskSummary(total=1, completed=2, overdue=0, high_priority=0)
