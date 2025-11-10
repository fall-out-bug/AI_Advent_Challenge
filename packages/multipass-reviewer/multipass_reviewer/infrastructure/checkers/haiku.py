"""Checker producing haiku summaries for reports."""

from __future__ import annotations

from typing import Dict

from multipass_reviewer.infrastructure.checkers.base import BaseChecker


class HaikuChecker(BaseChecker):
    """Generate a simple deterministic haiku."""

    name = "haiku"
    default_severity = "info"

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        summary = codebase.get("summary") or "Architecture stable"
        lines = [
            "Tests whisper softly",
            summary.strip(),
            "Quality takes root",
        ]
        metadata: dict[str, object] = {"haiku": "\n".join(lines)}
        return [], metadata
