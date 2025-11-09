"""Generator for detailed markdown reports from homework reviews.

Following Clean Architecture principles and the Zen of Python.
"""

import re
from typing import Any, Dict, List, Optional

from src.domain.models.code_review_models import MultiPassReport
from src.infrastructure.logging.review_logger import ReviewLogger


def _clean_path(path: str) -> str:
    """Clean file path by removing temporary directory prefixes.

    Purpose:
        Removes temporary directory prefixes like /tmp/homework_review_*/
        from file paths to make them relative and readable.

    Args:
        path: File path that may contain temp directory prefix

    Returns:
        Cleaned relative path

    Example:
        _clean_path("/tmp/homework_review_abc123/src/main.py")
        # Returns: "src/main.py"
    """
    if not path or path == "N/A":
        return path
    # Remove common temp directory patterns
    path = re.sub(r"/tmp/homework_review_[^/]+/", "", path)
    path = re.sub(r"/tmp/[^/]+/", "", path)
    return path


def _clean_linter_issue_path(issue_text: str) -> str:
    """Clean file path in linter issue string.

    Purpose:
        Removes temporary directory prefixes from file paths in linter
        issue strings (pylint, mypy format: "path:line:column: message").

    Args:
        issue_text: Linter issue string that may contain full path

    Returns:
        Issue string with cleaned relative path

    Example:
        _clean_linter_issue_path("/tmp/homework_review_abc/src/main.py:10:5: error: ...")
        # Returns: "src/main.py:10:5: error: ..."
    """
    if not issue_text:
        return issue_text
    # Extract path (part before first colon that contains path-like content)
    # Pattern: path starts with /tmp or absolute path, ends before :line:column:
    path_match = re.match(r"^(/tmp/[^:]+|/[^:]+)", issue_text)
    if path_match:
        full_path = path_match.group(1)
        cleaned_path = _clean_path(full_path)
        # Replace full path with cleaned path in the issue text
        return issue_text.replace(full_path, cleaned_path, 1)
    return issue_text


async def _generate_haiku_from_model(
    client, critical_count: int, major_count: int, component: str, top_issues: List[str]
) -> str:
    """Request Mistral to generate a haiku based on review findings."""

    issues_summary = ", ".join(top_issues[:3]) if top_issues else "code quality"

    prompt = f"""Generate a haiku (3 lines: 5-7-5 syllables) about this code review:

Component: {component}
Critical issues: {critical_count}
Major issues: {major_count}
Top issues: {issues_summary}

Create a thoughtful, professional haiku using software/data metaphors.
Return ONLY the 3-line haiku, nothing else."""

    try:
        response = await client.make_request(
            model_name="mistral", prompt=prompt, temperature=0.8, max_tokens=100
        )
        haiku_text = response.response.strip()
        # Clean up if model added quotes or extra formatting
        haiku_text = re.sub(r'^["\'`]|["\'`]$', "", haiku_text)
        # Remove any system tokens or prompt echoes
        haiku_text = re.sub(
            r"^.*?<<SYS>>.*?<</SYS>>.*?\n?", "", haiku_text, flags=re.DOTALL
        )
        # Remove if model echoed the prompt (find lines that start with actual haiku lines - typically 5-10 words)
        lines = haiku_text.split("\n")
        clean_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that look like prompt text (very long or contain specific patterns)
            if (
                line
                and len(line) < 150
                and not line.startswith(  # Reasonable haiku line length
                    "Generate a haiku"
                )
                and not "Component:" in line[:50]
                and not "Critical issues:" in line[:50]
                and not "Top issues:" in line[:50]
                and not "Return ONLY" in line
            ):
                clean_lines.append(line)

        # Take last 3 meaningful lines
        if len(clean_lines) >= 3:
            haiku_text = "\n".join(clean_lines[-3:])
        else:
            haiku_text = (
                "\n".join(clean_lines)
                if clean_lines
                else "Code flows onward,\nIssues found, lessons learned—\nImprovement awaits."
            )
        return haiku_text
    except Exception:
        return "Code flows onward,\nIssues found, lessons learned—\nImprovement awaits."


