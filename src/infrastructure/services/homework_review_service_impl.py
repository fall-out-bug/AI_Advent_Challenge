"""Infrastructure implementation of HomeworkReviewService.

Provides concrete implementation using HW Checker client and review tools.
Following Clean Architecture: Infrastructure layer implements domain interfaces.

Epic 21 · Stage 21_01b · Homework Review Service
"""

# noqa: E501
import base64
import logging
from pathlib import Path
from typing import Any, Dict

# noqa: E501
from src.domain.agents.state_machine import DialogContext
from src.domain.interfaces.homework_checker import HomeworkCheckerProtocol
from src.domain.interfaces.homework_review_service import (
    HomeworkReviewError,
    HomeworkReviewService,
)
from src.domain.interfaces.storage_service import StorageService
from src.domain.interfaces.tool_client import ToolClientProtocol

# noqa: E501
logger = logging.getLogger(__name__)


# noqa: E501
# noqa: E501
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
    text = text.replace("`", "\\`")
    return text


# noqa: E501
# noqa: E501
class HomeworkReviewServiceImpl(HomeworkReviewService):
    """Infrastructure implementation of HomeworkReviewService.

    Purpose:
        Provides concrete homework review functionality using
        HW Checker API for data and review tools for analysis.

    Attributes:
        hw_checker: Protocol for accessing homework submissions.
        tool_client: Protocol for executing review tools.
    """

    def __init__(
        self,
        hw_checker: HomeworkCheckerProtocol,
        tool_client: ToolClientProtocol,
        storage_service: StorageService,
    ):
        """Initialize homework review service.

        Args:
            hw_checker: Homework checker protocol implementation.
            tool_client: Tool client protocol implementation.
            storage_service: Secure storage service for temp files.
        """
        self.hw_checker = hw_checker
        self.tool_client = tool_client
        self.storage_service = storage_service

    async def list_homeworks(self, days: int) -> Dict[str, Any]:
        """List recent homework submissions.

        Args:
            days: Number of days to look back.

        Returns:
            Dictionary with 'total' and 'commits' keys.

        Raises:
            HomeworkReviewError: If listing operation fails.
        """
        try:
            return await self.hw_checker.get_recent_commits(days=days)
        except Exception as e:
            logger.error(f"Failed to list homeworks: {e}", exc_info=True)
            raise HomeworkReviewError(f"Failed to list homeworks: {e}") from e

    async def review_homework(self, context: DialogContext, commit_hash: str) -> str:
        """Review homework by commit hash.

        Args:
            context: Dialog context with state and data.
            commit_hash: Git commit hash to review.

        Returns:
            Special format string for file sending or error message.

        Raises:
            HomeworkReviewError: If review operation fails.
        """
        try:
            # Download archive
            logger.info(
                f"Downloading archive for commit {commit_hash[:20]}... (full length: {len(commit_hash)})"
            )
            archive_bytes = await self.hw_checker.download_archive(commit_hash)

            # Create secure temp file using storage service
            temp_file = self.storage_service.create_temp_file(
                suffix=".zip",
                prefix="homework_review_",
                content=archive_bytes,
            )
            temp_path = Path(temp_file.name)
            archive_size = len(archive_bytes)

            logger.info(f"Saved archive to {temp_path} (size: {archive_size} bytes)")

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
                        return "❌ Ошибка при выполнении ревью. Проверьте логи сервера."
                    if total_findings == 0:
                        components_count = len(result.get("detected_components", []))
                        exec_time = result.get("execution_time_seconds", 0)
                        return (
                            "✅ Ревью выполнено успешно, но не найдено проблем.\n\n"
                            "Статистика:\n"
                            f"- Компонентов обнаружено: {components_count}\n"
                            "- Найдено проблем: 0\n"
                            f"- Время выполнения: {exec_time:.2f} сек\n\n"
                            "Архив обработан, но код не содержит критических проблем."
                        )
                    return "❌ Ревью не вернуло отчет. Попробуйте позже."

                # Return special format for file sending
                filename = f"review_{commit_hash[:12]}.md"
                content_b64 = base64.b64encode(markdown_report.encode("utf-8")).decode(
                    "ascii"
                )
                report_len = len(markdown_report)
                logger.info(
                    f"Sending markdown report as file: {filename} ({report_len} chars)"
                )
                return f"FILE:{filename}:{content_b64}"

            finally:
                # Cleanup temp file using storage service
                try:
                    temp_file.close()  # Close file handle first
                    self.storage_service.cleanup_temp_file(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {str(temp_path)}: {e}")

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Failed to review homework {commit_hash}: {error_msg}",
                exc_info=True,
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
                return "❌ Не удалось подключиться к серверу проверки домашних работ. Проверьте доступность серверов."
            if "timeout" in error_msg.lower():
                return "❌ Превышено время ожидания ответа от сервера. Попробуйте позже."
            return f"❌ Ошибка при ревью домашней работы: {error_msg[:150]}"
