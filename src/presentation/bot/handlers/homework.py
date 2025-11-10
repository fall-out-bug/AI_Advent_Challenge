"""Homework handler for Butler bot HOMEWORK_REVIEW mode."""

from __future__ import annotations

import base64
import logging
import re
from typing import Iterable, Optional

from src.application.dtos.butler_dialog_dtos import DialogContext
from src.application.dtos.homework_dtos import (
    HomeworkListResult,
    HomeworkReviewResult,
    HomeworkSubmission,
)
from src.application.use_cases.list_homework_submissions import (
    ListHomeworkSubmissionsUseCase,
)
from src.application.use_cases.review_homework_use_case import ReviewHomeworkUseCase
from src.presentation.bot.handlers.base import Handler

logger = logging.getLogger(__name__)


def _escape_markdown(text: str) -> str:
    """Escape Telegram Markdown special characters."""
    if not text:
        return ""
    value = str(text)
    return (
        value.replace("*", "")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("`", "\\`")
    )


class HomeworkHandler(Handler):
    """Handle homework listing and review commands."""

    def __init__(
        self,
        list_use_case: ListHomeworkSubmissionsUseCase,
        review_use_case: ReviewHomeworkUseCase,
    ) -> None:
        """Initialize handler with required use cases."""
        self._list_use_case = list_use_case
        self._review_use_case = review_use_case

    async def handle(self, context: DialogContext, message: str) -> str:
        """Route message to list or review homework workflows."""
        message_lower = message.lower()
        if self._is_list_request(message_lower):
            days = self._parse_days_from_message(message)
            return await self._handle_list(days)

        commit_hash = self._parse_commit_hash_from_message(message)
        if commit_hash:
            return await self._handle_review(commit_hash)

        return (
            "❌ Не понял команду. Используйте:\n"
            "- Покажи домашки\n"
            "- Сделай ревью {commit_hash}"
        )

    async def _handle_list(self, days: int) -> str:
        """Execute list use case and format output."""
        try:
            result = await self._list_use_case.execute(days=days)
            return self._format_list_response(days, result)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to list homeworks: %s", exc, exc_info=True)
            return "❌ Ошибка при получении списка домашних работ."

    async def _handle_review(self, commit_hash: str) -> str:
        """Execute review use case and format response."""
        try:
            result = await self._review_use_case.execute(commit_hash=commit_hash)
            return self._format_review_response(commit_hash, result)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to review homework %s: %s", commit_hash, exc, exc_info=True)
            return f"❌ Ошибка при ревью домашней работы: {str(exc)[:120]}"

    def _format_list_response(self, days: int, result: HomeworkListResult) -> str:
        """Build markdown list output."""
        if not result.submissions:
            return self._format_empty_list(days)

        lines: list[str] = [f"📚 Домашки за последние {days} дней\n"]
        for submission in result.submissions:
            lines.extend(self._format_submission(submission))

        extra = result.total - len(result.submissions)
        if extra > 0:
            lines.append(f"... и еще {extra} домашних работ")

        return "\n".join(lines)

    def _format_empty_list(self, days: int) -> str:
        """Return fallback message when no submissions found."""
        return (
            f"📚 Нет домашних работ за последние {days} дней.\n\n"
            "Используйте команду 'Сделай ревью {commit_hash}' для ревью конкретного коммита."
        )

    def _format_submission(self, submission: HomeworkSubmission) -> list[str]:
        """Format single homework submission entry."""
        status_emoji = self._status_emoji(submission.status)
        safe_archive = _escape_markdown(submission.archive_name)
        safe_assignment = _escape_markdown(submission.assignment)
        safe_hash = _escape_markdown(submission.commit_hash)

        header = (
            f"{status_emoji} {safe_assignment}: {safe_archive}"
            if safe_assignment
            else f"{status_emoji} {safe_archive}"
        )

        lines = [header, f"   Коммит: {safe_hash}"]
        if submission.commit_dttm:
            lines.append(f"   Дата: {submission.commit_dttm}")
        if submission.status:
            lines.append(f"   Статус: {submission.status}")
        lines.append("")
        return lines

    def _format_review_response(
        self, commit_hash: str, result: HomeworkReviewResult
    ) -> str:
        """Build file payload with markdown report."""
        markdown = result.markdown_report or ""
        if not markdown.strip():
            return (
                "✅ Ревью выполнено успешно, но отчет пуст.\n"
                "Проверьте логи сервера для подробностей."
            )
        filename = f"review_{commit_hash[:12]}.md"
        encoded = base64.b64encode(markdown.encode("utf-8")).decode("ascii")
        return f"FILE:{filename}:{encoded}"

    def _is_list_request(self, message_lower: str) -> bool:
        """Return True if message requests homework list."""
        list_keywords = [
            "покажи домашки",
            "покажи домашк",
            "покажи домашние работы",
            "show homework",
            "homework list",
            "список домашек",
            "список домашних работ",
            "list homework",
            "домашки",
            "homework",
        ]
        return any(keyword in message_lower for keyword in list_keywords)

    def _parse_commit_hash_from_message(self, message: str) -> Optional[str]:
        """Extract commit hash from message."""
        patterns = [
            r"(?:сделай|do|make)\s+ревью\s+([a-f0-9]{7,64})",
            r"ревью\s+([a-f0-9]{7,64})",
            r"review\s+([a-f0-9]{7,64})",
            r"проверь\s+коммит\s+([a-f0-9]{7,64})",
            r"check\s+commit\s+([a-f0-9]{7,64})",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _parse_days_from_message(self, message: str) -> int:
        """Extract number of days from message."""
        message_lower = message.lower()
        patterns = [
            (r"за\s+(\d+)\s+дн", 1),
            (r"(\d+)\s+дн", 1),
            (r"за\s+(\d+)\s+день", 1),
            (r"(\d+)\s+день", 1),
            (r"for\s+(\d+)\s+days?", 1),
            (r"(\d+)\s+days?", 1),
        ]
        for pattern, multiplier in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return int(match.group(1)) * multiplier
        return 1

    def _status_emoji(self, status: str) -> str:
        """Return emoji for status string."""
        mapping = {
            "passed": "✅",
            "failed": "❌",
            "running": "🔄",
            "queued": "⏳",
            "error": "⚠️",
            "timeout": "⏱️",
        }
        return mapping.get(status, "📌")
