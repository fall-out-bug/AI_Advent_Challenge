"""Homework handler for Butler Agent HOMEWORK_REVIEW mode.

Handles homework listing and review requests.
Following Python Zen: Simple is better than complex.
"""

import base64
import logging
import re
import tempfile
from pathlib import Path
from typing import Optional

from src.domain.agents.handlers.handler import Handler
from src.domain.agents.state_machine import DialogContext
from src.domain.interfaces.tool_client import ToolClientProtocol
from src.infrastructure.hw_checker.client import HWCheckerClient

logger = logging.getLogger(__name__)


def _escape_markdown(text: str) -> str:
    """Escape Markdown special characters.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for Telegram Markdown parsing
    """
    if not text:
        return ""
    text = str(text)
    text = text.replace("*", "")
    text = text.replace("_", "\\_")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("(", "\\(")
    text = text.replace(")", "\\)")
    text = text.replace("`", "\\`")
    return text


class HomeworkHandler(Handler):
    """Handler for HOMEWORK_REVIEW mode - homework listing and review.

    Handles commands:
    - "Покажи домашки" - list recent commits
    - "Сделай ревью {commit_hash}" - review homework archive

    Following SOLID: Single Responsibility Principle.
    """

    def __init__(
        self,
        hw_checker_client: HWCheckerClient,
        tool_client: ToolClientProtocol,
    ):
        """Initialize homework handler.

        Args:
            hw_checker_client: HW Checker API client
            tool_client: MCP tool client for review operations
        """
        self.hw_checker_client = hw_checker_client
        self.tool_client = tool_client

    async def handle(self, context: DialogContext, message: str) -> str:
        """Handle homework review request.

        Args:
            context: Dialog context with state and data
            message: User message text

        Returns:
            Response text or special format for file sending
        """
        message_lower = message.lower()

        # Check for "покажи домашки" command (list commits)
        # More specific patterns first
        list_keywords = [
            "покажи домашки",
            "покажи домашк",
            "покажи домашние работы",
            "show homework",
            "homework list",
            "список домашек",
            "список домашних работ",
            "list homework",
            "домашки",  # Simple keyword
            "homework",  # Simple keyword
        ]
        if any(keyword in message_lower for keyword in list_keywords):
            return await self._list_homeworks(context, message)

        # Check for review command
        commit_hash = self._parse_commit_hash_from_message(message)
        if commit_hash:
            return await self._review_homework(context, commit_hash)

        return "❌ Не понял команду. Используйте:\n- Покажи домашки\n- Сделай ревью {commit_hash}"

    def _parse_commit_hash_from_message(self, message: str) -> Optional[str]:
        """Parse commit hash from message.

        Args:
            message: User message text

        Returns:
            Commit hash or None
        """
        # Patterns: "сделай ревью abc123", "review abc123", "ревью abc123"
        # Support full-length commit hashes (up to 64 characters for SHA-256)
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

    async def _list_homeworks(self, context: DialogContext, message: str) -> str:
        """List recent homework commits.

        Args:
            context: Dialog context
            message: User message (may contain days parameter)

        Returns:
            Formatted list of homeworks
        """
        if not self.hw_checker_client:
            return "❌ HW Checker client не настроен."

        try:
            # Parse days from message (default: 1)
            days = self._parse_days_from_message(message)

            result = await self.hw_checker_client.get_recent_commits(days=days)
            commits = result.get("commits", [])
            total = result.get("total", 0)

            if not commits:
                return f"📚 Нет домашних работ за последние {days} дней.\n\nИспользуйте команду 'Сделай ревью {commit_hash}' для ревью конкретного коммита."

            lines = [f"📚 Домашки за последние {days} дней\n"]

            for commit in commits:
                commit_hash = commit.get("commit_hash", "N/A")
                archive_name = commit.get("archive_name", "N/A")
                assignment = commit.get("assignment", "N/A")
                commit_dttm = commit.get("commit_dttm", "")
                status = commit.get("status", "")

                # Status emoji
                status_emoji = {
                    "passed": "✅",
                    "failed": "❌",
                    "running": "🔄",
                    "queued": "⏳",
                    "error": "⚠️",
                    "timeout": "⏱️",
                }.get(status, "📌")

                # Escape markdown
                safe_archive = _escape_markdown(archive_name)
                safe_assignment = _escape_markdown(assignment)
                safe_hash = _escape_markdown(
                    commit_hash
                )  # Full commit hash, not truncated

                lines.append(f"{status_emoji} {safe_assignment}: {safe_archive}")
                lines.append(f"   Коммит: {safe_hash}")
                if commit_dttm:
                    lines.append(f"   Дата: {commit_dttm}")
                if status:
                    lines.append(f"   Статус: {status}")
                lines.append("")

            if total > len(commits):
                lines.append(f"... и еще {total - len(commits)} домашних работ")

            return "\n".join(lines)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to list homeworks: {error_msg}", exc_info=True)

            if "connection" in error_msg.lower() or "failed" in error_msg.lower():
                return "❌ Не удалось подключиться к серверу проверки домашних работ."
            return f"❌ Ошибка при получении списка домашних работ: {error_msg[:100]}"

    def _parse_days_from_message(self, message: str) -> int:
        """Parse number of days from message.

        Args:
            message: User message text

        Returns:
            Number of days (default: 1)
        """
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

    async def _review_homework(self, context: DialogContext, commit_hash: str) -> str:
        """Review homework by commit hash.

        Args:
            context: Dialog context
            commit_hash: Git commit hash

        Returns:
            Special format string for file sending or error message
        """
        if not self.hw_checker_client:
            return "❌ HW Checker client не настроен."

        try:
            # Download archive
            logger.info(
                f"Downloading archive for commit {commit_hash[:20]}... (full length: {len(commit_hash)})"
            )
            archive_bytes = await self.hw_checker_client.download_archive(commit_hash)

            # Save to shared temp directory (accessible by both butler-bot and mcp-server)
            # Use /app/archive if available (shared volume), otherwise fallback to /tmp
            import os

            shared_temp_dir = "/app/archive"
            if os.path.exists(shared_temp_dir):
                temp_dir = shared_temp_dir
            else:
                temp_dir = tempfile.gettempdir()

            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".zip", prefix="homework_review_", dir=temp_dir
            )
            temp_file.write(archive_bytes)
            temp_path = temp_file.name
            temp_file.close()

            logger.info(
                f"Saved archive to {temp_path} (size: {len(archive_bytes)} bytes)"
            )

            try:
                # Call review tool
                logger.info(f"Starting review for commit {commit_hash}")
                result = await self.tool_client.call_tool(
                    "review_homework_archive",
                    {
                        "archive_path": temp_path,
                        "assignment_type": "auto",
                        "token_budget": 8000,
                        "model_name": "mistral",
                    },
                )

                # Extract markdown report
                markdown_report = result.get("markdown_report", "")

                # Log result info for debugging
                logger.info(
                    f"Review completed: success={result.get('success')}, "
                    f"total_findings={result.get('total_findings')}, "
                    f"markdown_length={len(markdown_report) if markdown_report else 0}"
                )

                # Check if markdown_report is empty or whitespace-only
                if not markdown_report or not markdown_report.strip():
                    # If no report, try to provide helpful error message
                    total_findings = result.get("total_findings", 0)
                    success = result.get("success", False)
                    if not success:
                        return f"❌ Ошибка при выполнении ревью. Проверьте логи сервера."
                    if total_findings == 0:
                        return (
                            f"✅ Ревью выполнено успешно, но не найдено проблем.\n\n"
                            f"Статистика:\n"
                            f"- Компонентов обнаружено: {len(result.get('detected_components', []))}\n"
                            f"- Найдено проблем: 0\n"
                            f"- Время выполнения: {result.get('execution_time_seconds', 0):.2f} сек\n\n"
                            f"Архив обработан, но код не содержит критических проблем."
                        )
                    return "❌ Ревью не вернуло отчет. Попробуйте позже."

                # Return special format for file sending
                # Format: "FILE:<filename>:<base64_content>"
                filename = f"review_{commit_hash[:12]}.md"
                content_b64 = base64.b64encode(markdown_report.encode("utf-8")).decode(
                    "ascii"
                )
                logger.info(
                    f"Sending markdown report as file: {filename} ({len(markdown_report)} chars)"
                )
                return f"FILE:{filename}:{content_b64}"

            finally:
                # Cleanup temp file
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_path}: {e}")

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Failed to review homework {commit_hash}: {error_msg}", exc_info=True
            )

            # Check for HTTP 404 specifically
            if "404" in error_msg or "not found" in error_msg.lower():
                return (
                    f"❌ Архив с коммитом {commit_hash} не найден на сервере.\n\n"
                    f"Возможные причины:\n"
                    f"• Коммит еще не обработан\n"
                    f"• Коммит не содержит архива домашней работы\n"
                    f"• Проверьте правильность хеша коммита"
                )
            if (
                "connection" in error_msg.lower()
                or "connection error" in error_msg.lower()
            ):
                return f"❌ Не удалось подключиться к серверу проверки домашних работ. Проверьте доступность серверов."
            if "timeout" in error_msg.lower():
                return (
                    f"❌ Превышено время ожидания ответа от сервера. Попробуйте позже."
                )
            return f"❌ Ошибка при ревью домашней работы: {error_msg[:150]}"
