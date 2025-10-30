"""Adapter for code complexity analysis using radon."""
import sys
from pathlib import Path
from typing import Any, Dict

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))

from src.presentation.mcp.exceptions import MCPValidationError


class ComplexityAdapter:
    """Adapter for code complexity analysis."""

    def __init__(self) -> None:
        """Initialize complexity adapter."""
        try:
            from radon.complexity import cc_visit
            from radon.metrics import mi_visit
            self.cc_visit = cc_visit
            self.mi_visit = mi_visit
            self.has_radon = True
        except ImportError:
            self.has_radon = False

    def analyze_complexity(self, code: str, detailed: bool = True) -> Dict[str, Any]:
        """Analyze code complexity metrics."""
        self._validate_inputs(code)

        if not self.has_radon:
            return self._basic_analysis(code, detailed)

        return self._radon_analysis(code, detailed)

    def _validate_inputs(self, code: str) -> None:
        """Validate inputs."""
        if not code or not code.strip():
            raise MCPValidationError("code cannot be empty", field="code")

    def _basic_analysis(self, code: str, detailed: bool) -> Dict[str, Any]:
        """Basic analysis without radon."""
        lines = code.splitlines()
        loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
        
        # Estimate complexity based on control flow keywords
        control_flow = ["if", "elif", "else", "for", "while", "try", "except"]
        complexity = sum(code.count(cf) for cf in control_flow)
        
        recommendations = []
        if complexity > 10:
            recommendations.append("Consider splitting complex functions into smaller ones")
        if loc > 50:
            recommendations.append("Function is too long. Aim for < 50 lines")
        
        return {
            "cyclomatic_complexity": complexity,
            "cognitive_complexity": complexity,
            "lines_of_code": loc,
            "maintainability_index": self._estimate_mi(complexity, loc),
            "recommendations": recommendations,
        }

    def _radon_analysis(self, code: str, detailed: bool) -> Dict[str, Any]:
        """Analyze using radon."""
        try:
            # Cyclomatic complexity
            cc_results = self.cc_visit(code)
            max_cc = max((r.complexity for r in cc_results), default=1)
            
            # Maintainability index
            mi_score = self.mi_visit(code, multi=True)
            
            # Lines of code (excluding comments)
            lines = code.splitlines()
            loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
            
            # Generate recommendations
            recommendations = self._generate_recommendations(max_cc, loc, mi_score)
            
            result = {
                "cyclomatic_complexity": max_cc,
                "cognitive_complexity": max_cc,  # Simplified for now
                "lines_of_code": loc,
                "maintainability_index": round(mi_score, 2),
                "recommendations": recommendations,
            }
            
            if detailed and cc_results:
                result["functions"] = [
                    {"name": r.name, "complexity": r.complexity, "line": r.lineno}
                    for r in cc_results
                ]
            
            return result
            
        except Exception as e:
            raise MCPValidationError(
                f"Complexity analysis failed: {e}",
                field="code"
            )

    def _estimate_mi(self, complexity: int, loc: int) -> float:
        """Estimate maintainability index."""
        # Simplified heuristic: 100 - (complexity * 2) - (loc * 0.1)
        mi = 100 - (complexity * 2) - (loc * 0.1)
        return max(0, min(100, round(mi, 2)))

    def _generate_recommendations(
        self, complexity: int, loc: int, mi: float
    ) -> list[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        if complexity > 10:
            recommendations.append(
                "Cyclomatic complexity is high. Consider refactoring into smaller functions."
            )
        
        if loc > 50:
            recommendations.append(
                "Function is too long. Aim for < 50 lines per function."
            )
        
        if mi < 50:
            recommendations.append(
                "Maintainability index is low. Focus on improving code clarity and structure."
            )
        
        if not recommendations:
            recommendations.append("Code complexity metrics are within acceptable ranges.")
        
        return recommendations
