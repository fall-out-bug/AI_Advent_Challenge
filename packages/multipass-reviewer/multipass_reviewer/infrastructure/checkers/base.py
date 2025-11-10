"""Base helpers for modular reviewer checkers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol

from multipass_reviewer.infrastructure.monitoring import metrics


@dataclass(slots=True)
class CheckerResult:
    """Normalized output from a checker run."""

    checker: str
    issues: List[Dict[str, Any]] = field(default_factory=list)
    severity: str = "info"
    metadata: Dict[str, Any] = field(default_factory=dict)


class CheckerProtocol(Protocol):
    async def run(self, codebase: Dict[str, str]) -> CheckerResult:
        """Execute checker against provided files."""
        ...


class BaseChecker:
    """Shared logic for concrete checkers."""

    name: str = "base"
    default_severity: str = "info"

    async def run(self, codebase: Dict[str, str]) -> CheckerResult:
        start = time.perf_counter()
        issues, metadata = self._collect(codebase)
        severity = self._derive_severity(issues)
        result = CheckerResult(
            checker=self.name,
            issues=issues,
            severity=severity,
            metadata=metadata,
        )
        metrics.observe_checker_runtime(self.name, time.perf_counter() - start)
        metrics.observe_checker_findings(self.name, result.issues)
        return result

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        raise NotImplementedError

    def _derive_severity(self, issues: List[Dict[str, Any]]) -> str:
        if not issues:
            return "info"
        return self.default_severity
