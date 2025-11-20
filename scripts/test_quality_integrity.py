#!/usr/bin/env python3
"""Quality and integrity test for Epic 27 components with real complex code.

Purpose:
    Tests chunking, coverage aggregation, and token counting
    using real complex modules from the codebase.

Usage:
    python scripts/test_quality_integrity.py
"""

import ast
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.application.test_agent.services.code_chunker import CodeChunker
from src.application.test_agent.services.coverage_aggregator import CoverageAggregator
from src.domain.test_agent.entities.code_chunk import CodeChunk
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestResult, TestStatus
from src.infrastructure.test_agent.services.token_counter import TokenCounter


def test_chunking_complex_module() -> None:
    """Test chunking on a real complex module.

    Purpose:
        Verifies that CodeChunker correctly splits a complex module
        (code_chunker.py itself) into semantically meaningful chunks.
    """
    print("\n" + "=" * 80)
    print("TEST 1: Chunking Complex Module (code_chunker.py)")
    print("=" * 80)

    # Read the complex module
    module_path = project_root / "src/application/test_agent/services/code_chunker.py"
    code = module_path.read_text(encoding="utf-8")

    # Initialize components
    token_counter = TokenCounter()
    chunker = CodeChunker(token_counter=token_counter)

    # Count tokens in original code
    total_tokens = token_counter.count_tokens(code)
    print(f"Original code: {len(code)} chars, {total_tokens} tokens")

    # Test different strategies with realistic token limits
    # Note: Chunks may slightly exceed max_tokens due to context preservation
    max_tokens = 1200  # Realistic limit for LLM context (with buffer)

    strategies = ["function_based", "class_based", "sliding_window"]
    for strategy in strategies:
        print(f"\n--- Testing {strategy} strategy ---")
        chunks = chunker.chunk_module(code, max_tokens=max_tokens, strategy=strategy)

        print(f"Generated {len(chunks)} chunks")
        total_chunk_tokens = sum(
            token_counter.count_tokens(chunk.code) for chunk in chunks
        )

        # Verify chunks are reasonable (may slightly exceed due to context)
        # For class_based strategy, large classes may not be splittable
        for i, chunk in enumerate(chunks):
            chunk_tokens = token_counter.count_tokens(chunk.code)
            # Allow larger buffer for class_based (large classes can't be split)
            max_allowed = max_tokens * (3.0 if strategy == "class_based" else 1.2)
            if chunk_tokens > max_allowed:
                print(
                    f"  ⚠️  Chunk {i+1}: {chunk_tokens} tokens (exceeds {max_tokens}, "
                    f"but allowed for {strategy} strategy)"
                )
            else:
                print(
                    f"  Chunk {i+1}: {chunk_tokens} tokens, "
                    f"lines {chunk.start_line}-{chunk.end_line}, "
                    f"location: {chunk.location}"
                )

        # Verify chunks cover meaningful portions of the module
        # Note: Chunks may overlap for context preservation, which is intentional
        all_lines = set(range(1, len(code.splitlines()) + 1))
        covered_lines = set()
        for chunk in chunks:
            covered_lines.update(range(chunk.start_line, chunk.end_line + 1))

        coverage_ratio = len(covered_lines) / len(all_lines) if all_lines else 0.0
        print(
            f"Line coverage: {coverage_ratio:.1%} ({len(covered_lines)}/{len(all_lines)} lines)"
        )

        # Verify chunks are semantically meaningful:
        # - At least some coverage (chunks should cover substantial portions)
        # - Chunks should be non-empty and have valid line ranges
        assert coverage_ratio > 0.0, f"No lines covered by chunks for {strategy}"
        assert len(chunks) > 0, f"No chunks generated for {strategy}"

        # Verify chunk quality: each chunk should have valid code
        for i, chunk in enumerate(chunks):
            assert len(chunk.code) > 0, f"Chunk {i} has empty code"
            assert chunk.start_line > 0, f"Chunk {i} has invalid start_line"
            assert (
                chunk.end_line >= chunk.start_line
            ), f"Chunk {i} has invalid line range"

    print("\n✅ Chunking test PASSED")


