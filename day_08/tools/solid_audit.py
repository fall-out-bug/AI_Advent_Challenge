"""
SOLID Principles Audit Tool for Token Analysis System.

This module provides comprehensive analysis of SOLID principles compliance
across the codebase, identifying violations and suggesting improvements.
"""

import ast
import inspect
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class ViolationType(Enum):
    """Types of SOLID principle violations."""
    SRP = "Single Responsibility Principle"
    OCP = "Open/Closed Principle"
    LSP = "Liskov Substitution Principle"
    ISP = "Interface Segregation Principle"
    DIP = "Dependency Inversion Principle"


@dataclass
class Violation:
    """Represents a SOLID principle violation."""
    file_path: str
    line_number: int
    class_name: str
    violation_type: ViolationType
    description: str
    severity: str  # low, medium, high
    suggestion: str


class SOLIDAuditor:
    """
    Auditor for SOLID principles compliance.
    
    Analyzes Python code for violations of SOLID principles and provides
    recommendations for improvement.
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize SOLID auditor.
        
        Args:
            base_path: Base path of the project to audit
        """
        self.base_path = base_path
        self.violations: List[Violation] = []
        self.class_info: Dict[str, Dict[str, Any]] = {}
    
    def audit_codebase(self) -> Dict[str, List[Violation]]:
        """
        Audit the entire codebase for SOLID violations.
        
        Returns:
            Dict[str, List[Violation]]: Violations grouped by principle
        """
        self.violations.clear()
        self.class_info.clear()
        
        # Find all Python files
        python_files = list(self.base_path.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
            
            try:
                self._audit_file(file_path)
            except Exception as e:
                print(f"Error auditing {file_path}: {e}")
        
        # Group violations by principle
        violations_by_principle = {}
        for violation_type in ViolationType:
            violations_by_principle[violation_type.value] = [
                v for v in self.violations if v.violation_type == violation_type
            ]
        
        return violations_by_principle
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".git",
            "venv",
            "env",
            "tests",
            "htmlcov",
            ".pytest_cache"
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _audit_file(self, file_path: Path) -> None:
        """Audit a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._audit_class(file_path, node, content)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _audit_class(self, file_path: Path, class_node: ast.ClassDef, content: str) -> None:
        """Audit a single class for SOLID violations."""
        class_name = class_node.name
        lines = content.split('\n')
        
        # Extract class information
        methods = [n.name for n in class_node.body if isinstance(n, ast.FunctionDef)]
        attributes = [n.targets[0].id for n in class_node.body 
                     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)]
        
        self.class_info[class_name] = {
            'methods': methods,
            'attributes': attributes,
            'line_count': len([n for n in class_node.body if isinstance(n, ast.FunctionDef)]),
            'file_path': str(file_path)
        }
        
        # Check SRP violations
        self._check_srp_violations(file_path, class_node, class_name, methods)
        
        # Check OCP violations
        self._check_ocp_violations(file_path, class_node, class_name)
        
        # Check ISP violations
        self._check_isp_violations(file_path, class_node, class_name, methods)
        
        # Check DIP violations
        self._check_dip_violations(file_path, class_node, class_name)
    
    def _check_srp_violations(self, file_path: Path, class_node: ast.ClassDef, 
                            class_name: str, methods: List[str]) -> None:
        """Check for Single Responsibility Principle violations."""
        
        # Check for too many methods (indicates multiple responsibilities)
        if len(methods) > 10:
            self.violations.append(Violation(
                file_path=str(file_path),
                line_number=class_node.lineno,
                class_name=class_name,
                violation_type=ViolationType.SRP,
                description=f"Class has {len(methods)} methods, suggesting multiple responsibilities",
                severity="medium",
                suggestion="Consider splitting into multiple classes with single responsibilities"
            ))
        
        # Check for mixed concerns in method names
        concerns = {
            'io': ['read', 'write', 'load', 'save', 'file', 'http', 'request'],
            'validation': ['validate', 'check', 'verify'],
            'calculation': ['calculate', 'compute', 'process', 'analyze'],
            'formatting': ['format', 'print', 'display', 'render'],
            'business': ['execute', 'run', 'perform', 'handle']
        }
        
        method_concerns = {concern: 0 for concern in concerns}
        
        for method in methods:
            method_lower = method.lower()
            for concern, keywords in concerns.items():
                if any(keyword in method_lower for keyword in keywords):
                    method_concerns[concern] += 1
        
        # If class handles more than 2 different concerns, it might violate SRP
        active_concerns = [concern for concern, count in method_concerns.items() if count > 0]
        if len(active_concerns) > 2:
            self.violations.append(Violation(
                file_path=str(file_path),
                line_number=class_node.lineno,
                class_name=class_name,
                violation_type=ViolationType.SRP,
                description=f"Class handles multiple concerns: {', '.join(active_concerns)}",
                severity="high",
                suggestion="Split class into separate classes, each handling one concern"
            ))
    
    def _check_ocp_violations(self, file_path: Path, class_node: ast.ClassDef, class_name: str) -> None:
        """Check for Open/Closed Principle violations."""
        
        # Look for hardcoded if/elif chains that could be replaced with polymorphism
        for node in ast.walk(class_node):
            if isinstance(node, ast.If):
                if self._has_hardcoded_conditions(node):
                    self.violations.append(Violation(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        class_name=class_name,
                        violation_type=ViolationType.OCP,
                        description="Hardcoded conditional logic that could be replaced with polymorphism",
                        severity="medium",
                        suggestion="Use strategy pattern or factory pattern for extensibility"
                    ))
    
    def _has_hardcoded_conditions(self, if_node: ast.If) -> bool:
        """Check if if statement has hardcoded conditions."""
        # Simple heuristic: check for string comparisons in conditions
        if isinstance(if_node.test, ast.Compare):
            for comparator in if_node.test.comparators:
                if isinstance(comparator, ast.Str):
                    return True
        return False
    
    def _check_isp_violations(self, file_path: Path, class_node: ast.ClassDef, 
                            class_name: str, methods: List[str]) -> None:
        """Check for Interface Segregation Principle violations."""
        
        # Check for classes with too many methods (fat interfaces)
        if len(methods) > 15:
            self.violations.append(Violation(
                file_path=str(file_path),
                line_number=class_node.lineno,
                class_name=class_name,
                violation_type=ViolationType.ISP,
                description=f"Class has {len(methods)} methods, creating a fat interface",
                severity="medium",
                suggestion="Split interface into smaller, focused interfaces"
            ))
        
        # Check for methods that are not used together (cohesion issues)
        # This is a simplified check - in practice, you'd need more sophisticated analysis
        if len(methods) > 8:
            # Look for method name patterns that suggest different responsibilities
            io_methods = [m for m in methods if any(keyword in m.lower() 
                          for keyword in ['read', 'write', 'load', 'save'])]
            calc_methods = [m for m in methods if any(keyword in m.lower() 
                           for keyword in ['calculate', 'compute', 'process'])]
            
            if io_methods and calc_methods and len(io_methods) + len(calc_methods) > len(methods) * 0.6:
                self.violations.append(Violation(
                    file_path=str(file_path),
                    line_number=class_node.lineno,
                    class_name=class_name,
                    violation_type=ViolationType.ISP,
                    description="Class mixes I/O operations with calculations",
                    severity="low",
                    suggestion="Consider separating I/O and calculation concerns"
                ))
    
    def _check_dip_violations(self, file_path: Path, class_node: ast.ClassDef, class_name: str) -> None:
        """Check for Dependency Inversion Principle violations."""
        
        # Look for direct instantiation of concrete classes
        for node in ast.walk(class_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    # Direct instantiation of concrete classes
                    if node.func.id in ['TokenCounter', 'SimpleTextCompressor', 'TokenAnalysisClient']:
                        self.violations.append(Violation(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            class_name=class_name,
                            violation_type=ViolationType.DIP,
                            description=f"Direct instantiation of concrete class: {node.func.id}",
                            severity="medium",
                            suggestion="Use dependency injection or factory pattern"
                        ))
    
    def generate_report(self) -> str:
        """Generate a comprehensive SOLID audit report."""
        violations_by_principle = self.audit_codebase()
        
        report = []
        report.append("=" * 80)
        report.append("SOLID PRINCIPLES AUDIT REPORT")
        report.append("=" * 80)
        report.append("")
        
        total_violations = sum(len(violations) for violations in violations_by_principle.values())
        report.append(f"Total violations found: {total_violations}")
        report.append("")
        
        for principle, violations in violations_by_principle.items():
            report.append(f"{principle}:")
            report.append("-" * len(principle))
            
            if not violations:
                report.append("✅ No violations found")
            else:
                for violation in violations:
                    report.append(f"  📍 {violation.file_path}:{violation.line_number}")
                    report.append(f"     Class: {violation.class_name}")
                    report.append(f"     Severity: {violation.severity}")
                    report.append(f"     Issue: {violation.description}")
                    report.append(f"     Suggestion: {violation.suggestion}")
                    report.append("")
            
            report.append("")
        
        # Summary statistics
        report.append("SUMMARY STATISTICS:")
        report.append("-" * 20)
        
        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        for violations in violations_by_principle.values():
            for violation in violations:
                severity_counts[violation.severity] += 1
        
        report.append(f"High severity: {severity_counts['high']}")
        report.append(f"Medium severity: {severity_counts['medium']}")
        report.append(f"Low severity: {severity_counts['low']}")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 15)
        
        if severity_counts['high'] > 0:
            report.append("🔴 Priority: Address high severity violations first")
        
        if total_violations > 20:
            report.append("⚠️  Consider refactoring classes with many violations")
        
        report.append("💡 Focus on SRP violations for immediate impact")
        report.append("🔧 Implement dependency injection for DIP violations")
        report.append("📐 Use interfaces and abstractions for ISP violations")
        
        return "\n".join(report)
    
    def get_violations_by_file(self) -> Dict[str, List[Violation]]:
        """Get violations grouped by file."""
        violations_by_file = {}
        
        for violation in self.violations:
            file_path = violation.file_path
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)
        
        return violations_by_file
    
    def get_most_problematic_classes(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get classes with the most violations."""
        class_violations = {}
        
        for violation in self.violations:
            class_name = violation.class_name
            class_violations[class_name] = class_violations.get(class_name, 0) + 1
        
        return sorted(class_violations.items(), key=lambda x: x[1], reverse=True)[:limit]


def run_solid_audit(project_path: str) -> str:
    """
    Run SOLID audit on the project.
    
    Args:
        project_path: Path to the project root
        
    Returns:
        str: Audit report
    """
    auditor = SOLIDAuditor(Path(project_path))
    return auditor.generate_report()


if __name__ == "__main__":
    # Run audit on current project
    import sys
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    report = run_solid_audit(project_path)
    print(report)
