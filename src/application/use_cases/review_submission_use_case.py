"""Use case for reviewing code submissions from archives."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Add shared to path for imports
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

# Try to import UnifiedModelClient with fallbacks
_UNIFIED_CLIENT_AVAILABLE = False
try:
    from shared_package.clients.unified_client import UnifiedModelClient
    _UNIFIED_CLIENT_AVAILABLE = True
except ImportError:
    try:
        from shared.clients.unified_client import UnifiedModelClient
        _UNIFIED_CLIENT_AVAILABLE = True
    except ImportError:
        shared_package_path = _root / "shared" / "shared_package"
        if shared_package_path.exists():
            sys.path.insert(0, str(shared_package_path.parent))
            try:
                from shared_package.clients.unified_client import UnifiedModelClient
                _UNIFIED_CLIENT_AVAILABLE = True
            except ImportError:
                pass

if not _UNIFIED_CLIENT_AVAILABLE:
    class UnifiedModelClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("UnifiedModelClient not available. Shared package not installed.")

from src.domain.agents.multi_pass_reviewer import MultiPassReviewerAgent
from src.domain.interfaces.archive_reader import ArchiveReader
from src.domain.interfaces.log_analyzer import LogAnalyzer
from src.domain.interfaces.log_parser import LogParser
from src.domain.interfaces.review_publisher import ReviewPublisher
from src.domain.interfaces.tool_client import ToolClientProtocol
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.domain.value_objects.long_summarization_task import LongTask
from src.infrastructure.config.settings import Settings
from src.infrastructure.logs.log_normalizer import LogNormalizer
from src.infrastructure.adapters.multi_pass_model_adapter import MultiPassModelAdapter
from src.infrastructure.logging.review_logger import ReviewLogger
from src.infrastructure.repositories.homework_review_repository import (
    HomeworkReviewRepository,
)
from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository

logger = logging.getLogger(__name__)


class ReviewSubmissionUseCase:
    """Use case for reviewing code submissions from archives.

    Purpose:
        Orchestrates the complete review process using MultiPassReviewerAgent:
        extracts archives, analyzes diff, runs multi-pass review, saves results,
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
        log_parser: LogParser,
        log_normalizer: LogNormalizer,
        log_analyzer: LogAnalyzer,
        settings: Settings,
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
        self.log_parser = log_parser
        self.log_normalizer = log_normalizer
        self.log_analyzer = log_analyzer
        self.settings = settings

        # Create review logger
        review_logger = ReviewLogger(session_id=None)

        # Create MultiPassReviewerAgent with adapter
        self.reviewer_agent = MultiPassReviewerAgent(
            unified_client=unified_client,
            token_budget=token_budget,
            review_logger=review_logger,
        )

    async def execute(self, task: LongTask) -> str:
        """Process review task.

        Purpose:
            Extracts archives, runs multi-pass review, saves results,
            and publishes to external API.

        Args:
            task: Review task to process

        Returns:
            Review session ID

        Raises:
            ValueError: If task metadata is invalid
            Exception: On processing failure
        """
        if task.task_type.value != "code_review":
            raise ValueError(f"Task type must be CODE_REVIEW, got {task.task_type}")

        # Extract task metadata
        metadata = task.metadata
        new_submission_path = metadata.get("new_submission_path")
        previous_submission_path = metadata.get("previous_submission_path")
        assignment_id = metadata.get("assignment_id", "unknown")
        new_commit = metadata.get("new_commit")
        old_commit = metadata.get("old_commit")
        logs_zip_path = metadata.get("logs_zip_path")
        student_id = str(task.user_id)  # user_id stores student_id for review tasks

        if not new_submission_path:
            raise ValueError("new_submission_path is required in task metadata")
        if not new_commit:
            raise ValueError("new_commit is required in task metadata")

        logger.info(
            f"Processing review task: task_id={task.task_id}, "
            f"student_id={student_id}, assignment_id={assignment_id}"
        )

        try:
            # 1. Run multi-pass review from archives
            report = await self.reviewer_agent.review_from_archives(
                archive_reader=self.archive_reader,
                diff_analyzer=self.diff_analyzer,
                new_archive_path=new_submission_path,
                previous_archive_path=previous_submission_path,
                assignment_id=assignment_id,
                student_id=student_id,
            )

            session_id = report.session_id

            # 2. Run Pass 4: Log Analysis (if enabled and logs provided)
            if (
                self.settings.enable_log_analysis
                and logs_zip_path
                and hasattr(self.archive_reader, "extract_logs")
            ):
                try:
                    logger.info(f"Starting Pass 4: Log analysis for {logs_zip_path}")
                    pass_4_results = await self._run_pass_4_log_analysis(logs_zip_path)
                    report.pass_4_logs = pass_4_results
                    logger.info(
                        f"Pass 4 completed: {pass_4_results.get('log_groups_analyzed', 0)} groups analyzed"
                    )
                except Exception as e:
                    logger.warning(f"Pass 4 (log analysis) failed: {e}", exc_info=True)
                    report.pass_4_logs = {
                        "status": "error",
                        "error": str(e)[:200],
                    }
            elif logs_zip_path and not self.settings.enable_log_analysis:
                report.pass_4_logs = {
                    "status": "skipped",
                    "reason": "Log analysis disabled in settings",
                }
            elif not logs_zip_path:
                report.pass_4_logs = {
                    "status": "skipped",
                    "reason": "No logs archive provided",
                }

            # 3. Save review session to repository
            repo_name = f"{student_id}_{assignment_id}"
            report_json = report.to_dict()
            report_markdown = report.to_markdown()

            # Get logs from review logger (if available)
            logs = {}
            if self.reviewer_agent.review_logger:
                logs = self.reviewer_agent.review_logger.get_all_logs()

            await self.review_repository.save_review_session(
                session_id=session_id,
                repo_name=repo_name,
                assignment_type=assignment_id,
                logs=logs,
                report={"markdown": report_markdown, "json": report_json},
                metadata={
                    "task_id": task.task_id,
                    "student_id": student_id,
                    "diff_metrics": report.pass_1.metadata.get("diff_metrics")
                    if report.pass_1
                    else None,
                },
            )

            logger.info(f"Saved review session: session_id={session_id}")

            # 4. Generate haiku
            if hasattr(self.reviewer_agent, "client") and self.reviewer_agent.client:
                try:
                    from src.infrastructure.reporting.homework_report_generator import (
                        _generate_haiku_from_model,
                    )
                    top_titles = (
                        [f.title[:40] for f in report.pass_1.findings[:3]]
                        if report.pass_1 and report.pass_1.findings
                        else []
                    )
                    haiku = await _generate_haiku_from_model(
                        client=self.reviewer_agent.client,
                        critical_count=report.critical_count,
                        major_count=report.major_count,
                        component=(
                            report.detected_components[0]
                            if report.detected_components
                            else "code"
                        ),
                        top_issues=top_titles,
                    )
                    report.haiku = haiku
                    logger.info("Generated haiku for report")
                except Exception as e:
                    logger.warning(f"Failed to generate haiku: {e}")
                    report.haiku = (
                        "Code flows onward,\n"
                        "Issues found, lessons learned—\n"
                        "Improvement awaits."
                    )

            # 5. Publish via MCP with fallback
            overall_score = self._extract_overall_score(report)
            await self._publish_review_via_mcp(
                student_id=student_id,
                assignment_id=assignment_id,
                submission_hash=new_commit,
                review_markdown=report_markdown,
                session_id=session_id,
                overall_score=overall_score,
                task_id=task.task_id,
            )

            # 6. Mark task as completed
            await self.tasks_repository.complete(task.task_id, session_id)
            logger.info(f"Review task completed: task_id={task.task_id}, session_id={session_id}")

            return session_id

        except Exception as e:
            logger.error(f"Failed to process review task: {e}", exc_info=True)
            error_msg = str(e)[:1000]
            await self.tasks_repository.fail(task.task_id, error_msg)
            raise

    def _extract_overall_score(self, report) -> int:
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

    async def _run_pass_4_log_analysis(
        self, logs_zip_path: str
    ) -> dict[str, Any]:
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
        logs_dict = self.archive_reader.extract_logs(logs_zip_path)
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
        grouped = self.log_normalizer.group_by_component_and_severity(
            filtered_entries
        )
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
            "Respond with JSON: {\n  \"tool\": \"submit_review_result\",\n"
            "  \"arguments\": { ... }\n}."
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

    def _parse_tool_call_response(
        self, response_text: str
    ) -> Optional[dict[str, Any]]:
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

