#!/usr/bin/env python3
"""Test Epic 27 components on a very large module.

Purpose:
    Tests chunking, coverage aggregation, and token counting
    on the largest module in the codebase (butler_handler.py - 1736 lines).

Usage:
    python scripts/test_large_module.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.application.test_agent.services.code_chunker import CodeChunker
from src.application.test_agent.services.coverage_aggregator import CoverageAggregator
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestResult, TestStatus
from src.infrastructure.test_agent.services.token_counter import TokenCounter


def test_large_module_chunking() -> None:
    """Test chunking on the largest module in the codebase.

    Purpose:
        Verifies that CodeChunker correctly handles a very large module
        (butler_handler.py - 1736 lines, ~7000+ tokens).
    """
    print("\n" + "=" * 80)
    print("TEST: Chunking Very Large Module (butler_handler.py)")
    print("=" * 80)

    # Read the large module
    module_path = project_root / "src/presentation/bot/handlers/butler_handler.py"

    if not module_path.exists():
        print(f"❌ Module not found: {module_path}")
        return

    code = module_path.read_text(encoding="utf-8")
    lines = len(code.splitlines())

    # Initialize components
    token_counter = TokenCounter()
    chunker = CodeChunker(token_counter=token_counter)

    # Count tokens in original code
    total_tokens = token_counter.count_tokens(code)
    print(f"Module: {module_path.name}")
    print(f"Size: {lines} lines, {len(code)} chars, {total_tokens} tokens")
    print(f"\nThis is a {'VERY LARGE' if total_tokens > 5000 else 'LARGE'} module!")

    # Test with realistic token limits
    max_tokens = 2000  # Realistic limit for LLM context

    # Test all strategies
    strategies = ["function_based", "class_based", "sliding_window"]

    for strategy in strategies:
        print(f"\n--- Testing {strategy} strategy (max_tokens={max_tokens}) ---")
        chunks = chunker.chunk_module(code, max_tokens=max_tokens, strategy=strategy)

        print(f"Generated {len(chunks)} chunks")

        # Analyze chunks
        chunk_sizes = []
        for i, chunk in enumerate(chunks):
            chunk_tokens = token_counter.count_tokens(chunk.code)
            chunk_sizes.append(chunk_tokens)
            if len(chunks) <= 10:
                # Show all chunks if <= 10
                print(
                    f"  Chunk {i+1}: {chunk_tokens} tokens, "
                    f"lines {chunk.start_line}-{chunk.end_line}, "
                    f"location: {chunk.location}"
                )
            elif i < 3 or i >= len(chunks) - 2:  # Show first 3 and last 2
                print(
                    f"  Chunk {i+1}: {chunk_tokens} tokens, "
                    f"lines {chunk.start_line}-{chunk.end_line}, "
                    f"location: {chunk.location}"
                )
            elif i == 3:
                print(f"  ... ({len(chunks) - 5} more chunks) ...")

        # Statistics
        if chunk_sizes:
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            max_size = max(chunk_sizes)
            min_size = min(chunk_sizes)
            print(f"  Statistics: avg={avg_size:.0f}, min={min_size}, max={max_size}")
            print(
                f"  Chunks within limit: {sum(1 for s in chunk_sizes if s <= max_tokens)}/{len(chunk_sizes)}"
            )

        # Verify chunks cover meaningful portions
        all_lines = set(range(1, lines + 1))
        covered_lines = set()
        for chunk in chunks:
            covered_lines.update(range(chunk.start_line, chunk.end_line + 1))

        coverage_ratio = len(covered_lines) / len(all_lines) if all_lines else 0.0
        print(
            f"  Line coverage: {coverage_ratio:.1%} ({len(covered_lines)}/{len(all_lines)} lines)"
        )

        # Verify chunk quality
        assert len(chunks) > 0, f"Should generate at least one chunk for {strategy}"
        assert coverage_ratio > 0.0, f"Should cover at least some lines for {strategy}"

        for i, chunk in enumerate(chunks):
            assert len(chunk.code) > 0, f"Chunk {i} has empty code in {strategy}"
            assert (
                chunk.start_line > 0
            ), f"Chunk {i} has invalid start_line in {strategy}"
            assert (
                chunk.end_line >= chunk.start_line
            ), f"Chunk {i} has invalid line range in {strategy}"

    print("\n✅ Large module chunking test PASSED")


def test_large_module_coverage() -> None:
    """Test coverage aggregation with large module.

    Purpose:
        Verifies that CoverageAggregator works correctly with large modules.
    """
    print("\n" + "=" * 80)
    print("TEST: Coverage Aggregation for Large Module")
    print("=" * 80)

    aggregator = CoverageAggregator()

    # Create realistic test results for large module
    test_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=50,
            passed_count=48,
            failed_count=2,
            coverage=72.5,
            errors=[],
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=45,
            passed_count=44,
            failed_count=1,
            coverage=78.3,
            errors=[],
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=35,
            passed_count=35,
            failed_count=0,
            coverage=65.1,
            errors=[],
        ),
    ]

    # Aggregate coverage
    aggregated = aggregator.aggregate_coverage(test_results)
    print(f"Aggregated coverage: {aggregated:.2f}%")
    print(f"Total tests: {sum(r.test_count for r in test_results)}")
    print(f"Total passed: {sum(r.passed_count for r in test_results)}")
    print(f"Total failed: {sum(r.failed_count for r in test_results)}")

    # Verify aggregation is reasonable
    assert 65.0 <= aggregated <= 80.0, f"Aggregated coverage out of range: {aggregated}"

    # Test gap identification
    module_path = project_root / "src/presentation/bot/handlers/butler_handler.py"
    code = module_path.read_text(encoding="utf-8")
    code_file = CodeFile(path=str(module_path), content=code)

    gaps = aggregator.identify_gaps(aggregated, code_file)
    print(f"\nIdentified {len(gaps)} coverage gaps")

    # Show sample gaps
    if gaps:
        print(f"Sample gaps (first 5): {gaps[:5]}")

    print("\n✅ Large module coverage aggregation test PASSED")


def test_performance() -> None:
    """Test performance on large module.

    Purpose:
        Verifies that chunking and token counting are performant
        even on very large modules.
    """
    print("\n" + "=" * 80)
    print("TEST: Performance on Large Module")
    print("=" * 80)

    import time

    module_path = project_root / "src/presentation/bot/handlers/butler_handler.py"
    code = module_path.read_text(encoding="utf-8")

    token_counter = TokenCounter()
    chunker = CodeChunker(token_counter=token_counter)

    # Test token counting performance
    start = time.time()
    tokens = token_counter.count_tokens(code)
    token_time = time.time() - start
    print(f"Token counting: {tokens} tokens in {token_time*1000:.2f}ms")

    # Test chunking performance
    start = time.time()
    chunks = chunker.chunk_module(code, max_tokens=2000, strategy="function_based")
    chunk_time = time.time() - start
    print(f"Chunking: {len(chunks)} chunks in {chunk_time*1000:.2f}ms")
    print(f"Average time per chunk: {chunk_time/len(chunks)*1000:.2f}ms")

    # Performance assertions
    assert token_time < 1.0, f"Token counting too slow: {token_time}s"
    assert chunk_time < 5.0, f"Chunking too slow: {chunk_time}s"

    print("\n✅ Performance test PASSED")


def main() -> None:
    """Run all large module tests.

    Purpose:
        Executes comprehensive tests on Epic 27 components
        using the largest module in the codebase.
    """
    print("\n" + "=" * 80)
    print("EPIC 27 LARGE MODULE TEST SUITE")
    print("Testing with butler_handler.py (1736 lines)")
    print("=" * 80)

    tests = [
        test_large_module_chunking,
        test_large_module_coverage,
        test_performance,
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
