"""Checker for simple type annotation heuristics."""

from __future__ import annotations

from typing import Dict

from multipass_reviewer.infrastructure.checkers.base import BaseChecker


class TypeChecker(BaseChecker):
    """Ensure functions declare parameter and return annotations."""

    name = "type_checker"
    default_severity = "major"

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        issues: list[dict[str, object]] = []
        for path, content in codebase.items():
            if not path.endswith(".py"):
                continue
            lines = content.splitlines()
            for lineno, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped.startswith("def "):
                    continue
                start = stripped.find("(") + 1
                end = stripped.find(")")
                params_section = stripped[start:end]
                params = [p.strip() for p in params_section.split(",") if p.strip()]
                missing_param_hints = [
                    p for p in params if (":" not in p and not p.startswith("*"))
                ]
                missing_return = "->" not in stripped
                if missing_param_hints or missing_return:
                    issues.append(
                        {
                            "file": path,
                            "line": lineno,
                            "rule": "missing_type_hints",
                            "message": (
                                f"Function in {path}:{lineno} lacks type hints"
                            ),
                        }
                    )
        metadata: dict[str, object] = {"files_scanned": len(codebase)}
        return issues, metadata
