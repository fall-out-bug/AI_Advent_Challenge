"""Placeholder diff analyzer for modular package."""

from __future__ import annotations

from typing import Dict


class DiffAnalyzer:
    def analyze(self, old_code: str, new_code: str) -> Dict[str, str]:
        return {"old": old_code, "new": new_code}
