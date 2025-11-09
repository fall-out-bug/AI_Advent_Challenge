"""Checker for lightweight lint-style diagnostics."""

from __future__ import annotations

from typing import Dict

from multipass_reviewer.infrastructure.checkers.base import BaseChecker


class LinterChecker(BaseChecker):
    """Detect simple whitespace and length violations."""

    name = "linter"
    default_severity = "minor"

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        issues: list[dict[str, object]] = []
        for path, content in codebase.items():
            for lineno, line in enumerate(content.splitlines(), start=1):
                if line.rstrip(" \t") != line:
                    issues.append(
                        {
                            "file": path,
                            "line": lineno,
                            "rule": "trailing_whitespace",
                            "message": f"Trailing whitespace in {path}:{lineno}",
                        }
                    )
                if len(line) > 120:
                    issues.append(
                        {
                            "file": path,
                            "line": lineno,
                            "rule": "line_too_long",
                            "message": (
                                "Line exceeds 120 characters in " f"{path}:{lineno}"
                            ),
                        }
                    )
        metadata: dict[str, object] = {"issues_found": len(issues)}
        return issues, metadata
