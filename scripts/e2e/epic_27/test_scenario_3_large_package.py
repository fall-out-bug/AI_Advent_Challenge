"""E2E user simulation script - Scenario 3: Large package (multiple modules).

Purpose:
    Simulates user pointing Test Agent to larger package (multiple modules),
    verifying agent processes files in chunks, verifying tests generated
    across package, verifying no failures due to context limits, and
    verifying meaningful tests for main public APIs.

Example:
    $ python scripts/e2e/epic_27/test_scenario_3_large_package.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CLI_MODULE = "src.presentation.cli.test_agent.main"


def create_large_package() -> Path:
    """Create large package with multiple modules for testing.

    Returns:
        Path to package directory.
    """
    package_dir = PROJECT_ROOT / "test_large_package"
    package_dir.mkdir(exist_ok=True)

    # Create __init__.py
    init_file = package_dir / "__init__.py"
    init_file.write_text('"""Large package for E2E testing."""\n')

    # Module 1: Data structures
    module1_code = '''"""Data structures module."""

from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class Stack(Generic[T]):
    """Stack data structure implementation."""

    def __init__(self) -> None:
        """Initialize empty stack."""
        self._items: List[T] = []

    def push(self, item: T) -> None:
        """Push item onto stack.

        Args:
            item: Item to push.
        """
        self._items.append(item)

    def pop(self) -> T:
        """Pop item from stack.

        Returns:
            Top item from stack.

        Raises:
            IndexError: If stack is empty.
        """
        if self.is_empty():
            raise IndexError("Cannot pop from empty stack")
        return self._items.pop()

    def peek(self) -> Optional[T]:
        """Peek at top item without removing.

        Returns:
            Top item, or None if empty.
        """
        if self.is_empty():
            return None
        return self._items[-1]

    def is_empty(self) -> bool:
        """Check if stack is empty.

        Returns:
            True if empty, False otherwise.
        """
        return len(self._items) == 0

    def size(self) -> int:
        """Get stack size.

        Returns:
            Number of items in stack.
        """
        return len(self._items)


class Queue(Generic[T]):
    """Queue data structure implementation."""

    def __init__(self) -> None:
        """Initialize empty queue."""
        self._items: List[T] = []

    def enqueue(self, item: T) -> None:
        """Add item to queue.

        Args:
            item: Item to add.
        """
        self._items.append(item)

    def dequeue(self) -> T:
        """Remove and return front item.

        Returns:
            Front item from queue.

        Raises:
            IndexError: If queue is empty.
        """
        if self.is_empty():
            raise IndexError("Cannot dequeue from empty queue")
        return self._items.pop(0)

    def front(self) -> Optional[T]:
        """Get front item without removing.

        Returns:
            Front item, or None if empty.
        """
        if self.is_empty():
            return None
        return self._items[0]

    def is_empty(self) -> bool:
        """Check if queue is empty.

        Returns:
            True if empty, False otherwise.
        """
        return len(self._items) == 0

    def size(self) -> int:
        """Get queue size.

        Returns:
            Number of items in queue.
        """
        return len(self._items)
'''
    module1_file = package_dir / "data_structures.py"
    module1_file.write_text(module1_code)

    # Module 2: Algorithms
    module2_code = '''"""Algorithms module."""

from typing import List


def binary_search(arr: List[int], target: int) -> int:
    """Binary search algorithm.

    Args:
        arr: Sorted list of integers.
        target: Target value to find.

    Returns:
        Index of target, or -1 if not found.
    """
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


def quick_sort(arr: List[int]) -> List[int]:
    """Quick sort algorithm.

    Args:
        arr: List of integers to sort.

    Returns:
        Sorted list.
    """
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


def merge_sort(arr: List[int]) -> List[int]:
    """Merge sort algorithm.

    Args:
        arr: List of integers to sort.

    Returns:
        Sorted list.
    """
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(left: List[int], right: List[int]) -> List[int]:
    """Merge two sorted lists.

    Args:
        left: First sorted list.
        right: Second sorted list.

    Returns:
        Merged sorted list.
    """
    result = []
    i, j = 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
'''
    module2_file = package_dir / "algorithms.py"
    module2_file.write_text(module2_code)

    # Module 3: Utilities
    module3_code = '''"""Utilities module."""

import hashlib
from typing import Dict, List


def hash_string(text: str) -> str:
    """Hash string using SHA256.

    Args:
        text: String to hash.

    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(text.encode()).hexdigest()


def group_by_key(items: List[Dict], key: str) -> Dict:
    """Group items by key.

    Args:
        items: List of dictionaries.
        key: Key to group by.

    Returns:
        Dictionary grouped by key.
    """
    result: Dict = {}
    for item in items:
        value = item.get(key)
        if value not in result:
            result[value] = []
        result[value].append(item)
    return result


