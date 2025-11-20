"""TestResult domain entity."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TestStatus(str, Enum):
    """Test execution status enum."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """
    Domain entity representing test execution results.

    Purpose:
        Represents the results of test execution including status, counts, coverage, and errors.

    Attributes:
        status: Test execution status.
        test_count: Total number of tests executed.
        passed_count: Number of tests that passed.
        failed_count: Number of tests that failed.
        coverage: Optional test coverage percentage (0-100).
        errors: Optional list of error messages.

    Example:
        >>> result = TestResult(
        ...     status=TestStatus.PASSED,
        ...     test_count=10,
        ...     passed_count=10,
        ...     failed_count=0,
        ...     coverage=85.5
        ... )
        >>> result.status
        <TestStatus.PASSED: 'passed'>
    """

    status: TestStatus
    test_count: int
    passed_count: int
    failed_count: int
    coverage: Optional[float] = None
    errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate TestResult attributes."""
        if self.test_count < 0:
            raise ValueError("test_count cannot be negative")
        if self.passed_count < 0:
            raise ValueError("passed_count cannot be negative")
        if self.failed_count < 0:
            raise ValueError("failed_count cannot be negative")
        if self.coverage is not None:
            if not 0.0 <= self.coverage <= 100.0:
                raise ValueError("coverage must be between 0 and 100")