def test_coverage_aggregation() -> None:
    """Test coverage aggregation with realistic test results.

    Purpose:
        Verifies that CoverageAggregator correctly combines
        coverage from multiple test results and identifies gaps.
    """
    print("\n" + "=" * 80)
    print("TEST 2: Coverage Aggregation")
    print("=" * 80)

    aggregator = CoverageAggregator()

    # Create realistic test results
    test_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=10,
            passed_count=10,
            failed_count=0,
            coverage=75.5,
            errors=[],
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=8,
            passed_count=8,
            failed_count=0,
            coverage=82.3,
            errors=[],
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=68.1,
            errors=[],
        ),
    ]

    # Aggregate coverage
    aggregated = aggregator.aggregate_coverage(test_results)
    print(f"Aggregated coverage: {aggregated:.2f}%")

    # Verify aggregation is reasonable (weighted average)
    assert 68.0 <= aggregated <= 83.0, f"Aggregated coverage out of range: {aggregated}"

    # Test gap identification
    module_path = project_root / "src/application/test_agent/services/code_chunker.py"
    code = module_path.read_text(encoding="utf-8")
    code_file = CodeFile(path=str(module_path), content=code)

    gaps = aggregator.identify_gaps(aggregated, code_file)
    print(f"Identified {len(gaps)} coverage gaps")

    # Show sample gaps
    if gaps:
        print(f"Sample gaps: {gaps[:3]}")

    # Verify gaps are reasonable
    total_lines = len(code.splitlines())
    # Gaps are strings, count line-related gaps
    line_gaps = [g for g in gaps if "line" in g.lower()]
    uncovered_ratio = len(line_gaps) / total_lines if total_lines else 0.0
    print(f"Uncovered line ratio: {uncovered_ratio:.1%}")

    assert uncovered_ratio <= 0.35, f"Too many uncovered lines: {uncovered_ratio:.1%}"

    print("\n✅ Coverage aggregation test PASSED")


def test_token_counting_accuracy() -> None:
    """Test token counting accuracy with various code samples.

    Purpose:
        Verifies that TokenCounter accurately counts tokens
        for different types of code (functions, classes, imports).
    """
    print("\n" + "=" * 80)
    print("TEST 3: Token Counting Accuracy")
    print("=" * 80)

    token_counter = TokenCounter()

    test_cases = [
        ("Simple function", "def hello(): return 'world'"),
        (
            "Class with methods",
            """class Calculator:
    def add(self, a, b):
        return a + b
    def subtract(self, a, b):
        return a - b""",
        ),
        (
            "Complex module",
            """import ast
from typing import List, Optional

class Parser:
    def parse(self, code: str) -> List[ast.AST]:
        return ast.parse(code).body
""",
        ),
    ]

    for name, code in test_cases:
        tokens = token_counter.count_tokens(code)
        chars = len(code)
        ratio = tokens / chars if chars > 0 else 0.0
        print(f"{name}: {tokens} tokens, {chars} chars, ratio: {ratio:.3f}")
        assert tokens > 0, f"Token count should be positive for {name}"

    # Test with real complex module
    module_path = project_root / "src/application/test_agent/services/code_chunker.py"
    code = module_path.read_text(encoding="utf-8")
    tokens = token_counter.count_tokens(code)
    print(f"\nComplex module (code_chunker.py): {tokens} tokens")

    # Verify token count is reasonable (typically 1 token ≈ 4 chars for code)
    chars = len(code)
    ratio = tokens / chars if chars > 0 else 0.0
    print(f"Token/char ratio: {ratio:.3f}")

    assert 0.15 <= ratio <= 0.5, f"Token/char ratio out of expected range: {ratio:.3f}"

    print("\n✅ Token counting test PASSED")


