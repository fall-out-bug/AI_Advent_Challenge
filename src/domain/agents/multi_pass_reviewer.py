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

from shared_package.clients.unified_client import UnifiedModelClient

from src.domain.agents.passes.architecture_pass import (
    ArchitectureReviewPass,
)
from src.domain.agents.passes.component_pass import ComponentDeepDivePass
from src.domain.agents.passes.synthesis_pass import SynthesisPass
from src.domain.agents.session_manager import SessionManager
from src.domain.models.code_review_models import (
    MultiPassReport,
    PassFindings,
)
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
        """
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

