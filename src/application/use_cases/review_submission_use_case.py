"""Use case for reviewing code submissions from archives."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional, cast, Callable

try:
    from shared_package.clients.unified_client import UnifiedModelClient  # type: ignore[import-not-found]
except ImportError:
    try:
        from shared.clients.unified_client import UnifiedModelClient  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(
            "UnifiedModelClient not available. Shared SDK is not installed."
        ) from exc


from multipass_reviewer.application.config import ReviewConfig

from src.application.services.modular_review_service import ModularReviewService
from src.application.services.review_rate_limiter import (
    ReviewRateLimiter,
    ReviewRateLimiterConfig,
    ReviewRateLimitExceeded,
)
from src.domain.interfaces.archive_reader import ArchiveReader
from src.domain.interfaces.log_analyzer import LogAnalyzer
from src.domain.interfaces.log_parser import LogParser
from src.domain.interfaces.review_publisher import ReviewPublisher
from src.domain.interfaces.tool_client import ToolClientProtocol
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.domain.value_objects.long_summarization_task import LongTask
from src.domain.models.code_review_models import MultiPassReport
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.logging.review_logger import ReviewLogger
from src.infrastructure.logs.llm_log_analyzer import LLMLogAnalyzer
from src.infrastructure.logs.log_normalizer import LogNormalizer
from src.infrastructure.logs.log_parser_impl import LogParserImpl
from src.infrastructure.repositories.homework_review_repository import (
    HomeworkReviewRepository,
)
from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _ReviewTaskContext:
    """Aggregated task metadata for review execution."""

    task: LongTask
    new_submission_path: str
    previous_submission_path: Optional[str]
    assignment_id: str
    new_commit: str
    old_commit: Optional[str]
    logs_zip_path: Optional[str]
    student_id: str

    @property
    def repo_name(self) -> str:
        """Return repository identifier for storage."""
        return f"{self.student_id}_{self.assignment_id}"


class ReviewSubmissionUseCase:
    """Use case for reviewing code submissions from archives.

    Purpose:
        Orchestrates the complete review process using the reusable modular reviewer:
        extracts archives, analyzes diff, runs modular multi-pass review, saves results,
        and publishes to external API.

    Args:
        archive_reader: Archive extraction service
        diff_analyzer: Code diff analyzer
        unified_client: UnifiedModelClient for LLM calls
        review_repository: Repository for saving review sessions
        tasks_repository: Repository for updating task status
        publisher: External API publisher (mock or real)
        token_budget: Token budget for multi-pass review (default: 12000)
    """

    def __init__(
        self,
        archive_reader: ArchiveReader,
        diff_analyzer: DiffAnalyzer,
        unified_client: UnifiedModelClient,
        review_repository: HomeworkReviewRepository,
        tasks_repository: LongTasksRepository,
        publisher: ReviewPublisher,
        log_parser: Optional[LogParser] = None,
        log_normalizer: Optional[LogNormalizer] = None,
        log_analyzer: Optional[LogAnalyzer] = None,
        settings: Optional[Settings] = None,
        token_budget: int = 12000,
        mcp_client: Optional[ToolClientProtocol] = None,
        fallback_publisher: Optional[ReviewPublisher] = None,
    ) -> None:
        """Initialize use case.

        Args:
            archive_reader: Archive service
            diff_analyzer: Diff analyzer
            unified_client: UnifiedModelClient
            review_repository: Review repository
            tasks_repository: Tasks repository
            publisher: External publisher
            log_parser: Log parser implementation
            log_normalizer: Log normalizer
            log_analyzer: LLM log analyzer
            settings: Application settings
            token_budget: Token budget for review
            mcp_client: MCP tool client for publishing results
            fallback_publisher: Optional fallback review publisher
        """
        self.archive_reader = archive_reader
        self.diff_analyzer = diff_analyzer
        self.unified_client = unified_client
        self.review_repository = review_repository
        self.tasks_repository = tasks_repository
        self.publisher = publisher
        self.fallback_publisher = fallback_publisher or publisher
        self.mcp_client = mcp_client
        self.settings = settings or get_settings()
        self.log_parser = log_parser or LogParserImpl()
        self.log_normalizer = log_normalizer or LogNormalizer()
        self.log_analyzer = log_analyzer or LLMLogAnalyzer(
            unified_client=unified_client,
            timeout=self.settings.log_analysis_timeout,
            retries=self.settings.review_max_retries,
        )

        # Create review logger shared across review workflow
        self.review_logger = ReviewLogger(session_id=None)

        if not isinstance(archive_reader, ZipArchiveService):
            raise ValueError(
                "ModularReviewService requires ZipArchiveService as archive reader"
            )

        review_config = ReviewConfig(token_budget=token_budget)
        self.modular_service = ModularReviewService(
            archive_service=archive_reader,
            diff_analyzer=diff_analyzer,
            llm_client=unified_client,
            review_config=review_config,
            review_logger=self.review_logger,
            settings=self.settings,
        )

        limiter_config = ReviewRateLimiterConfig(
            window_seconds=self.settings.review_rate_limit_window_seconds,
            per_student=self.settings.review_rate_limit_per_student,
            per_assignment=self.settings.review_rate_limit_per_assignment,
        )
        self.rate_limiter = ReviewRateLimiter(self.tasks_repository, limiter_config)

    async def execute(self, task: LongTask) -> str:
        """Process review task via modular reviewer workflow."""
        context = self._extract_task_context(task)
        await self._enforce_rate_limits(context)
        logger.info(
            "Processing review task: task_id=%s, student_id=%s, assignment_id=%s",
            context.task.task_id,
            context.student_id,
            context.assignment_id,
        )

        try:
            report = await self._run_review(context)
            await self._append_log_analysis(report, context)
            await self._attach_haiku(report)
            report_markdown = await self._persist_report(report, context)
            await self._publish_review_report(report, context, report_markdown)
            await self._mark_task_complete(context.task, cast(str, report.session_id))
            return cast(str, report.session_id)
        except Exception as exc:
            await self._mark_task_failed(context.task, exc)
            raise

    def _extract_task_context(self, task: LongTask) -> _ReviewTaskContext:
        """Collect and validate metadata required for review processing."""
        if task.task_type.value != "code_review":
            raise ValueError(f"Task type must be CODE_REVIEW, got {task.task_type}")
        metadata = task.metadata
        new_submission_path = metadata.get("new_submission_path")
        new_commit = metadata.get("new_commit")
        if not new_submission_path:
            raise ValueError("new_submission_path is required in task metadata")
        if not new_commit:
            raise ValueError("new_commit is required in task metadata")
        return _ReviewTaskContext(
            task=task,
            new_submission_path=new_submission_path,
            previous_submission_path=metadata.get("previous_submission_path"),
            assignment_id=metadata.get("assignment_id", "unknown"),
            new_commit=new_commit,
            old_commit=metadata.get("old_commit"),
            logs_zip_path=metadata.get("logs_zip_path"),
            student_id=str(task.user_id),
        )

    async def _enforce_rate_limits(self, context: _ReviewTaskContext) -> None:
        """Ensure review execution stays within configured rate limits."""
        try:
            await self.rate_limiter.ensure_within_limits(
                context.student_id, context.assignment_id
            )
        except ReviewRateLimitExceeded as exc:
            logger.warning(
                "Review rate limit exceeded: student_id=%s, assignment_id=%s, error=%s",
                context.student_id,
                context.assignment_id,
                exc,
            )
            raise

    async def _run_review(self, context: _ReviewTaskContext) -> MultiPassReport:
        """Run modular review service and return generated report."""
        report = await self.modular_service.review_submission(
            new_archive_path=context.new_submission_path,
            previous_archive_path=context.previous_submission_path,
            assignment_id=context.assignment_id,
            student_id=context.student_id,
        )
        return cast(MultiPassReport, report)

    async def _append_log_analysis(
        self, report: Any, context: _ReviewTaskContext
    ) -> None:
        """Attach log analysis results to report when configured."""
        logs_zip = context.logs_zip_path
        if not logs_zip:
            self._set_log_analysis_status(report, "skipped", "No logs archive provided")
            return
        if not self.settings.enable_log_analysis:
            self._set_log_analysis_status(
                report, "skipped", "Log analysis disabled in settings"
            )
            return
        if not hasattr(self.archive_reader, "extract_logs"):
            self._set_log_analysis_status(
                report, "skipped", "Archive reader cannot extract logs"
            )
            return
        try:
            logger.info("Starting Pass 4: Log analysis for %s", logs_zip)
            result = await self._run_pass_4_log_analysis(logs_zip)
            report.pass_4_logs = result
            logger.info(
                "Pass 4 completed: %s groups analyzed",
                result.get("log_groups_analyzed", 0),
            )
        except Exception as exc:
            self._handle_log_analysis_error(report, exc)

    async def _attach_haiku(self, report: Any) -> None:
        """Generate haiku summary using LLM client when available."""
        if not hasattr(self.unified_client, "make_request"):
            return
        try:
            from src.infrastructure.reporting.homework_report_generator import (
                _generate_haiku_from_model,
            )

            top_titles = self._top_issue_titles(report)
            report.haiku = await _generate_haiku_from_model(
                client=self.unified_client,
                critical_count=report.critical_count,
                major_count=report.major_count,
                component=(
                    report.detected_components[0]
                    if report.detected_components
                    else "code"
                ),
                top_issues=top_titles,
            )
            logger.info("Generated haiku for report")
        except Exception as exc:
            logger.warning("Failed to generate haiku: %s", exc)
            report.haiku = (
                "Code flows onward,\n"
                "Issues found, lessons learned—\n"
                "Improvement awaits."
            )

    def _set_log_analysis_status(self, report: Any, status: str, reason: str) -> None:
        """Set pass 4 status with a provided reason."""
        report.pass_4_logs = {"status": status, "reason": reason}

    def _handle_log_analysis_error(self, report: Any, exc: Exception) -> None:
        """Handle log analysis errors with structured logging."""
        logger.warning("Pass 4 (log analysis) failed: %s", exc, exc_info=True)
        report.pass_4_logs = {"status": "error", "error": str(exc)[:200]}

    async def _persist_report(self, report: Any, context: _ReviewTaskContext) -> str:
        """Persist review outputs and return markdown representation."""
        session_id = report.session_id
        report_json = report.to_dict()
        report_markdown = report.to_markdown()
        logs = self.review_logger.get_all_logs() if self.review_logger else {}
        metadata = {
            "task_id": context.task.task_id,
            "student_id": context.student_id,
            "diff_metrics": (
                report.pass_1.metadata.get("diff_metrics") if report.pass_1 else None
            ),
        }
        await self.review_repository.save_review_session(
            session_id=session_id,
            repo_name=context.repo_name,
            assignment_type=context.assignment_id,
            logs=logs,
            report={"markdown": report_markdown, "json": report_json},
            metadata=metadata,
        )
        logger.info("Saved review session: session_id=%s", session_id)
        return cast(str, report_markdown)

    async def _publish_review_report(
        self,
        report: Any,
        context: _ReviewTaskContext,
        report_markdown: str,
    ) -> None:
        """Publish review using MCP with fallback options."""
        overall_score = self._extract_overall_score(report)
        await self._publish_review_via_mcp(
            student_id=context.student_id,
            assignment_id=context.assignment_id,
            submission_hash=context.new_commit,
            review_markdown=report_markdown,
            session_id=report.session_id,
            overall_score=overall_score,
            task_id=context.task.task_id,
        )

    async def _mark_task_complete(self, task: LongTask, session_id: str) -> None:
        """Mark task as completed and log outcome."""
        await self.tasks_repository.complete(task.task_id, session_id)
        logger.info(
            "Review task completed: task_id=%s, session_id=%s",
            task.task_id,
            session_id,
        )

    async def _mark_task_failed(self, task: LongTask, exc: Exception) -> None:
        """Persist failure state for review task."""
        logger.error("Failed to process review task: %s", exc, exc_info=True)
        await self.tasks_repository.fail(task.task_id, str(exc)[:1000])

    def _top_issue_titles(self, report: Any) -> list[str]:
        """Return truncated titles for top critical findings."""
        if not (report.pass_1 and getattr(report.pass_1, "findings", None)):
            return []
        return [finding.title[:40] for finding in report.pass_1.findings[:3]]

    def _extract_overall_score(self, report: MultiPassReport) -> int:
        """Extract overall score from MultiPassReport.

        Purpose:
            Attempts to extract a numeric score from the report.
            Falls back to 50 if no score is found.

        Args:
            report: MultiPassReport

        Returns:
            Overall score (0-100)
        """
        # Try to extract score from pass_1 metadata
        if report.pass_1 and report.pass_1.metadata:
            score = report.pass_1.metadata.get("overall_score")
            if score is not None:
                return int(score)

        # Fallback: calculate score based on findings severity
        # This is a simple heuristic
        total_findings_raw = getattr(report, "total_findings", 0)
        try:
            total_findings = int(total_findings_raw)
        except (TypeError, ValueError):
            return 50

        if total_findings == 0:
            return 100
        elif total_findings < 5:
            return 80
        elif total_findings < 10:
            return 60
        else:
            return 40

    async def _run_pass_4_log_analysis(self, logs_zip_path: str) -> dict[str, Any]:
        """Run Pass 4: Runtime log analysis.

        Purpose:
            Extract, parse, normalize, and analyze logs using LLM.

        Args:
            logs_zip_path: Path to logs ZIP archive

        Returns:
            Dictionary with analysis results

        Example:
            results = await self._run_pass_4_log_analysis("/path/to/logs.zip")
        """
        from src.domain.value_objects.log_analysis import LogEntry

        # 1. Extract logs from archive
        extractor = cast(
            Callable[[str], dict[str, str]],
            getattr(self.archive_reader, "extract_logs"),
        )
        logs_dict = extractor(logs_zip_path)
        if not logs_dict:
            return {
                "status": "skipped",
                "reason": "No log files found in archive",
            }

        # 2. Parse logs
        all_entries: list[LogEntry] = []
        for file_path, content in logs_dict.items():
            # Determine source type
            if "checker.log" in file_path:
                source = "checker"
            elif "stderr" in file_path.lower():
                source = "docker-stderr"
            elif "stdout" in file_path.lower():
                source = "docker-stdout"
            elif "compose" in file_path:
                source = "container"
            else:
                source = "container"

            entries = self.log_parser.parse(content, source)
            all_entries.extend(entries)

        if not all_entries:
            return {
                "status": "skipped",
                "reason": "No log entries parsed",
            }

        # 3. Filter by severity
        filtered_entries = self.log_normalizer.filter_by_severity(
            all_entries, min_severity=self.settings.log_analysis_min_severity
        )

        if not filtered_entries:
            return {
                "status": "completed",
                "total_log_entries": len(all_entries),
                "log_groups_analyzed": 0,
                "results": [],
            }

        # 4. Group and normalize
        grouped = self.log_normalizer.group_by_component_and_severity(filtered_entries)
        log_groups = self.log_normalizer.create_log_groups(grouped)

        # 5. Limit groups to analyze
        groups_to_analyze = log_groups[: self.settings.log_analysis_max_groups]

        # 6. Analyze with LLM
        analysis_results = []
        for log_group in groups_to_analyze:
            result = await self.log_analyzer.analyze_log_group(log_group)
            if result:
                analysis_results.append(
                    {
                        "component": log_group.component,
                        "classification": result.classification,
                        "description": result.description,
                        "root_cause": result.root_cause,
                        "recommendations": result.recommendations,
                        "confidence": result.confidence,
                        "count": log_group.count,
                    }
                )

        return {
            "status": "completed",
            "total_log_entries": len(all_entries),
            "log_groups_analyzed": len(analysis_results),
            "results": analysis_results,
        }

    async def _publish_review_via_mcp(
        self,
        student_id: str,
        assignment_id: str,
        submission_hash: str,
        review_markdown: str,
        session_id: str,
        overall_score: Optional[int],
        task_id: str,
    ) -> bool:
        """Publish review via MCP tool, falling back on failure.

        Purpose:
            Gather tool arguments through LLM guidance and execute MCP tool
            invocation. Falls back to configured publisher when anything fails.

        Args:
            student_id: Student identifier provided to MCP.
            assignment_id: Assignment identifier for fallback payload.
            submission_hash: Commit hash associated with submission.
            review_markdown: Markdown review content.
            session_id: Review session identifier.
            overall_score: Optional numeric score to publish.
            task_id: Identifier of the long-running task.

        Returns:
            True when MCP publishing succeeds, otherwise False.

        Example:
            >>> await use_case._publish_review_via_mcp(
            ...     "Ivanov Ivan",
            ...     "HW1",
            ...     "abc123",
            ...     "# Review",
            ...     "session-1",
            ...     90,
            ...     "task-1",
            ... )
        """

        if self.mcp_client is None:
            await self._publish_via_fallback(
                assignment_id,
                student_id,
                submission_hash,
                session_id,
                overall_score,
                task_id,
            )
            return False

        arguments = await self._collect_mcp_arguments(
            student_id,
            submission_hash,
            review_markdown,
            session_id,
            overall_score,
        )

        if arguments is None:
            await self._publish_via_fallback(
                assignment_id,
                student_id,
                submission_hash,
                session_id,
                overall_score,
                task_id,
            )
            return False

        try:
            await self.mcp_client.call_tool("submit_review_result", arguments)
            logger.info("Published review via MCP tool")
            return True
        except Exception as error:
            logger.warning(f"MCP tool call failed: {error}")
            await self._publish_via_fallback(
                assignment_id,
                student_id,
                submission_hash,
                session_id,
                overall_score,
                task_id,
            )
            return False

    async def _collect_mcp_arguments(
        self,
        student_id: str,
        submission_hash: str,
        review_markdown: str,
        session_id: str,
        overall_score: Optional[int],
    ) -> Optional[dict[str, Any]]:
        """Collect MCP tool arguments through LLM guidance.

        Purpose:
            Prepare MCP context, prompt the LLM, and parse tool call arguments.

        Args:
            student_id: Student identifier.
            submission_hash: Commit hash for submission.
            review_markdown: Markdown review content.
            session_id: Review session identifier.
            overall_score: Optional numeric score extracted earlier.

        Returns:
            Dictionary with tool arguments or None on failure.

        Example:
            >>> args = await use_case._collect_mcp_arguments(
            ...     "Ivanov Ivan",
            ...     "abc123",
            ...     "# Review",
            ...     "session-1",
            ...     95,
            ... )
        """

        try:
            prompt, tools = await self._prepare_mcp_publish_context(
                mcp_client=self.mcp_client,  # type: ignore[arg-type]
                student_id=student_id,
                submission_hash=submission_hash,
                review_markdown=review_markdown,
                session_id=session_id,
                overall_score=overall_score,
            )
        except Exception as error:
            logger.warning(f"Failed to prepare MCP context: {error}")
            return None

        tool_schema = json.dumps(tools[0].get("input_schema", {}), indent=2)
        prompt_with_schema = (
            f"{prompt}\n\nTool input schema:\n{tool_schema}\n\n"
            'Respond with JSON: {\n  "tool": "submit_review_result",\n'
            '  "arguments": { ... }\n}.'
        )

        try:
            response = await self.unified_client.make_request(  # type: ignore[attr-defined]
                model_name=self.settings.llm_model,
                prompt=prompt_with_schema,
                max_tokens=400,
                temperature=0.0,
            )
        except Exception as error:
            logger.warning(f"LLM failed to provide MCP arguments: {error}")
            return None

        arguments = self._parse_tool_call_response(response.response)
        if arguments is None:
            logger.warning("LLM response did not contain valid tool arguments")
            return None

        self._enrich_tool_arguments(
            arguments,
            student_id,
            submission_hash,
            review_markdown,
            session_id,
            overall_score,
        )
        return arguments

    def _parse_tool_call_response(self, response_text: str) -> Optional[dict[str, Any]]:
        """Parse LLM response for tool call arguments.

        Purpose:
            Extract structured arguments from JSON-like responses produced
            by the LLM when instructed to provide tool invocation details.

        Args:
            response_text: Raw text returned by the LLM.

        Returns:
            Dictionary with arguments or None when parsing fails.

        Example:
            >>> use_case._parse_tool_call_response('{"tool": "submit"}')
        """

        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None

        if payload.get("tool") == "submit_review_result":
            arguments = payload.get("arguments")
            return arguments if isinstance(arguments, dict) else None

        required_keys = {
            "student_id",
            "submission_hash",
            "review_content",
        }
        if required_keys.issubset(payload.keys()):
            return payload  # type: ignore[return-value]

        return None

    def _enrich_tool_arguments(
        self,
        arguments: dict[str, Any],
        student_id: str,
        submission_hash: str,
        review_markdown: str,
        session_id: str,
        overall_score: Optional[int],
    ) -> None:
        """Ensure MCP tool arguments contain all required fields.

        Purpose:
            Backfill any missing parameters expected by HW checker MCP.

        Args:
            arguments: Parsed arguments from LLM response.
            student_id: Student identifier to ensure presence.
            submission_hash: Commit hash for submission.
            review_markdown: Markdown review content.
            session_id: Review session identifier.
            overall_score: Optional score to include.

        Example:
            >>> use_case._enrich_tool_arguments({}, "Ivanov Ivan", "hash", "# R", "s", 70)
        """

        arguments.setdefault("student_id", student_id)
        arguments.setdefault("submission_hash", submission_hash)
        arguments.setdefault("review_content", review_markdown)
        if session_id:
            arguments.setdefault("session_id", session_id)
        if overall_score is not None:
            arguments.setdefault("overall_score", overall_score)

    async def _publish_via_fallback(
        self,
        assignment_id: str,
        student_id: str,
        submission_hash: str,
        session_id: str,
        overall_score: Optional[int],
        task_id: str,
    ) -> None:
        """Publish review through fallback publisher if configured.

        Purpose:
            Provide resilience when MCP publishing is unavailable or fails.

        Args:
            assignment_id: Assignment identifier.
            student_id: Student identifier.
            submission_hash: Commit hash.
            session_id: Session identifier.
            overall_score: Optional numeric score.
            task_id: Task identifier for traceability.

        Example:
            >>> await use_case._publish_via_fallback("HW1", "Ivanov", "abc", "s", 80, "t")
        """

        if self.fallback_publisher is None:
            logger.warning("Fallback publisher not configured; skipping publish")
            return

        payload: dict[str, Any] = {
            "task_id": task_id,
            "student_id": student_id,
            "assignment_id": assignment_id,
            "session_id": session_id,
            "new_commit": submission_hash,
        }

        if overall_score is not None:
            payload["overall_score"] = overall_score

        try:
            await self.fallback_publisher.publish_review(payload)
            logger.info("Published review via fallback publisher")
        except Exception as error:
            logger.error(f"Fallback publish failed: {error}")

    async def _prepare_mcp_publish_context(
        self,
        mcp_client: ToolClientProtocol,
        student_id: str,
        submission_hash: str,
        review_markdown: str,
        session_id: str,
        overall_score: Optional[int],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Prepare prompt and tools list for MCP publishing step.

        Purpose:
            Collect tool schema from external MCP server and craft detailed
            instructions for the LLM to call the publishing tool with correct
            arguments.

        Args:
            mcp_client: Client for interacting with MCP tools.
            student_id: Student identifier text used by HW checker.
            submission_hash: Commit hash for the reviewed submission.
            review_markdown: Full markdown review content.
            session_id: Review session identifier.
            overall_score: Optional score extracted from review report.

        Returns:
            Tuple containing LLM prompt and filtered tools definition.

        Raises:
            RuntimeError: When required MCP tool is not available.

        Example:
            >>> prompt, tools = await use_case._prepare_mcp_publish_context(
            ...     mcp_client,
            ...     "Ivanov Ivan",
            ...     "abc123",
            ...     "# Review",
            ...     "session-1",
            ...     90,
            ... )
        """

        tools = await mcp_client.discover_tools()
        submit_tool = next(
            (tool for tool in tools if tool.get("name") == "submit_review_result"),
            None,
        )
        if submit_tool is None:
            raise RuntimeError("submit_review_result tool not available on MCP server")

        score_text = str(overall_score) if overall_score is not None else "not provided"
        prompt_lines = [
            "You are responsible for publishing the finalized code review.",
            (
                "Call the MCP tool `submit_review_result` with the arguments "
                "listed below."
            ),
            f"student_id: {student_id}",
            f"submission_hash: {submission_hash}",
        ]

        if session_id:
            prompt_lines.append(f"session_id: {session_id}")

        prompt_lines.append(f"overall_score: {score_text}")
        prompt_lines.append("Full review content follows:")
        prompt_lines.append(review_markdown)

        prompt = "\n".join(prompt_lines)
        return prompt, [submit_tool]