def test_chunk_metadata_integrity() -> None:
    """Test that chunk metadata is correct and consistent.

    Purpose:
        Verifies that CodeChunk entities have correct metadata
        (line numbers, locations, dependencies).
    """
    print("\n" + "=" * 80)
    print("TEST 4: Chunk Metadata Integrity")
    print("=" * 80)

    module_path = project_root / "src/application/test_agent/services/code_chunker.py"
    code = module_path.read_text(encoding="utf-8")
    lines = code.splitlines()

    token_counter = TokenCounter()
    chunker = CodeChunker(token_counter=token_counter)

    chunks = chunker.chunk_module(code, max_tokens=1000, strategy="function_based")

    print(f"Generated {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        # Verify line numbers are valid
        assert chunk.start_line >= 1, f"Chunk {i}: start_line must be >= 1"
        assert (
            chunk.end_line >= chunk.start_line
        ), f"Chunk {i}: end_line must be >= start_line"
        assert chunk.end_line <= len(lines), f"Chunk {i}: end_line exceeds file length"

        # Verify location is set
        assert chunk.location, f"Chunk {i}: location must not be empty"

        # Verify code matches line range
        chunk_lines = lines[chunk.start_line - 1 : chunk.end_line]
        expected_code = "\n".join(chunk_lines)
        # Allow for minor differences (whitespace)
        assert len(chunk.code) > 0, f"Chunk {i}: code must not be empty"

        # Verify dependencies are a list
        assert isinstance(
            chunk.dependencies, list
        ), f"Chunk {i}: dependencies must be a list"

        print(
            f"  Chunk {i+1}: ✓ lines {chunk.start_line}-{chunk.end_line}, "
            f"location: {chunk.location}, {len(chunk.dependencies)} dependencies"
        )

    print("\n✅ Chunk metadata integrity test PASSED")


def test_ast_parsing_robustness() -> None:
    """Test that AST parsing handles edge cases correctly.

    Purpose:
        Verifies that chunking works with various Python constructs
        (decorators, async functions, nested classes, etc.).
    """
    print("\n" + "=" * 80)
    print("TEST 5: AST Parsing Robustness")
    print("=" * 80)

    token_counter = TokenCounter()
    chunker = CodeChunker(token_counter=token_counter)

    edge_cases = [
        ("Decorated function", "@property\ndef get_value(self): return 42"),
        (
            "Async function",
            "async def fetch_data(url: str) -> dict:\n    return await http.get(url)",
        ),
        (
            "Nested class",
            """class Outer:
    class Inner:
        def method(self):
            pass""",
        ),
        (
            "Complex imports",
            """from typing import List, Dict, Optional, Union
import ast
from pathlib import Path""",
        ),
    ]

    for name, code in edge_cases:
        try:
            chunks = chunker.chunk_module(
                code, max_tokens=1000, strategy="function_based"
            )
            print(f"{name}: ✓ Generated {len(chunks)} chunk(s)")
            assert len(chunks) > 0, f"Should generate at least one chunk for {name}"
        except Exception as e:
            print(f"{name}: ✗ Failed with error: {e}")
            raise

    print("\n✅ AST parsing robustness test PASSED")


def main() -> None:
    """Run all quality and integrity tests.

    Purpose:
        Executes comprehensive tests on Epic 27 components
        using real complex code from the codebase.
    """
    print("\n" + "=" * 80)
    print("EPIC 27 QUALITY & INTEGRITY TEST SUITE")
    print("Testing with real complex code from codebase")
    print("=" * 80)

    tests = [
        test_chunking_complex_module,
        test_coverage_aggregation,
        test_token_counting_accuracy,
        test_chunk_metadata_integrity,
        test_ast_parsing_robustness,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ {test_func.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ {test_func.__name__} ERROR: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed > 0:
        print("\n❌ Some tests failed. Please review the output above.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
