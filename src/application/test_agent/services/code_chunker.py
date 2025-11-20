"""Code chunking service for splitting large modules into chunks."""

import ast
import logging
from pathlib import Path
from typing import List

from src.domain.test_agent.entities.code_chunk import CodeChunk
from src.domain.test_agent.interfaces.code_chunker import ICodeChunker
from src.domain.test_agent.interfaces.token_counter import ITokenCounter
from src.infrastructure.logging import get_logger


class CodeChunker:
    """
    Code chunking service implementing ICodeChunker.

    Purpose:
        Splits large Python modules into semantically meaningful chunks
        that fit within token limits.

    Example:
        >>> from src.infrastructure.test_agent.services.token_counter import TokenCounter
        >>> counter = TokenCounter()
        >>> chunker = CodeChunker(counter)
        >>> chunks = chunker.chunk_module("def hello(): pass", max_tokens=100)
        >>> len(chunks) > 0
        True
    """

    def __init__(self, token_counter: ITokenCounter) -> None:
        """Initialize code chunker.

        Args:
            token_counter: Token counter service for enforcing limits.
        """
        self.token_counter = token_counter
        self.logger = get_logger("test_agent.code_chunker")

    def chunk_module(
        self, code: str, max_tokens: int, strategy: str = "function_based"
    ) -> List[CodeChunk]:
        """Split a module into chunks that fit within token limit.

        Args:
            code: Source code of the module.
            max_tokens: Maximum tokens per chunk.
            strategy: Chunking strategy (function_based, class_based, sliding_window).

        Returns:
            List of CodeChunk entities.
        """
        if not code.strip():
            return []

        if strategy == "function_based":
            return self._chunk_by_functions(code, max_tokens)
        elif strategy == "class_based":
            return self._chunk_by_classes(code, max_tokens)
        elif strategy == "sliding_window":
            return self._chunk_sliding_window(code, max_tokens)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def chunk_package(
        self, package_path: str, max_tokens: int, strategy: str = "function_based"
    ) -> List[CodeChunk]:
        """Split a package into chunks that fit within token limit.

        Args:
            package_path: Path to the package directory.
            max_tokens: Maximum tokens per chunk.
            strategy: Chunking strategy (function_based, class_based, sliding_window).

        Returns:
            List of CodeChunk entities.
        """
        path = Path(package_path)
        if not path.exists():
            raise ValueError(f"Package path does not exist: {package_path}")

        all_chunks: List[CodeChunk] = []

        # Process all Python files in the package
        for py_file in path.rglob("*.py"):
            if py_file.name == "__pycache__":
                continue

            try:
                code = py_file.read_text(encoding="utf-8")
                file_chunks = self.chunk_module(code, max_tokens, strategy)

                # Update location to reflect actual file path
                for chunk in file_chunks:
                    chunk.location = str(py_file.relative_to(path.parent))

                all_chunks.extend(file_chunks)
            except Exception as e:
                self.logger.warning(f"Failed to process {py_file}: {e}")

        return all_chunks

    def _chunk_by_functions(self, code: str, max_tokens: int) -> List[CodeChunk]:
        """Chunk code by functions (function-based strategy).

        Args:
            code: Source code.
            max_tokens: Maximum tokens per chunk.

        Returns:
            List of CodeChunk entities.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.logger.warning(f"Failed to parse code: {e}. Using fallback chunking.")
            return self._chunk_fallback(code, max_tokens)

        # Extract imports and module-level code
        imports = self._extract_imports(tree)
        module_docstring = ast.get_docstring(tree)

        # Extract functions
        functions = [
            node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        ]

        if not functions:
            # No functions, return single chunk with all code
            return [
                CodeChunk(
                    code=code,
                    context=module_docstring or "",
                    dependencies=imports,
                    location="<module>",
                    start_line=1,
                    end_line=len(code.splitlines()),
                )
            ]

        chunks: List[CodeChunk] = []
        current_chunk_lines: List[str] = []
        current_chunk_start = 1
        current_imports = imports.copy()

        # Add imports to first chunk
        if imports:
            import_code = "\n".join(imports) + "\n\n"
            current_chunk_lines.append(import_code)

        for func in functions:
            func_code = ast.get_source_segment(code, func) or ""
            func_tokens = self.token_counter.count_tokens(func_code)

            # If function alone exceeds limit, split it (simplified)
            if func_tokens > max_tokens:
                # For now, include it anyway (could be enhanced)
                pass

            # Check if adding this function would exceed limit
            test_chunk = "\n".join(current_chunk_lines) + "\n" + func_code
            test_tokens = self.token_counter.count_tokens(test_chunk)

            if test_tokens > max_tokens and current_chunk_lines:
                # Finalize current chunk
                chunk_code = "\n".join(current_chunk_lines)
                chunks.append(
                    CodeChunk(
                        code=chunk_code,
                        context=module_docstring or "",
                        dependencies=current_imports,
                        location="<module>",
                        start_line=current_chunk_start,
                        end_line=current_chunk_start + len(chunk_code.splitlines()) - 1,
                    )
                )
                # Start new chunk
                current_chunk_lines = []
                current_chunk_start = len(chunk_code.splitlines()) + 1
                if imports:
                    current_chunk_lines.append("\n".join(imports) + "\n\n")

            current_chunk_lines.append(func_code)

        # Add final chunk
        if current_chunk_lines:
            chunk_code = "\n".join(current_chunk_lines)
            chunks.append(
                CodeChunk(
                    code=chunk_code,
                    context=module_docstring or "",
                    dependencies=current_imports,
                    location="<module>",
                    start_line=current_chunk_start,
                    end_line=current_chunk_start + len(chunk_code.splitlines()) - 1,
                )
            )

        return chunks if chunks else [self._create_fallback_chunk(code)]

    def _chunk_by_classes(self, code: str, max_tokens: int) -> List[CodeChunk]:
        """Chunk code by classes (class-based strategy).

        Args:
            code: Source code.
            max_tokens: Maximum tokens per chunk.

        Returns:
            List of CodeChunk entities.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.logger.warning(f"Failed to parse code: {e}. Using fallback chunking.")
            return self._chunk_fallback(code, max_tokens)

        # Extract imports and module-level code
        imports = self._extract_imports(tree)
        module_docstring = ast.get_docstring(tree)

        # Extract classes
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        if not classes:
            # No classes, fall back to function-based
            return self._chunk_by_functions(code, max_tokens)

        chunks: List[CodeChunk] = []
        current_chunk_lines: List[str] = []
        current_chunk_start = 1
        current_imports = imports.copy()

        # Add imports to first chunk
        if imports:
            import_code = "\n".join(imports) + "\n\n"
            current_chunk_lines.append(import_code)

        for cls in classes:
            # Get class code including all methods
            class_code = ast.get_source_segment(code, cls) or ""
            class_tokens = self.token_counter.count_tokens(class_code)

            # If class alone exceeds limit, include it anyway
            if class_tokens > max_tokens:
                # Finalize current chunk if it has content
                if current_chunk_lines and current_chunk_lines != [import_code]:
                    chunk_code = "\n".join(current_chunk_lines)
                    chunks.append(
                        CodeChunk(
                            code=chunk_code,
                            context=module_docstring or "",
                            dependencies=current_imports,
                            location="<module>",
                            start_line=current_chunk_start,
                            end_line=current_chunk_start
                            + len(chunk_code.splitlines())
                            - 1,
                        )
                    )
                    current_chunk_start += len(chunk_code.splitlines()) + 1

                # Add large class as its own chunk
                chunks.append(
                    CodeChunk(
                        code=class_code,
                        context=module_docstring or "",
                        dependencies=current_imports,
                        location="<module>",
                        start_line=cls.lineno,
                        end_line=cls.end_lineno or cls.lineno,
                    )
                )
                current_chunk_lines = []
                if imports:
                    current_chunk_lines.append("\n".join(imports) + "\n\n")
                continue

            # Check if adding this class would exceed limit
            test_chunk = "\n".join(current_chunk_lines) + "\n" + class_code
            test_tokens = self.token_counter.count_tokens(test_chunk)

            if test_tokens > max_tokens and current_chunk_lines:
                # Finalize current chunk
                chunk_code = "\n".join(current_chunk_lines)
                chunks.append(
                    CodeChunk(
                        code=chunk_code,
                        context=module_docstring or "",
                        dependencies=current_imports,
                        location="<module>",
                        start_line=current_chunk_start,
                        end_line=current_chunk_start + len(chunk_code.splitlines()) - 1,
                    )
                )
                # Start new chunk
                current_chunk_lines = []
                current_chunk_start = cls.lineno
                if imports:
                    current_chunk_lines.append("\n".join(imports) + "\n\n")

            current_chunk_lines.append(class_code)

        # Add final chunk
        if current_chunk_lines:
            chunk_code = "\n".join(current_chunk_lines)
            chunks.append(
                CodeChunk(
                    code=chunk_code,
                    context=module_docstring or "",
                    dependencies=current_imports,
                    location="<module>",
                    start_line=current_chunk_start,
                    end_line=current_chunk_start + len(chunk_code.splitlines()) - 1,
                )
            )

        return chunks if chunks else [self._create_fallback_chunk(code)]

    def _chunk_sliding_window(self, code: str, max_tokens: int) -> List[CodeChunk]:
        """Chunk code using sliding window strategy.

        Args:
            code: Source code.
            max_tokens: Maximum tokens per chunk.

        Returns:
            List of CodeChunk entities.
        """
        lines = code.splitlines()
        if not lines:
            return []

        chunks: List[CodeChunk] = []
        overlap_size = max(1, max_tokens // 10)  # 10% overlap
        current_start = 0
        imports = []
        module_docstring = ""

        # Extract imports and docstring from first lines
        try:
            tree = ast.parse(code)
            imports = self._extract_imports(tree)
            module_docstring = ast.get_docstring(tree) or ""
        except SyntaxError:
            pass

        # Calculate tokens per line (approximate)
        total_tokens = self.token_counter.count_tokens(code)
        tokens_per_line = max(1, total_tokens // len(lines)) if lines else 1
        lines_per_chunk = max(1, int(max_tokens / tokens_per_line))

        i = 0
        while i < len(lines):
            # Calculate chunk end
            chunk_end = min(i + lines_per_chunk, len(lines))
            chunk_lines = lines[i:chunk_end]

            # Add overlap from previous chunk (except for first chunk)
            if i > 0 and overlap_size > 0:
                overlap_start = max(0, i - overlap_size)
                overlap_lines = lines[overlap_start:i]
                chunk_lines = overlap_lines + chunk_lines

            chunk_code = "\n".join(chunk_lines)

            # Add imports to chunk if not already present
            if imports and not any(imp in chunk_code for imp in imports):
                chunk_code = "\n".join(imports) + "\n\n" + chunk_code

            chunks.append(
                CodeChunk(
                    code=chunk_code,
                    context=module_docstring,
                    dependencies=imports,
                    location="<module>",
                    start_line=max(1, i + 1),
                    end_line=max(1, chunk_end),
                )
            )

            # Move to next chunk with overlap
            next_i = (
                chunk_end - overlap_size
                if overlap_size > 0 and chunk_end > overlap_size
                else chunk_end
            )
            if next_i <= i:
                # Prevent infinite loop - ensure progress
                next_i = i + 1
            i = next_i

        return chunks if chunks else [self._create_fallback_chunk(code)]

    def _extract_imports(self, tree: ast.Module) -> List[str]:
        """Extract import statements from AST.

        Args:
            tree: Parsed AST module.

        Returns:
            List of import statement strings.
        """
        imports: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Reconstruct import statement (simplified)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = ", ".join(alias.name for alias in node.names)
                    imports.append(f"from {module} import {names}")
        return imports

    def _chunk_fallback(self, code: str, max_tokens: int) -> List[CodeChunk]:
        """Fallback chunking when AST parsing fails.

        Args:
            code: Source code.
            max_tokens: Maximum tokens per chunk.

        Returns:
            List of CodeChunk entities.
        """
        lines = code.splitlines()
        chunks: List[CodeChunk] = []
        current_chunk: List[str] = []
        current_start = 1

        for line in lines:
            current_chunk.append(line)
            chunk_code = "\n".join(current_chunk)
            tokens = self.token_counter.count_tokens(chunk_code)

            if tokens > max_tokens and len(current_chunk) > 1:
                # Finalize chunk (remove last line that caused overflow)
                current_chunk.pop()
                chunk_code = "\n".join(current_chunk)
                chunks.append(
                    CodeChunk(
                        code=chunk_code,
                        context="",
                        dependencies=[],
                        location="<module>",
                        start_line=current_start,
                        end_line=current_start + len(current_chunk) - 1,
                    )
                )
                current_start += len(current_chunk)
                current_chunk = [line]  # Start new chunk with overflow line

        # Add final chunk
        if current_chunk:
            chunk_code = "\n".join(current_chunk)
            chunks.append(
                CodeChunk(
                    code=chunk_code,
                    context="",
                    dependencies=[],
                    location="<module>",
                    start_line=current_start,
                    end_line=current_start + len(current_chunk) - 1,
                )
            )

        return chunks if chunks else [self._create_fallback_chunk(code)]

    def _create_fallback_chunk(self, code: str) -> CodeChunk:
        """Create a single fallback chunk with all code.

        Args:
            code: Source code.

        Returns:
            CodeChunk entity.
        """
        return CodeChunk(
            code=code,
            context="",
            dependencies=[],
            location="<module>",
            start_line=1,
            end_line=len(code.splitlines()),
        )
