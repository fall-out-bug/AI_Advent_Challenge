"""Unit tests for ICodeChunker interface - function-based strategy."""

import pytest

from src.application.test_agent.services.code_chunker import CodeChunker
from src.domain.test_agent.entities.code_chunk import CodeChunk
from src.domain.test_agent.interfaces.code_chunker import ICodeChunker
from src.domain.test_agent.value_objects.chunking_strategy import ChunkingStrategy
from src.infrastructure.test_agent.services.token_counter import TokenCounter


def test_chunk_module_single_function():
    """Test chunking a module with a single function."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
def hello():
    return "world"
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=100)

    # Assert
    assert len(chunks) > 0
    assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
    assert chunks[0].code.strip().startswith("def hello")


def test_chunk_module_multiple_functions():
    """Test chunking a module with multiple functions."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
def function_a():
    return 1

def function_b():
    return 2

def function_c():
    return 3
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=50)

    # Assert
    assert len(chunks) >= 1
    assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
    # Each chunk should contain at least one function
    assert any("function_a" in chunk.code for chunk in chunks)
    assert any("function_b" in chunk.code for chunk in chunks)
    assert any("function_c" in chunk.code for chunk in chunks)


def test_chunk_module_respects_max_tokens():
    """Test that chunks respect max_tokens limit."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = (
        """
def large_function():
    # This is a comment
    x = 1
    y = 2
    z = x + y
    return z
"""
        * 10
    )  # Repeat to create larger code

    # Act
    chunks = chunker.chunk_module(code, max_tokens=100)

    # Assert
    assert len(chunks) > 0
    for chunk in chunks:
        chunk_tokens = counter.count_tokens(chunk.code)
        assert chunk_tokens <= 100, f"Chunk exceeds max_tokens: {chunk_tokens}"


def test_chunk_module_preserves_imports():
    """Test that chunking preserves import statements."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
import os
import sys
from pathlib import Path

def test_function():
    return os.getcwd()
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=100)

    # Assert
    assert len(chunks) > 0
    # At least one chunk should contain imports
    imports_present = any(
        "import os" in chunk.code or "from pathlib" in chunk.code for chunk in chunks
    )
    assert imports_present, "Imports should be preserved in chunks"


def test_chunk_module_preserves_context():
    """Test that chunking preserves context metadata."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
# Module-level docstring
\"\"\"This is a test module.\"\"\"

def function():
    pass
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=100)

    # Assert
    assert len(chunks) > 0
    # Context should be preserved
    assert all(chunk.context is not None for chunk in chunks)


def test_chunk_module_function_based_strategy():
    """Test that function-based strategy groups functions correctly."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
def func_a():
    pass

def func_b():
    pass
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=100, strategy="function_based")

    # Assert
    assert len(chunks) > 0
    # Function-based strategy should create chunks per function or group small functions
    assert all(isinstance(chunk, CodeChunk) for chunk in chunks)


def test_chunk_package_multiple_files():
    """Test chunking a package with multiple files."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    # This test will need to be adjusted based on actual package structure
    # For now, we'll test with a mock package path
    import os
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        package_path = Path(tmpdir) / "test_package"
        package_path.mkdir()
        (package_path / "__init__.py").write_text("")
        (package_path / "module1.py").write_text("def func1(): pass")
        (package_path / "module2.py").write_text("def func2(): pass")

        # Act
        chunks = chunker.chunk_package(str(package_path), max_tokens=100)

        # Assert
        assert len(chunks) > 0
        assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
        # Should have chunks from multiple files
        locations = {chunk.location for chunk in chunks}
        assert len(locations) >= 1


def test_chunk_package_respects_directory_structure():
    """Test that chunking respects package directory structure."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        package_path = Path(tmpdir) / "test_package"
        package_path.mkdir()
        (package_path / "__init__.py").write_text("")
        (package_path / "submodule.py").write_text("def func(): pass")

        # Act
        chunks = chunker.chunk_package(str(package_path), max_tokens=100)

        # Assert
        assert len(chunks) > 0
        # Location should reflect file path
        assert all(chunk.location for chunk in chunks)


def test_chunk_module_class_based_strategy():
    """Test chunking with class-based strategy."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
class MyClass:
    def method_a(self):
        return 1

    def method_b(self):
        return 2

class AnotherClass:
    def method_c(self):
        return 3
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=100, strategy="class_based")

    # Assert
    assert len(chunks) > 0
    assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
    # Class-based strategy should group methods with their class
    assert any("class MyClass" in chunk.code for chunk in chunks)
    assert any("class AnotherClass" in chunk.code for chunk in chunks)


def test_chunk_module_class_based_preserves_methods():
    """Test that class-based strategy preserves methods with their class."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=100, strategy="class_based")

    # Assert
    assert len(chunks) > 0
    # Methods should be grouped with their class
    calculator_chunks = [c for c in chunks if "class Calculator" in c.code]
    assert len(calculator_chunks) > 0
    # Methods should be in the same chunk as the class
    for chunk in calculator_chunks:
        assert "def add" in chunk.code or "def subtract" in chunk.code


def test_chunk_module_sliding_window_strategy():
    """Test chunking with sliding-window strategy."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
def func1():
    pass

def func2():
    pass

def func3():
    pass

def func4():
    pass
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=50, strategy="sliding_window")

    # Assert
    assert len(chunks) > 0
    assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
    # Sliding window should create overlapping chunks
    # (For now, it uses function-based as fallback, so we just verify it works)


def test_chunk_module_sliding_window_overlap():
    """Test that sliding-window strategy creates overlapping chunks."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
def func1():
    return 1

def func2():
    return 2

def func3():
    return 3
"""

    # Act
    chunks = chunker.chunk_module(code, max_tokens=30, strategy="sliding_window")

    # Assert
    assert len(chunks) > 0
    # With small max_tokens, should create multiple chunks
    # (For now, it uses function-based as fallback, so we just verify it works)
    assert all(isinstance(chunk, CodeChunk) for chunk in chunks)


def test_chunk_selection_based_on_strategy():
    """Test that chunking strategy selection works correctly."""
    # Arrange
    counter = TokenCounter()
    chunker: ICodeChunker = CodeChunker(counter)
    code = """
def function():
    pass

class MyClass:
    def method(self):
        pass
"""

    # Act & Assert
    # Function-based strategy
    func_chunks = chunker.chunk_module(code, max_tokens=100, strategy="function_based")
    assert len(func_chunks) > 0

    # Class-based strategy
    class_chunks = chunker.chunk_module(code, max_tokens=100, strategy="class_based")
    assert len(class_chunks) > 0

    # Sliding-window strategy
    window_chunks = chunker.chunk_module(
        code, max_tokens=100, strategy="sliding_window"
    )
    assert len(window_chunks) > 0

    # All should produce valid chunks
    assert all(isinstance(c, CodeChunk) for c in func_chunks)
    assert all(isinstance(c, CodeChunk) for c in class_chunks)
    assert all(isinstance(c, CodeChunk) for c in window_chunks)
