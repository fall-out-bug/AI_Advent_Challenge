"""Multi-pass code review agent orchestrator.

Following Clean Architecture principles and the Zen of Python.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

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
    # Fallback: try shared.clients.unified_client
    try:
        from shared.clients.unified_client import UnifiedModelClient
        _UNIFIED_CLIENT_AVAILABLE = True
    except ImportError:
        # Last resort: try to add shared_package to path
        shared_package_path = _root / "shared" / "shared_package"
        if shared_package_path.exists():
            sys.path.insert(0, str(shared_package_path.parent))
            try:
                from shared_package.clients.unified_client import UnifiedModelClient
                _UNIFIED_CLIENT_AVAILABLE = True
            except ImportError:
                pass

# If UnifiedModelClient is not available, create a dummy class
if not _UNIFIED_CLIENT_AVAILABLE:
    # Create a dummy UnifiedModelClient to prevent NameError
    class UnifiedModelClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("UnifiedModelClient not available. Shared package not installed.")

from src.domain.agents.passes.architecture_pass import (
    ArchitectureReviewPass,
)
from src.domain.agents.passes.component_pass import ComponentDeepDivePass
from src.domain.agents.passes.synthesis_pass import SynthesisPass
from src.domain.agents.session_manager import SessionManager
from src.domain.interfaces.archive_reader import ArchiveReader
from src.domain.models.code_review_models import (
    MultiPassReport,
    PassFindings,
)
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.domain.value_objects.code_diff import CodeDiff
from src.infrastructure.logging.review_logger import ReviewLogger

logger = logging.getLogger(__name__)


class MultiPassReviewerAgent:
    """Orchestrator for multi-pass code review.

    Purpose:
        Coordinates all three review passes:
        - Pass 1: Architecture overview
        - Pass 2: Component deep-dive (per component)
        - Pass 3: Synthesis and integration

    Args:
        unified_client: UnifiedModelClient instance
        token_budget: Total token budget for all passes (default: 12000)

    Example:
        agent = MultiPassReviewerAgent(unified_client, token_budget=12000)
        report = await agent.process_multi_pass(code, repo_name="my_project")
        markdown = report.to_markdown()
    """

    def __init__(
        self,
        unified_client: UnifiedModelClient,
        token_budget: int = 12000,
        review_logger: Optional[ReviewLogger] = None,
    ):
        """Initialize multi-pass reviewer agent.

        Args:
            unified_client: UnifiedModelClient instance
            token_budget: Total token budget for all passes (default: 12000)
            review_logger: Optional ReviewLogger for detailed logging
            
        Raises:
            RuntimeError: If UnifiedModelClient is not available
        """
        if not _UNIFIED_CLIENT_AVAILABLE:
            raise RuntimeError("UnifiedModelClient not available. Shared package not installed.")
        self.client = unified_client
        self.token_budget = token_budget
        self.review_logger = review_logger
        self.logger = logging.getLogger(__name__)

    async def process_multi_pass(
        self,
        code: str,
        repo_name: str = "student_project",
    ) -> MultiPassReport:
        """Execute complete multi-pass review.

        Purpose:
            Main entry point for multi-pass code review.
            Executes all three passes sequentially and generates final report.

        Args:
            code: Code to review
            repo_name: Name of repository/project

        Returns:
            MultiPassReport with all findings

        Raises:
            Exception: If review process fails

        Example:
            report = await agent.process_multi_pass(
                code=project_code,
                repo_name="ml_project"
            )
        """
        self.logger.info("Starting multi-pass code review")
        start_time = datetime.now()

        # 1. Create session
        session = SessionManager.create()
        self.logger.info(f"Created session: {session.session_id}")

        pass_1_findings: Optional[PassFindings] = None
        pass_2_findings: Dict[str, PassFindings] = {}
        pass_3_findings: Optional[PassFindings] = None
        detected_components: list = []
        errors: Dict[str, str] = {}  # Track errors per component/pass

        # 2. Pass 1: Architecture Overview (Critical - must succeed)
        pass_1_findings = None
        detected_components = []
        try:
            architecture_pass = ArchitectureReviewPass(
                unified_client=self.client,
                session_manager=session,
                token_budget=self.token_budget // 4,  # Pass 1: 3000 tokens
                review_logger=self.review_logger,
            )
            pass_1_findings = await architecture_pass.run(code)
            detected_components = pass_1_findings.metadata.get("detected_components", [])
            self.logger.info(
                f"Pass 1 complete. Detected components: {detected_components}"
            )
        except Exception as e:
            error_msg = f"Pass 1 (Architecture) failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            errors["pass_1"] = error_msg
            # Pass 1 is critical - if it fails, we can't proceed meaningfully
            # But we still try to return partial report if possible
            detected_components = ["generic"]  # Fallback
            pass_1_findings = None  # Explicitly set to None to avoid AttributeError

        # 3. Pass 2: Component Deep-Dives (Sequential, non-blocking)
        if pass_1_findings or detected_components:
            # Calculate per-component token budget (6000 total split among components)
            num_components = len([c for c in detected_components if c != "generic"])
            per_component_budget = (self.token_budget // 2) // max(num_components, 1) if num_components > 0 else self.token_budget // 2
            
            for component_type in detected_components:
                if component_type != "generic":
                    try:
                        self.logger.info(f"Starting Pass 2 for {component_type}")
                        component_pass = ComponentDeepDivePass(
                            unified_client=self.client,
                            session_manager=session,
                            token_budget=per_component_budget,  # Per-component budget
                            review_logger=self.review_logger,
                        )
                        findings = await component_pass.run(
                            code=code,
                            component_type=component_type,
                            context_from_pass_1=pass_1_findings.to_dict()
                            if pass_1_findings
                            else None,
                        )
                        pass_2_findings[component_type] = findings
                        self.logger.info(f"Pass 2 complete for {component_type}")
                    except Exception as e:
                        error_msg = f"Pass 2 ({component_type}) failed: {str(e)}"
                        self.logger.error(
                            f"{error_msg}. Continuing with other components...",
                            exc_info=True  # Log full traceback
                        )
                        errors[f"pass_2_{component_type}"] = error_msg
                        # Continue with other components - don't block

        # 4. Pass 3: Synthesis (Can work with partial findings)
        try:
            synthesis_pass = SynthesisPass(
                unified_client=self.client,
                session_manager=session,
                token_budget=self.token_budget // 4,  # Pass 3: 3000 tokens
                review_logger=self.review_logger,
            )
            pass_3_findings = await synthesis_pass.run(code)
            self.logger.info("Pass 3 complete")
        except Exception as e:
            error_msg = f"Pass 3 (Synthesis) failed: {str(e)}"
            self.logger.error(error_msg)
            errors["pass_3"] = error_msg
            # Pass 3 failure is non-critical - we can still return Pass 1+2 findings

        # 5. Build final report
        execution_time = (datetime.now() - start_time).total_seconds()

        # Calculate total findings count
        total_findings = 0
        if pass_1_findings:
            total_findings += len(pass_1_findings.findings)
        for findings in pass_2_findings.values():
            total_findings += len(findings.findings)
        if pass_3_findings:
            total_findings += len(pass_3_findings.findings)

        # Determine report status
        has_critical_error = "pass_1" in errors
        has_partial_data = pass_1_findings or pass_2_findings or pass_3_findings

        if has_critical_error and not has_partial_data:
            # No usable data - raise exception
            raise Exception(
                f"Multi-pass review failed completely. Errors: {errors}"
            )

        # Add error metadata to report
        error_metadata = {
            "errors": errors,
            "has_partial_data": has_partial_data,
            "passes_completed": {
                "pass_1": pass_1_findings is not None,
                "pass_2": len(pass_2_findings),
                "pass_3": pass_3_findings is not None,
            },
        }

        final_report = MultiPassReport(
            session_id=session.session_id,
            repo_name=repo_name,
            pass_1=pass_1_findings,
            pass_2_results=pass_2_findings,
            pass_3=pass_3_findings,
            detected_components=detected_components,
            execution_time_seconds=execution_time,
            total_findings=total_findings,
        )

        # Store errors in metadata
        if errors:
            # Add to pass metadata if available
            if pass_1_findings:
                pass_1_findings.metadata.setdefault("errors", {}).update(error_metadata)
            else:
                # Store in session metadata
                session.save_findings("_errors", error_metadata)

        # 6. Persist session
        session.persist()

        self.logger.info(
            f"Multi-pass review complete in {execution_time:.1f}s. "
            f"Found {total_findings} total findings."
        )
        return final_report

    async def get_report(self, session_id: str) -> Optional[MultiPassReport]:
        """Retrieve existing report by session_id.

        Purpose:
            Loads previously generated report from session storage.

        Args:
            session_id: Session ID to load

        Returns:
            MultiPassReport if found, None otherwise

        Example:
            report = await agent.get_report("abc-123-session-id")
        """
        try:
            session = SessionManager(session_id=session_id)
            all_findings = session.load_all_findings()

            if not all_findings:
                return None

            # Reconstruct report from findings
            pass_1_data = all_findings.get("pass_1", {})
            pass_1_findings = (
                PassFindings.from_dict(pass_1_data) if pass_1_data else None
            )

            pass_2_findings = {}
            for key in all_findings.keys():
                if key.startswith("pass_2_"):
                    component_type = key.replace("pass_2_", "")
                    findings_data = all_findings[key]
                    if findings_data:
                        pass_2_findings[component_type] = PassFindings.from_dict(
                            findings_data
                        )

            pass_3_data = all_findings.get("pass_3", {})
            pass_3_findings = (
                PassFindings.from_dict(pass_3_data) if pass_3_data else None
            )

            detected_components = (
                pass_1_findings.metadata.get("detected_components", [])
                if pass_1_findings
                else []
            )

            return MultiPassReport(
                session_id=session_id,
                repo_name=pass_1_findings.metadata.get("repo_name", "unknown")
                if pass_1_findings
                else "unknown",
                pass_1=pass_1_findings,
                pass_2_results=pass_2_findings,
                pass_3=pass_3_findings,
                detected_components=detected_components,
            )

        except Exception as e:
            self.logger.error(f"Failed to load report for session {session_id}: {e}")
            return None

    async def review_from_archives(
        self,
        archive_reader: ArchiveReader,
        diff_analyzer: DiffAnalyzer,
        new_archive_path: str,
        previous_archive_path: str | None = None,
        assignment_id: str = "unknown",
        student_id: str | None = None,
    ) -> MultiPassReport:
        """Review code from ZIP archives.

        Purpose:
            Extracts archives, analyzes diff, combines code files,
            and runs multi-pass review. Uses dependency injection
            to avoid importing infrastructure layer.

        Args:
            archive_reader: Archive extraction service (injected)
            diff_analyzer: Code diff analyzer (injected)
            new_archive_path: Path to new submission ZIP
            previous_archive_path: Optional path to previous submission
            assignment_id: Assignment identifier
            student_id: Optional student identifier

        Returns:
            MultiPassReport with review findings

        Raises:
            Exception: On archive extraction or review failure

        Example:
            report = await agent.review_from_archives(
                archive_reader=zip_service,
                diff_analyzer=diff_analyzer,
                new_archive_path="/path/to/new.zip",
                previous_archive_path="/path/to/old.zip",
                assignment_id="HW2",
                student_id="student123"
            )
        """
        self.logger.info(
            f"Starting review from archives: new={new_archive_path}, "
            f"old={previous_archive_path}, assignment={assignment_id}"
        )

        # 1. Extract new archive
        new_archive = archive_reader.extract_submission(
            new_archive_path, f"new_{assignment_id}"
        )
        self.logger.info(
            f"Extracted new archive: {len(new_archive.code_files)} files, "
            f"total_size={new_archive.get_total_code_size()} bytes"
        )

        # 2. Extract old archive if provided
        old_archive = None
        if previous_archive_path:
            old_archive = archive_reader.extract_submission(
                previous_archive_path, f"old_{assignment_id}"
            )
            self.logger.info(
                f"Extracted old archive: {len(old_archive.code_files)} files"
            )

        # 3. Combine code files into strings
        def _combine_code_files(code_files: dict[str, str]) -> str:
            """Combine code files into single string."""
            parts = []
            for file_path, content in code_files.items():
                parts.append(f"# {file_path}\n{content}\n")
            return "\n".join(parts)

        old_code = (
            _combine_code_files(old_archive.code_files) if old_archive else ""
        )
        new_code = _combine_code_files(new_archive.code_files)

        # 4. Analyze diff (for context, not used directly in review)
        diff: CodeDiff | None = None
        if old_archive:
            diff = diff_analyzer.analyze(old_code, new_code)
            self.logger.info(
                f"Diff analysis: +{diff.lines_added} -{diff.lines_removed}, "
                f"change_ratio={diff.change_ratio:.1f}%, "
                f"refactor={diff.has_refactor}"
            )

        # 4.5. Run static analysis on extracted files
        static_analysis_results = None
        try:
            import tempfile
            from pathlib import Path
            from src.infrastructure.linters.code_quality_checker import CodeQualityChecker
            
            # Create temporary directory for extracted files
            with tempfile.TemporaryDirectory(prefix="review_static_analysis_") as tmpdir:
                tmp_path = Path(tmpdir)
                
                # Write extracted code files to temporary directory
                for file_path, file_content in new_archive.code_files.items():
                    # Create directory structure
                    full_path = tmp_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write file content
                    full_path.write_text(file_content, encoding='utf-8')
                
                # Run static analysis
                self.logger.info(f"Running static analysis on {len(new_archive.code_files)} files")
                checker = CodeQualityChecker(tmp_path)
                static_analysis_results = checker.run_all_checks()
                self.logger.info(
                    f"Static analysis complete: {static_analysis_results.get('summary', {}).get('total_issues', 0)} issues found"
                )
        except Exception as e:
            self.logger.warning(f"Static analysis failed: {e}", exc_info=True)
            # Continue without static analysis - it's not critical

# 5. Run multi-pass review on combined code
        repo_name = f"{student_id}_{assignment_id}" if student_id else assignment_id
        report = await self.process_multi_pass(code=new_code, repo_name=repo_name)
        
        # 5.5. Add static analysis results to report
        if static_analysis_results:
            report.static_analysis_results = static_analysis_results

        # 6. Add diff metadata to report if available
        if diff and report.pass_1:
            # Store diff metrics in pass_1 metadata for context
            report.pass_1.metadata["diff_metrics"] = {
                "lines_added": diff.lines_added,
                "lines_removed": diff.lines_removed,
                "change_ratio": diff.change_ratio,
                "functions_added": diff.functions_added,
                "functions_removed": diff.functions_removed,
                "classes_changed": diff.classes_changed,
                "has_refactor": diff.has_refactor,
            }

        self.logger.info(
            f"Review from archives complete: session_id={report.session_id}, "
            f"findings={report.total_findings}"
        )

        return report

    def export_report(
        self, report: MultiPassReport, format: str = "markdown"
    ) -> str:
        """Export report to different formats.

        Purpose:
            Converts MultiPassReport to various export formats.

        Args:
            report: MultiPassReport to export
            format: Export format ("markdown", "json", "html")

        Returns:
            Formatted report string

        Raises:
            ValueError: If format is not supported

        Example:
            markdown = agent.export_report(report, format="markdown")
            json_str = agent.export_report(report, format="json")
        """
        if format == "markdown":
            return report.to_markdown()
        elif format == "json":
            return report.to_json()
        elif format == "html":
            # Simple HTML export
            markdown = report.to_markdown()
            html = f"<html><body><pre>{markdown}</pre></body></html>"
            return html
        else:
            raise ValueError(f"Unsupported export format: {format}")

