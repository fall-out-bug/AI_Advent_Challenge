"""Domain models representing review pass results and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class PassFindings:
    pass_name: str
    status: str = "completed"
    error: Optional[str] = None
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MultiPassReport:
    session_id: str
    assignment_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    pass_1: Optional[PassFindings] = None
    pass_2: Optional[PassFindings] = None
    pass_3: Optional[PassFindings] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def passes(self) -> List[PassFindings]:
        """Return list of completed passes."""
        return [p for p in [self.pass_1, self.pass_2, self.pass_3] if p]
