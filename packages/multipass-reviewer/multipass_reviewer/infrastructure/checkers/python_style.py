"""Checker enforcing Python style expectations (docstrings, etc.)."""

from __future__ import annotations

from typing import Dict

from multipass_reviewer.infrastructure.checkers.base import BaseChecker


class PythonStyleChecker(BaseChecker):
    """Inspect Python files for basic style issues."""

    name = "python_style"
    default_severity = "major"

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        issues: list[dict[str, object]] = []
        for path, content in codebase.items():
            if not path.endswith(".py"):
                continue
            lines = content.splitlines()
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("def ") and self._missing_docstring(
                    lines, idx + 1
                ):
                    issues.append(
                        {
                            "file": path,
                            "line": idx + 1,
                            "rule": "missing_docstring",
                            "message": f"Function in {path} lacks docstring",
                        }
                    )
        metadata: dict[str, object] = {"files_scanned": len(codebase)}
        return issues, metadata

    @staticmethod
    def _missing_docstring(lines: list[str], start_idx: int) -> bool:
        for line in lines[start_idx:]:
            stripped = line.strip()
            if not stripped:
                continue
            return not (stripped.startswith('"""') or stripped.startswith("'''"))
        return True
