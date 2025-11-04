"""Domain models for multi-pass code review system.

Following Clean Architecture principles and the Zen of Python.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PassName(Enum):
    """Enum для identification проходов."""

    PASS_1 = "pass_1"
    PASS_2_DOCKER = "pass_2_docker"
    PASS_2_AIRFLOW = "pass_2_airflow"
    PASS_2_SPARK = "pass_2_spark"
    PASS_2_MLFLOW = "pass_2_mlflow"
    PASS_3 = "pass_3"


class SeverityLevel(Enum):
    """Severity levels for findings."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


@dataclass
class Finding:
    """Single finding from code review."""

    severity: SeverityLevel
    title: str
    description: str
    location: Optional[str] = None
    recommendation: Optional[str] = None
    effort_estimate: Optional[str] = None


@dataclass
class PassFindings:
    """Container for findings from a single pass."""

    pass_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    findings: List[Finding] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pass_name": self.pass_name,
            "timestamp": self.timestamp.isoformat(),
            "findings": [self._finding_to_dict(f) for f in self.findings],
            "recommendations": self.recommendations,
            "summary": self.summary,
            "metadata": self.metadata,
        }

    @staticmethod
    def _finding_to_dict(finding: Finding) -> Dict[str, Any]:
        """Convert Finding to dictionary."""
        return {
            "severity": finding.severity.value,
            "title": finding.title,
            "description": finding.description,
            "location": finding.location,
            "recommendation": finding.recommendation,
            "effort_estimate": finding.effort_estimate,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PassFindings":
        """Create PassFindings from dictionary."""
        findings = [
            Finding(
                severity=SeverityLevel(f.get("severity", "minor")),
                title=f.get("title", ""),
                description=f.get("description", ""),
                location=f.get("location"),
                recommendation=f.get("recommendation"),
                effort_estimate=f.get("effort_estimate"),
            )
            for f in data.get("findings", [])
        ]

        return cls(
            pass_name=data["pass_name"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            findings=findings,
            recommendations=data.get("recommendations", []),
            summary=data.get("summary"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MultiPassReport:
    """Final report combining findings from all passes."""

    session_id: str
    repo_name: str
    created_at: datetime = field(default_factory=datetime.now)
    pass_1: Optional[PassFindings] = None
    pass_2_results: Dict[str, PassFindings] = field(default_factory=dict)
    pass_3: Optional[PassFindings] = None
    detected_components: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    total_findings: int = 0

    @property
    def critical_count(self) -> int:
        """Count critical issues across all passes."""
        count = 0
        for pass_findings in self._all_findings():
            count += sum(
                1 for f in pass_findings.findings if f.severity == SeverityLevel.CRITICAL
            )
        return count

    @property
    def major_count(self) -> int:
        """Count major issues across all passes."""
        count = 0
        for pass_findings in self._all_findings():
            count += sum(
                1 for f in pass_findings.findings if f.severity == SeverityLevel.MAJOR
            )
        return count

    def _all_findings(self) -> List[PassFindings]:
        """Get all PassFindings from all passes."""
        results = []
        if self.pass_1:
            results.append(self.pass_1)
        results.extend(self.pass_2_results.values())
        if self.pass_3:
            results.append(self.pass_3)
        return results

    def to_markdown(self) -> str:
        """Export report as Markdown."""
        detected_comp = ', '.join(self.detected_components) if self.detected_components else 'None'
        md = f"""# Code Review Report: {self.repo_name}

**Session ID**: {self.session_id}
**Created**: {self.created_at.isoformat()}
**Execution Time**: {self.execution_time_seconds:.1f}s

## Summary
- Detected Components: {detected_comp}
- Critical Issues: {self.critical_count}
- Major Issues: {self.major_count}
- Total Execution Time: {self.execution_time_seconds:.1f} seconds

## Pass 1: Architecture Overview
{self._pass_to_markdown(self.pass_1)}

## Pass 2: Component Analysis
{self._pass_2_to_markdown()}

## Pass 3: Synthesis & Integration
{self._pass_to_markdown(self.pass_3)}

---
*Generated by Multi-Pass Code Review System v1.0*
"""
        return md

    def _pass_to_markdown(self, pass_findings: Optional[PassFindings]) -> str:
        """Convert PassFindings to Markdown section."""
        if not pass_findings:
            return "*(No findings)*"

        md = f"\n### {pass_findings.pass_name}\n\n"
        if pass_findings.summary:
            md += f"**Summary**: {pass_findings.summary}\n\n"

        if pass_findings.findings:
            md += "**Findings**:\n"
            for finding in pass_findings.findings:
                md += (
                    f"- [{finding.severity.value.upper()}] "
                    f"{finding.title}: {finding.description}\n"
                )
                if finding.location:
                    md += f"  - Location: {finding.location}\n"
                if finding.recommendation:
                    md += f"  - Recommendation: {finding.recommendation}\n"

        if pass_findings.recommendations:
            md += "\n**Recommendations**:\n"
            for rec in pass_findings.recommendations:
                md += f"- {rec}\n"

        return md

    def _pass_2_to_markdown(self) -> str:
        """Convert Pass 2 results to Markdown."""
        if not self.pass_2_results:
            return "*(No component analysis)*"

        md = ""
        for component_type, findings in self.pass_2_results.items():
            md += f"\n### {component_type.upper()}\n"
            md += self._pass_to_markdown(findings)

        return md

    def to_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "repo_name": self.repo_name,
            "created_at": self.created_at.isoformat(),
            "detected_components": self.detected_components,
            "execution_time_seconds": self.execution_time_seconds,
            "pass_1": self.pass_1.to_dict() if self.pass_1 else None,
            "pass_2": {
                comp: findings.to_dict()
                for comp, findings in self.pass_2_results.items()
            },
            "pass_3": self.pass_3.to_dict() if self.pass_3 else None,
            "summary": {
                "critical_count": self.critical_count,
                "major_count": self.major_count,
                "total_findings": self.total_findings,
            },
        }