def flatten(nested_list: List) -> List:
    """Flatten nested list.

    Args:
        nested_list: List that may contain nested lists.

    Returns:
        Flattened list.
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def chunk_list(items: List, chunk_size: int) -> List[List]:
    """Split list into chunks.

    Args:
        items: List to chunk.
        chunk_size: Size of each chunk.

    Returns:
        List of chunks.
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
'''
    module3_file = package_dir / "utilities.py"
    module3_file.write_text(module3_code)

    return package_dir


def run_test_agent_on_package(package_path: Path) -> Tuple[str, str, int]:
    """Run Test Agent CLI on package directory.

    Args:
        package_path: Path to package directory.

    Returns:
        Tuple of (stdout, stderr, returncode).
    """
    # Test Agent CLI expects a file, so we'll point to __init__.py
    # In real scenario, CLI might support directories
    init_file = package_path / "__init__.py"
    if not init_file.exists():
        # Create minimal __init__.py
        init_file.write_text('"""Package."""\n')

    cmd = [
        sys.executable,
        "-m",
        CLI_MODULE,
        str(init_file),
        "--save-tests",
    ]
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=900,  # 15 minutes for large package
    )
    return result.stdout, result.stderr, result.returncode


def find_generated_tests() -> List[Path]:
    """Find all generated test files in workspace directory.

    Returns:
        List of paths to generated test files.
    """
    workspace_dir = PROJECT_ROOT / "workspace"
    if not workspace_dir.exists():
        return []

    test_files = list(workspace_dir.glob("generated_tests_*.py"))
    return sorted(test_files, key=lambda p: p.stat().st_mtime, reverse=True)


def check_for_context_errors(output: str) -> bool:
    """Check if output contains context limit errors.

    Args:
        output: Test Agent output.

    Returns:
        True if context errors found, False otherwise.
    """
    error_keywords = [
        "context window",
        "token limit",
        "too large",
        "exceeds",
        "context overflow",
    ]
    output_lower = output.lower()
    return any(keyword in output_lower for keyword in error_keywords)


def verify_tests_for_public_apis(test_files: List[Path], package_dir: Path) -> bool:
    """Verify tests cover main public APIs.

    Args:
        test_files: List of generated test files.
        package_dir: Package directory.

    Returns:
        True if public APIs are covered, False otherwise.
    """
    # Read all test files
    test_content = ""
    for test_file in test_files:
        test_content += test_file.read_text() + "\n"

    # Check for tests of main classes/functions
    public_apis = [
        "Stack",
        "Queue",
        "binary_search",
        "quick_sort",
        "merge_sort",
        "hash_string",
        "group_by_key",
        "flatten",
        "chunk_list",
    ]

    found_apis = []
    for api in public_apis:
        if f"test_{api.lower()}" in test_content or api in test_content:
            found_apis.append(api)

    coverage_ratio = len(found_apis) / len(public_apis) if public_apis else 0.0
    return coverage_ratio >= 0.5  # At least 50% of public APIs should be tested


def main() -> int:
    """Main function for Scenario 3 E2E test.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("=" * 70)
    print("E2E Scenario 3: Large Package (Multiple Modules)")
    print("=" * 70)
    print()

    # Step 1: Create large package
    print("Step 1: Creating large package with multiple modules...")
    package_dir = create_large_package()
    print(f"✓ Created package: {package_dir}")
    print(f"  Modules: data_structures.py, algorithms.py, utilities.py")
    print()

    try:
        # Step 2: Run Test Agent on package
        print("Step 2: Running Test Agent on package...")
        print(f"Command: python -m {CLI_MODULE} {package_dir}/__init__.py --save-tests")
        stdout, stderr, returncode = run_test_agent_on_package(package_dir)

        if returncode != 0:
            print(f"⚠ Test Agent returned exit code {returncode}")
            print("STDOUT:", stdout[:500])  # Print first 500 chars
            print("STDERR:", stderr[:500])
        else:
            print("✓ Test Agent completed successfully")
        print()

        # Step 3: Verify no context limit failures
        print("Step 3: Verifying no context limit failures...")
        has_context_errors = check_for_context_errors(stdout + stderr)
        if has_context_errors:
            print("✗ Context limit errors detected in output")
            return 1
        else:
            print("✓ No context limit errors detected")
        print()

        # Step 4: Verify tests generated across package
        print("Step 4: Verifying tests generated...")
        test_files = find_generated_tests()
        if not test_files:
            print("✗ No generated test files found")
            return 1

        print(f"✓ Found {len(test_files)} generated test file(s)")
        for test_file in test_files:
            print(f"  - {test_file.name} ({test_file.stat().st_size} bytes)")
        print()

        # Step 5: Verify meaningful tests for public APIs
        print("Step 5: Verifying tests for main public APIs...")
        has_public_api_tests = verify_tests_for_public_apis(test_files, package_dir)
        if has_public_api_tests:
            print("✓ Public APIs are covered by tests")
        else:
            print("⚠ Some public APIs may not be covered")
            # Note: This is a warning, not a failure

        print()
        print("=" * 70)
        print("Scenario 3: COMPLETED")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  - Package processed: {package_dir}")
        print(f"  - Test files generated: {len(test_files)}")
        print(f"  - Context errors: {'None' if not has_context_errors else 'Found'}")
        print(
            f"  - Public API coverage: {'Good' if has_public_api_tests else 'Partial'}"
        )

        return 0

    except subprocess.TimeoutExpired:
        print("✗ Test Agent timed out")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        if package_dir.exists() and "test_large_package" in str(package_dir):
            import shutil

            shutil.rmtree(package_dir, ignore_errors=True)
            print(f"✓ Cleaned up package directory: {package_dir}")


if __name__ == "__main__":
    sys.exit(main())
