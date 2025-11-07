"""Formatter for static analysis results in markdown reports."""

import re
from typing import Any, Dict, List


def _clean_path(path: str) -> str:
    """Clean file path by removing temporary directory prefixes.

    Purpose:
        Removes temporary directory prefixes like /tmp/homework_review_*/
        from file paths to make them relative and readable.

    Args:
        path: File path that may contain temp directory prefix

    Returns:
        Cleaned relative path
    """
    if not path or path == "N/A":
        return path
    # Remove common temp directory patterns
    path = re.sub(r'/tmp/homework_review_[^/]+/', '', path)
    path = re.sub(r'/tmp/[^/]+/', '', path)
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
    """
    if not issue_text:
        return issue_text
    # Extract path (part before first colon that contains path-like content)
    path_match = re.match(r'^(/tmp/[^:]+|/[^:]+)', issue_text)
    if path_match:
        full_path = path_match.group(1)
        cleaned_path = _clean_path(full_path)
        return issue_text.replace(full_path, cleaned_path, 1)
    return issue_text


def format_static_analysis_markdown(linter_results: Dict[str, Any]) -> str:
    """Format static analysis results as markdown.

    Purpose:
        Converts linter results dictionary to markdown format
        matching the example reports structure.

    Args:
        linter_results: Dictionary with linter results from CodeQualityChecker

    Returns:
        Markdown string with static analysis results

    Example:
        results = checker.run_all_checks()
        markdown = format_static_analysis_markdown(results)
    """
    if not linter_results:
        return ""

    md_parts: List[str] = []

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

    return "\n".join(md_parts)

