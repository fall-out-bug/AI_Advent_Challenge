from __future__ import annotations

from typing import List

from src.domain.value_objects.task_summary import DigestMessage, TaskSummary


class TelegramFormatter:
    """Format domain value objects into Telegram-friendly text messages."""

    def format_task_summary(self, summary: TaskSummary) -> str:
        timeframe = f" ({summary.timeframe})" if summary.timeframe else ""
        return (
            f"📋 Summary{timeframe}\n\n"
            f"Total: {summary.total}\n"
            f"Completed: {summary.completed}\n"
            f"Overdue: {summary.overdue}\n"
            f"High priority: {summary.high_priority}"
        )

    def format_digest(self, digest: DigestMessage) -> str:
        if not digest.items:
            return "📰 No digests available yet."
        lines: List[str] = []
        for item in digest.items[:5]:
            lines.append(f"📰 {item.channel}: {item.summary}")
        return "\n".join(lines)
