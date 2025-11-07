"""Diff analyzer service for code comparison."""

from __future__ import annotations

import ast
import difflib
import logging

from src.domain.value_objects.code_diff import CodeDiff

logger = logging.getLogger(__name__)


class DiffAnalyzer:
    """Analyzes code differences using text and AST analysis.

    Purpose:
        Compares two code versions using both textual diff and
        AST-based semantic analysis for Python code.

    Example:
        analyzer = DiffAnalyzer()
        diff = analyzer.analyze(old_code, new_code)
        print(f"Added {diff.lines_added} lines")
    """

    def analyze(self, old_code: str, new_code: str) -> CodeDiff:
        """Analyze differences between two code versions.

        Args:
            old_code: Previous version of code
            new_code: New version of code

        Returns:
            CodeDiff with analysis results
        """
        text_diff = self._compute_text_diff(old_code, new_code)
        ast_changes = self._analyze_ast_changes(old_code, new_code)

        total_lines = max(
            len(old_code.splitlines()), len(new_code.splitlines()), 1
        )
        change_ratio = (text_diff.lines_changed / total_lines) * 100.0

        return CodeDiff(
            lines_added=text_diff.lines_added,
            lines_removed=text_diff.lines_removed,
            lines_changed=text_diff.lines_changed,
            change_ratio=min(change_ratio, 100.0),
            functions_added=ast_changes.functions_added,
            functions_removed=ast_changes.functions_removed,
            classes_changed=ast_changes.classes_changed,
            imports_added=ast_changes.imports_added,
            imports_removed=ast_changes.imports_removed,
            complexity_delta=ast_changes.complexity_delta,
            has_refactor=ast_changes.has_refactor,
            has_new_imports=len(ast_changes.imports_added) > 0,
        )

    def _compute_text_diff(
        self, old_code: str, new_code: str
    ) -> _TextDiffResult:
        """Compute textual diff using difflib.

        Args:
            old_code: Previous code
            new_code: New code

        Returns:
            TextDiffResult with line counts
        """
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))

        lines_added = sum(
            1
            for line in diff
            if line.startswith("+") and not line.startswith("+++")
        )
        lines_removed = sum(
            1
            for line in diff
            if line.startswith("-") and not line.startswith("---")
        )
        lines_changed = max(lines_added, lines_removed)

        return _TextDiffResult(
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_changed=lines_changed,
        )

    def _analyze_ast_changes(
        self, old_code: str, new_code: str
    ) -> _ASTChanges:
        """Analyze AST-level changes for Python code.

        Args:
            old_code: Previous code
            new_code: New code

        Returns:
            ASTChanges with semantic analysis
        """
        old_ast = self._parse_ast_safe(old_code)
        new_ast = self._parse_ast_safe(new_code)

        if not old_ast or not new_ast:
            return _ASTChanges()

        old_functions = self._extract_functions(old_ast)
        new_functions = self._extract_functions(new_ast)
        old_classes = self._extract_classes(old_ast)
        new_classes = self._extract_classes(new_ast)
        old_imports = self._extract_imports(old_ast)
        new_imports = self._extract_imports(new_ast)

        functions_added = [
            name for name in new_functions if name not in old_functions
        ]
        functions_removed = [
            name for name in old_functions if name not in new_functions
        ]
        classes_changed = [
            name
            for name in new_classes
            if name in old_classes and new_classes[name] != old_classes[name]
        ]
        imports_added = [
            imp for imp in new_imports if imp not in old_imports
        ]
        imports_removed = [
            imp for imp in old_imports if imp not in new_imports
        ]

        has_refactor = (
            len(functions_added) > 0
            or len(functions_removed) > 0
            or len(classes_changed) > 0
        )

        complexity_delta = self._estimate_complexity_delta(
            old_ast, new_ast
        )

        return _ASTChanges(
            functions_added=functions_added,
            functions_removed=functions_removed,
            classes_changed=classes_changed,
            imports_added=imports_added,
            imports_removed=imports_removed,
            complexity_delta=complexity_delta,
            has_refactor=has_refactor,
        )

    def _parse_ast_safe(self, code: str) -> ast.Module | None:
        """Parse code to AST, return None on error.

        Args:
            code: Python code to parse

        Returns:
            AST module or None if parsing fails
        """
        if not code.strip():
            return None
        try:
            return ast.parse(code)
        except SyntaxError:
            logger.debug("Failed to parse code as Python AST")
            return None

    def _extract_functions(self, node: ast.Module) -> list[str]:
        """Extract function names from AST.

        Args:
            node: AST module node

        Returns:
            List of function names
        """
        functions: list[str] = []
        for item in ast.walk(node):
            if isinstance(item, ast.FunctionDef):
                functions.append(item.name)
        return functions

    def _extract_classes(self, node: ast.Module) -> dict[str, int]:
        """Extract class names and method counts from AST.

        Args:
            node: AST module node

        Returns:
            Dictionary mapping class names to method counts
        """
        classes: dict[str, int] = {}
        for item in ast.walk(node):
            if isinstance(item, ast.ClassDef):
                method_count = sum(
                    1
                    for child in ast.walk(item)
                    if isinstance(child, ast.FunctionDef)
                )
                classes[item.name] = method_count
        return classes

    def _extract_imports(self, node: ast.Module) -> list[str]:
        """Extract import statements from AST.

        Args:
            node: AST module node

        Returns:
            List of import strings
        """
        imports: list[str] = []
        for item in ast.walk(node):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    imports.append(alias.name)
            elif isinstance(item, ast.ImportFrom):
                module = item.module or ""
                for alias in item.names:
                    imports.append(f"{module}.{alias.name}")
        return imports

    def _estimate_complexity_delta(
        self, old_ast: ast.Module, new_ast: ast.Module
    ) -> int:
        """Estimate change in cyclomatic complexity.

        Args:
            old_ast: Previous AST
            new_ast: New AST

        Returns:
            Estimated complexity delta
        """
        old_complexity = self._count_decision_points(old_ast)
        new_complexity = self._count_decision_points(new_ast)
        return new_complexity - old_complexity

    def _count_decision_points(self, node: ast.Module) -> int:
        """Count decision points (if, for, while, etc.) in AST.

        Args:
            node: AST module node

        Returns:
            Count of decision points
        """
        count = 0
        for item in ast.walk(node):
            if isinstance(
                item,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.Try,
                    ast.With,
                    ast.And,
                    ast.Or,
                ),
            ):
                count += 1
        return count


class _TextDiffResult:
    """Internal result from text diff computation."""

    def __init__(
        self, lines_added: int, lines_removed: int, lines_changed: int
    ):
        self.lines_added = lines_added
        self.lines_removed = lines_removed
        self.lines_changed = lines_changed


class _ASTChanges:
    """Internal result from AST analysis."""

    def __init__(
        self,
        functions_added: list[str] | None = None,
        functions_removed: list[str] | None = None,
        classes_changed: list[str] | None = None,
        imports_added: list[str] | None = None,
        imports_removed: list[str] | None = None,
        complexity_delta: int = 0,
        has_refactor: bool = False,
    ):
        self.functions_added = functions_added or []
        self.functions_removed = functions_removed or []
        self.classes_changed = classes_changed or []
        self.imports_added = imports_added or []
        self.imports_removed = imports_removed or []
        self.complexity_delta = complexity_delta
        self.has_refactor = has_refactor