def _truncate_title(title: str, max_len: int = 60) -> str:
    """Truncate title if too long."""
    if len(title) <= max_len:
        return title
    return title[: max_len - 3] + "..."


async def generate_detailed_markdown_report(
    report: MultiPassReport,
    review_logger: Optional[ReviewLogger] = None,
    linter_results: Optional[Dict[str, Any]] = None,
    client=None,
) -> str:
    """Generate detailed markdown report from review results.

    Purpose:
        Creates a comprehensive markdown report including:
        - Executive summary
        - Detected components
        - Detailed findings from each pass
        - Linter results (flake8, pylint, mypy, black, isort)
        - Recommendations and priority roadmap
        - Model reasoning excerpts
        - Statistics

    Args:
        report: MultiPassReport with all findings
        review_logger: Optional ReviewLogger for accessing logs
        linter_results: Optional linter results from CodeQualityChecker
        client: Optional UnifiedModelClient for haiku generation

    Returns:
        Detailed markdown report as string

    Example:
        markdown = await generate_detailed_markdown_report(
            report=multi_pass_report,
            review_logger=logger,
            linter_results=linter_results,
            client=client
        )
    """
    md_parts = []

    # Header
    md_parts.append("# Code Review Report: Detailed Analysis")
    md_parts.append("")
    md_parts.append(f"**Archive Name**: {report.repo_name}")
    md_parts.append(f"**Session ID**: {report.session_id}")
    md_parts.append(
        f"**Created**: {report.created_at.isoformat() if hasattr(report, 'created_at') else 'N/A'}"
    )
    md_parts.append(f"**Review Duration**: {report.execution_time_seconds:.2f} seconds")
    md_parts.append("")

    # Statistics - calculate counts from findings
    critical_count = 0
    major_count = 0

    # Count from Pass 1
    if report.pass_1:
        for finding in report.pass_1.findings:
            severity = (
                finding.severity.value
                if hasattr(finding.severity, "value")
                else str(finding.severity).lower()
            )
            if severity == "critical":
                critical_count += 1
            elif severity == "major":
                major_count += 1

    # Count from Pass 2
    for findings in report.pass_2_results.values():
        for finding in findings.findings:
            severity = (
                finding.severity.value
                if hasattr(finding.severity, "value")
                else str(finding.severity).lower()
            )
            if severity == "critical":
                critical_count += 1
            elif severity == "major":
                major_count += 1

    # Count from Pass 3
    if report.pass_3:
        for finding in report.pass_3.findings:
            severity = (
                finding.severity.value
                if hasattr(finding.severity, "value")
                else str(finding.severity).lower()
            )
            if severity == "critical":
                critical_count += 1
            elif severity == "major":
                major_count += 1

    # Generate haiku
    haiku = "Code flows onward,\nIssues found, lessons learned—\nImprovement awaits."
    if client:
        top_titles = (
            [f.title[:40] for f in report.pass_1.findings[:3]]
            if report.pass_1 and report.pass_1.findings
            else []
        )
        haiku = await _generate_haiku_from_model(
            client,
            critical_count,
            major_count,
            report.detected_components[0] if report.detected_components else "code",
            top_titles,
        )

    md_parts.append("---")
    md_parts.append("")
    md_parts.append("*A code review haiku:*")
    md_parts.append("")
    haiku_lines = [line.strip() for line in haiku.split("\n") if line.strip()]
    # Format haiku with proper line breaks in blockquote
    # Each line gets its own > prefix, with empty lines between for proper Markdown formatting
    for i, line in enumerate(haiku_lines):
        md_parts.append(f"> {line}")
        # Add empty line after each haiku line (except the last) to ensure proper separation
        if i < len(haiku_lines) - 1:
            md_parts.append(">")
    md_parts.append("")
    md_parts.append("---")
    md_parts.append("")

    # Executive Summary
    md_parts.append("## Executive Summary")
    md_parts.append("")
    if report.total_findings == 0:
        md_parts.append(
            f"This codebase has been thoroughly analyzed using a multi-pass review approach. "
            f"The review detected **{len(report.detected_components)} component type(s)** "
            f"and **no critical issues were found**. The code appears to be well-structured and follows "
            f"good practices in the areas analyzed."
        )
    else:
        md_parts.append(
            f"This report provides a comprehensive codebase analysis using a "
            f"multi-pass review approach. The review detected **{len(report.detected_components)} component type(s)** "
            f"and identified **{report.total_findings} total issue(s)** across all review passes."
        )
    md_parts.append("")

    md_parts.append("### Key Metrics")
    md_parts.append("")
    md_parts.append(f"- **Critical Issues**: {critical_count}")
    md_parts.append(f"- **Major Issues**: {major_count}")
    md_parts.append(f"- **Total Issues**: {report.total_findings}")
    md_parts.append(
        f"- **Detected Components**: {', '.join(report.detected_components)}"
    )
    md_parts.append(
        f"- **Review Duration**: {report.execution_time_seconds:.2f} seconds"
    )
    md_parts.append("")

    # Detected Components
    md_parts.append("## Detected Components")
    md_parts.append("")
    if report.detected_components:
        for component in report.detected_components:
            md_parts.append(f"- **{component.title()}**: Detected and analyzed")
        md_parts.append("")
    else:
        md_parts.append(
            "*No specific components detected. General analysis performed.*"
        )
        md_parts.append("")

    # Linter Results Section
    if linter_results:
        md_parts.append("## Static Analysis Results")
        md_parts.append("")

        tools = linter_results.get("tools", {})
        summary = linter_results.get("summary", {})

        if summary:
            md_parts.append(f"**Total Issues**: {summary.get('total_issues', 0)}")
            md_parts.append(f"**Tools Run**: {summary.get('tools_run', 0)}")
            md_parts.append(
                f"**Successfully Completed**: {summary.get('tools_successful', 0)}"
            )
            md_parts.append("")

        # Flake8
        if "flake8" in tools:
            flake8 = tools["flake8"]
            md_parts.append("### Flake8 (Code Style)")
            md_parts.append("")
            if flake8.get("success"):
                md_parts.append(f"- **Total Issues**: {flake8.get('issues_count', 0)}")
                if flake8.get("issues"):
                    md_parts.append("")
                    md_parts.append("**Example Issues:**")
                    for issue in flake8["issues"][:10]:  # Top 10 issues
                        file_path = _clean_path(issue.get("file", "N/A"))
                        # Show full error message without truncation
                        error_message = issue.get("message", "N/A")
                        md_parts.append(
                            f"- `{file_path}:{issue.get('line', 'N/A')}` - {error_message}"
                        )
                md_parts.append("")
            else:
                md_parts.append(
                    f"- **Status**: {'Installed' if flake8.get('error') != 'Not installed' else 'Not Installed'}"
                )
                if flake8.get("error"):
                    md_parts.append(f"- **Note**: {flake8['error']}")
                md_parts.append("")

        # Pylint
        if "pylint" in tools:
            pylint = tools["pylint"]
            md_parts.append("### Pylint (Code Quality)")
            md_parts.append("")
            if pylint.get("success"):
                md_parts.append(f"- **Score**: {pylint.get('score', 'N/A')}/10")
                md_parts.append(f"- **Total Issues**: {pylint.get('issues_count', 0)}")
                if pylint.get("issues"):
                    md_parts.append("")
                    md_parts.append("**Example Issues:**")
                    for issue in pylint["issues"][:10]:  # Top 10 issues
                        cleaned_issue = _clean_linter_issue_path(str(issue))
                        # Wrap issue in backticks for code formatting, no truncation to show full error
                        md_parts.append(f"- `{cleaned_issue}`")
                md_parts.append("")
            else:
                md_parts.append(
                    f"- **Status**: {'Installed' if pylint.get('error') != 'Not installed' else 'Not Installed'}"
                )
                if pylint.get("error"):
                    md_parts.append(f"- **Note**: {pylint['error']}")
                md_parts.append("")

        # MyPy
        if "mypy" in tools:
            mypy = tools["mypy"]
            md_parts.append("### MyPy (Type Checking)")
            md_parts.append("")
            if mypy.get("success"):
                md_parts.append(f"- **Files Checked**: {mypy.get('files_checked', 0)}")
                md_parts.append(f"- **Errors**: {mypy.get('errors', 0)}")
                if mypy.get("issues"):
                    md_parts.append("")
                    md_parts.append("**Example Errors:**")
                    for issue in mypy["issues"][:10]:  # Top 10 errors
                        cleaned_issue = _clean_linter_issue_path(str(issue))
                        # Wrap issue in backticks for code formatting, no truncation to show full error
                        md_parts.append(f"- `{cleaned_issue}`")
                md_parts.append("")
            else:
                md_parts.append(
                    f"- **Status**: {'Installed' if mypy.get('error') != 'Not installed' else 'Not Installed'}"
                )
                if mypy.get("error"):
                    md_parts.append(f"- **Note**: {mypy['error']}")
                md_parts.append("")

        # Black
        if "black" in tools:
            black = tools["black"]
            md_parts.append("### Black (Formatting)")
            md_parts.append("")
            if black.get("success"):
                md_parts.append(f"- **Files Checked**: {black.get('files_checked', 0)}")
                md_parts.append(
                    f"- **Needs Reformatting**: {black.get('needs_reformatting', 0)}"
                )
                md_parts.append("")
            else:
                md_parts.append(
                    f"- **Status**: {'Installed' if black.get('error') != 'Not installed' else 'Not Installed'}"
                )
                if black.get("error"):
                    md_parts.append(f"- **Note**: {black['error']}")
                md_parts.append("")

        # isort
        if "isort" in tools:
            isort = tools["isort"]
            md_parts.append("### isort (Import Sorting)")
            md_parts.append("")
            if isort.get("success"):
                md_parts.append(f"- **Files Checked**: {isort.get('files_checked', 0)}")
                md_parts.append(f"- **Needs Sorting**: {isort.get('needs_sorting', 0)}")
                md_parts.append("")
            else:
                md_parts.append(
                    f"- **Status**: {'Installed' if isort.get('error') != 'Not installed' else 'Not Installed'}"
                )
                if isort.get("error"):
                    md_parts.append(f"- **Note**: {isort['error']}")
                md_parts.append("")

    # Pass 1: Architecture Overview
    md_parts.append("## Pass 1: Architecture Overview")
    md_parts.append("")
    if report.pass_1:
        if report.pass_1.summary:
            md_parts.append(f"{report.pass_1.summary}")
            md_parts.append("")
        elif report.total_findings == 0:
            # Provide informative summary when no issues found
            md_parts.append(
                "The architecture review examined the overall codebase structure, "
                "design patterns, and architectural decisions. No critical architectural issues were identified."
            )
            md_parts.append("")

        md_parts.append("### Issues Found")
        md_parts.append("")
        if report.pass_1.findings:
            for finding in report.pass_1.findings:
                severity_emoji = {
                    "critical": "🔴",
                    "major": "🟠",
                    "minor": "🟡",
                }.get(
                    finding.severity.value
                    if hasattr(finding.severity, "value")
                    else str(finding.severity).lower(),
                    "⚪",
                )

                title = _truncate_title(finding.title)
                md_parts.append(
                    f"#### {severity_emoji} [{finding.severity.value.upper() if hasattr(finding.severity, 'value') else str(finding.severity).upper()}] {title}"
                )
                md_parts.append("")
                md_parts.append(f"**Description**: {finding.description}")
                if finding.location:
                    cleaned_location = _clean_path(str(finding.location))
                    md_parts.append(f"**Location**: {cleaned_location}")
                if finding.recommendation:
                    md_parts.append(f"**Recommendation**: {finding.recommendation}")
                if finding.effort_estimate:
                    md_parts.append(f"**Effort Estimate**: {finding.effort_estimate}")
                md_parts.append("")
        else:
            md_parts.append("*No issues found in Pass 1.*")
            md_parts.append("")

        if report.pass_1.recommendations:
            md_parts.append("### Recommendations")
            md_parts.append("")
            for i, rec in enumerate(report.pass_1.recommendations, 1):
                md_parts.append(f"{i}. {rec}")
            md_parts.append("")
    else:
        md_parts.append("*Pass 1 (Architecture Overview) was not completed.*")
        md_parts.append("")

    # Pass 2: Component Analysis
    md_parts.append("## Pass 2: Component Analysis")
    md_parts.append("")
    if report.pass_2_results:
        for component_type, findings in report.pass_2_results.items():
            md_parts.append(f"### {component_type.upper()} Component")
            md_parts.append("")

            if findings.summary:
                md_parts.append(f"{findings.summary}")
                md_parts.append("")

            if findings.findings:
                md_parts.append("#### Issues Found")
                md_parts.append("")
                for finding in findings.findings:
                    severity_emoji = {
                        "critical": "🔴",
                        "major": "🟠",
                        "minor": "🟡",
                    }.get(
                        finding.severity.value
                        if hasattr(finding.severity, "value")
                        else str(finding.severity).lower(),
                        "⚪",
                    )

                    title = _truncate_title(finding.title)
                    md_parts.append(
                        f"##### {severity_emoji} [{finding.severity.value.upper() if hasattr(finding.severity, 'value') else str(finding.severity).upper()}] {title}"
                    )
                    md_parts.append("")
                    md_parts.append(f"**Description**: {finding.description}")
                    if finding.location:
                        cleaned_location = _clean_path(str(finding.location))
                        md_parts.append(f"**Location**: {cleaned_location}")
                    if finding.recommendation:
                        md_parts.append(f"**Recommendation**: {finding.recommendation}")
                    if finding.effort_estimate:
                        md_parts.append(
                            f"**Effort Estimate**: {finding.effort_estimate}"
                        )
                    md_parts.append("")
            else:
                md_parts.append("*No issues found for this component.*")
                md_parts.append("")

            if findings.recommendations:
                md_parts.append("#### Recommendations")
                md_parts.append("")
                for i, rec in enumerate(findings.recommendations, 1):
                    md_parts.append(f"{i}. {rec}")
                md_parts.append("")
    else:
        md_parts.append("*Component analysis was not performed.*")
        md_parts.append("")

    # Pass 3: Synthesis
    md_parts.append("## Pass 3: Synthesis and Integration")
    md_parts.append("")
    if report.pass_3:
        if report.pass_3.summary:
            md_parts.append(f"{report.pass_3.summary}")
            md_parts.append("")

        if report.pass_3.findings:
            md_parts.append("### Final Issues")
            md_parts.append("")
            for finding in report.pass_3.findings:
                severity_emoji = {
                    "critical": "🔴",
                    "major": "🟠",
                    "minor": "🟡",
                }.get(
                    finding.severity.value
                    if hasattr(finding.severity, "value")
                    else str(finding.severity).lower(),
                    "⚪",
                )

                title = _truncate_title(finding.title)
                md_parts.append(
                    f"#### {severity_emoji} [{finding.severity.value.upper() if hasattr(finding.severity, 'value') else str(finding.severity).upper()}] {title}"
                )
                md_parts.append("")
                md_parts.append(f"**Description**: {finding.description}")
                if finding.location:
                    cleaned_location = _clean_path(str(finding.location))
                    md_parts.append(f"**Location**: {cleaned_location}")
                if finding.recommendation:
                    md_parts.append(f"**Recommendation**: {finding.recommendation}")
                if finding.effort_estimate:
                    md_parts.append(f"**Effort Estimate**: {finding.effort_estimate}")
                md_parts.append("")

        if report.pass_3.recommendations:
            md_parts.append("### Priority Roadmap")
            md_parts.append("")
            md_parts.append(
                "Based on comprehensive analysis, below are prioritized recommendations:"
            )
            md_parts.append("")
            for i, rec in enumerate(report.pass_3.recommendations, 1):
                # Clean recommendation text and ensure proper line breaks
                rec_text = str(rec).strip()
                # Split long recommendations into lines if needed
                if len(rec_text) > 150:
                    # Try to break at sentence boundaries
                    sentences = rec_text.split(". ")
                    if len(sentences) > 1:
                        rec_lines = [
                            f"{s}."
                            if not s.endswith(".") and i < len(sentences) - 1
                            else s
                            for i, s in enumerate(sentences)
                            if s.strip()
                        ]
                        for j, rec_line in enumerate(rec_lines):
                            if j == 0:
                                md_parts.append(f"**Priority {i}**: {rec_line}")
                            else:
                                md_parts.append(f"  {rec_line}")
                    else:
                        md_parts.append(f"**Priority {i}**: {rec_text}")
                else:
                    md_parts.append(f"**Priority {i}**: {rec_text}")
                md_parts.append("")
            md_parts.append("")
    else:
        md_parts.append("*Pass 3 (Synthesis) was not completed.*")
        md_parts.append("")

    # Model Reasoning (if available)
    if review_logger:
        reasoning_log = review_logger.get_reasoning_log()
        if reasoning_log:
            md_parts.append("## Model Reasoning")
            md_parts.append("")
            md_parts.append(
                "Below are key reasoning stages from the model during analysis:"
            )
            md_parts.append("")
            for entry in reasoning_log[-5:]:  # Last 5 reasoning entries
                md_parts.append(f"### {entry.get('pass_name', 'Unknown')}")
                md_parts.append("")
                if entry.get("context"):
                    md_parts.append(f"**Context**: {entry['context']}")
                    md_parts.append("")
                md_parts.append(f"{entry.get('reasoning', 'N/A')}")
                md_parts.append("")

            # Add detailed reasoning section with model responses
            model_responses = review_logger.get_model_responses()
            if model_responses:
                md_parts.append("### Detailed Reasoning Analysis")
                md_parts.append("")
                for i, resp in enumerate(
                    model_responses[-3:], 1
                ):  # Last 3 model responses
                    pass_name = resp.get("pass_name", "Unknown")
                    prompt_preview = (
                        resp.get("prompt", "")[:300] + "..."
                        if len(resp.get("prompt", "")) > 300
                        else resp.get("prompt", "")
                    )
                    response_preview = (
                        resp.get("response", "")[:500] + "..."
                        if len(resp.get("response", "")) > 500
                        else resp.get("response", "")
                    )

                    md_parts.append(f"#### Interaction {i}: {pass_name}")
                    md_parts.append("")
                    md_parts.append("**Model Request:**")
                    md_parts.append("```")
                    md_parts.append(prompt_preview)
                    md_parts.append("```")
                    md_parts.append("")
                    md_parts.append("**Model Response:**")
                    md_parts.append("```")
                    md_parts.append(response_preview)
                    md_parts.append("```")
                    md_parts.append("")

                    tokens = resp.get("tokens_used", {})
                    if tokens:
                        md_parts.append(
                            f"*Tokens: {tokens.get('input_tokens', 0)} input, {tokens.get('output_tokens', 0)} output*"
                        )
                        md_parts.append("")

    # Statistics Section
    md_parts.append("## Review Statistics")
    md_parts.append("")
    if review_logger:
        model_responses = review_logger.get_model_responses()
        total_time_ms = sum(
            resp.get("execution_time_ms", 0) or 0 for resp in model_responses
        )

        md_parts.append("### Execution Time")
        md_parts.append("")
        md_parts.append(
            f"- **Total Review Duration**: {report.execution_time_seconds:.2f} seconds"
        )
        if total_time_ms > 0:
            md_parts.append(
                f"- **Model Response Time**: {total_time_ms / 1000:.2f} seconds"
            )
        md_parts.append("")

    md_parts.append("### Issues Summary")
    md_parts.append("")
    md_parts.append(f"- **Critical Issues**: {critical_count}")
    md_parts.append(f"- **Major Issues**: {major_count}")
    md_parts.append(f"- **Total Issues**: {report.total_findings}")
    md_parts.append("")

    # Footer
    md_parts.append("---")
    md_parts.append("")
    md_parts.append(
        f"*Generated by multi-pass code review system v1.0 | Session: {report.session_id}*"
    )

    return "\n".join(md_parts)
