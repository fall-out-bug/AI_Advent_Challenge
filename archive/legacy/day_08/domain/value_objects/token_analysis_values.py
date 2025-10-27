"""
Value objects for the token analysis system.

This module contains immutable value objects that represent concepts
in the token analysis domain without identity.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class TokenCount:
    """
    Value object representing a token count.

    This immutable value object encapsulates token counting logic and validation.
    """

    def __init__(self, count: int):
        """
        Initialize token count.

        Args:
            count: Number of tokens (must be non-negative)

        Raises:
            ValueError: If count is negative
        """
        if count < 0:
            raise ValueError("Token count cannot be negative")
        self._count = count

    @property
    def count(self) -> int:
        """Get the token count."""
        return self._count

    def __eq__(self, other) -> bool:
        """Check equality with another TokenCount."""
        if not isinstance(other, TokenCount):
            return False
        return self._count == other._count

    def __hash__(self) -> int:
        """Get hash of the token count."""
        return hash(self._count)

    def __str__(self) -> str:
        """String representation."""
        return str(self._count)

    def __repr__(self) -> str:
        """Representation."""
        return f"TokenCount({self._count})"

    def add(self, other: "TokenCount") -> "TokenCount":
        """
        Add another token count.

        Args:
            other: Another token count to add

        Returns:
            TokenCount: New token count with sum
        """
        return TokenCount(self._count + other._count)

    def subtract(self, other: "TokenCount") -> "TokenCount":
        """
        Subtract another token count.

        Args:
            other: Another token count to subtract

        Returns:
            TokenCount: New token count with difference

        Raises:
            ValueError: If result would be negative
        """
        result = self._count - other._count
        if result < 0:
            raise ValueError("Token count cannot be negative")
        return TokenCount(result)

    def multiply(self, factor: float) -> "TokenCount":
        """
        Multiply token count by a factor.

        Args:
            factor: Multiplication factor

        Returns:
            TokenCount: New token count multiplied by factor
        """
        return TokenCount(int(self._count * factor))

    def is_zero(self) -> bool:
        """Check if token count is zero."""
        return self._count == 0

    def is_positive(self) -> bool:
        """Check if token count is positive."""
        return self._count > 0


class CompressionRatio:
    """
    Value object representing a compression ratio.

    This immutable value object encapsulates compression ratio logic and validation.
    """

    def __init__(self, ratio: float):
        """
        Initialize compression ratio.

        Args:
            ratio: Compression ratio (must be between 0 and 1)

        Raises:
            ValueError: If ratio is not between 0 and 1
        """
        if not (0.0 <= ratio <= 1.0):
            raise ValueError("Compression ratio must be between 0 and 1")
        self._ratio = ratio

    @property
    def ratio(self) -> float:
        """Get the compression ratio."""
        return self._ratio

    def __eq__(self, other) -> bool:
        """Check equality with another CompressionRatio."""
        if not isinstance(other, CompressionRatio):
            return False
        return abs(self._ratio - other._ratio) < 1e-9  # Float comparison

    def __hash__(self) -> int:
        """Get hash of the compression ratio."""
        return hash(round(self._ratio, 9))  # Round for consistent hashing

    def __str__(self) -> str:
        """String representation."""
        return f"{self._ratio:.3f}"

    def __repr__(self) -> str:
        """Representation."""
        return f"CompressionRatio({self._ratio})"

    def is_perfect_compression(self) -> bool:
        """Check if this is perfect compression (ratio = 0)."""
        return self._ratio == 0.0

    def is_no_compression(self) -> bool:
        """Check if there's no compression (ratio = 1)."""
        return self._ratio == 1.0

    def get_compression_percentage(self) -> float:
        """
        Get compression percentage.

        Returns:
            float: Compression percentage (0-100)
        """
        return (1.0 - self._ratio) * 100.0

    def compare_to_target(self, target: "CompressionRatio") -> float:
        """
        Compare this ratio to a target ratio.

        Args:
            target: Target compression ratio

        Returns:
            float: Difference from target (positive = over-compressed, negative = under-compressed)
        """
        return self._ratio - target._ratio

    def is_within_tolerance(
        self, target: "CompressionRatio", tolerance: float = 0.1
    ) -> bool:
        """
        Check if this ratio is within tolerance of target.

        Args:
            target: Target compression ratio
            tolerance: Tolerance level

        Returns:
            bool: True if within tolerance
        """
        return abs(self.compare_to_target(target)) <= tolerance


class ModelSpecification:
    """
    Value object representing a model specification.

    This immutable value object encapsulates model identification and configuration.
    """

    def __init__(
        self,
        name: str,
        version: str,
        framework: str,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize model specification.

        Args:
            name: Model name
            version: Model version
            framework: ML framework
            parameters: Model parameters
        """
        if not name.strip():
            raise ValueError("Model name cannot be empty")
        if not version.strip():
            raise ValueError("Model version cannot be empty")
        if not framework.strip():
            raise ValueError("Framework cannot be empty")

        self._name = name.strip()
        self._version = version.strip()
        self._framework = framework.strip()
        self._parameters = parameters or {}

    @property
    def name(self) -> str:
        """Get model name."""
        return self._name

    @property
    def version(self) -> str:
        """Get model version."""
        return self._version

    @property
    def framework(self) -> str:
        """Get framework."""
        return self._framework

    @property
    def parameters(self) -> Dict[str, Any]:
        """Get model parameters."""
        return self._parameters.copy()  # Return copy to maintain immutability

    def __eq__(self, other) -> bool:
        """Check equality with another ModelSpecification."""
        if not isinstance(other, ModelSpecification):
            return False
        return (
            self._name == other._name
            and self._version == other._version
            and self._framework == other._framework
        )

    def __hash__(self) -> int:
        """Get hash of the model specification."""
        return hash((self._name, self._version, self._framework))

    def __str__(self) -> str:
        """String representation."""
        return f"{self._name} v{self._version} ({self._framework})"

    def __repr__(self) -> str:
        """Representation."""
        return f"ModelSpecification(name='{self._name}', version='{self._version}', framework='{self._framework}')"

    def get_full_name(self) -> str:
        """Get full model name with version."""
        return f"{self._name}_{self._version}"

    def is_compatible_with(self, other: "ModelSpecification") -> bool:
        """
        Check if this model is compatible with another.

        Args:
            other: Another model specification

        Returns:
            bool: True if compatible
        """
        return self._name == other._name and self._framework == other._framework

    def with_parameters(self, parameters: Dict[str, Any]) -> "ModelSpecification":
        """
        Create a new model specification with updated parameters.

        Args:
            parameters: New parameters

        Returns:
            ModelSpecification: New specification with parameters
        """
        return ModelSpecification(
            name=self._name,
            version=self._version,
            framework=self._framework,
            parameters=parameters,
        )


class ProcessingTime:
    """
    Value object representing processing time.

    This immutable value object encapsulates processing time logic and validation.
    """

    def __init__(self, seconds: float):
        """
        Initialize processing time.

        Args:
            seconds: Processing time in seconds (must be non-negative)

        Raises:
            ValueError: If seconds is negative
        """
        if seconds < 0:
            raise ValueError("Processing time cannot be negative")
        self._seconds = seconds

    @property
    def seconds(self) -> float:
        """Get processing time in seconds."""
        return self._seconds

    @property
    def milliseconds(self) -> float:
        """Get processing time in milliseconds."""
        return self._seconds * 1000.0

    def __eq__(self, other) -> bool:
        """Check equality with another ProcessingTime."""
        if not isinstance(other, ProcessingTime):
            return False
        return abs(self._seconds - other._seconds) < 1e-9  # Float comparison

    def __hash__(self) -> int:
        """Get hash of the processing time."""
        return hash(round(self._seconds, 9))  # Round for consistent hashing

    def __str__(self) -> str:
        """String representation."""
        if self._seconds < 1.0:
            return f"{self.milliseconds:.1f}ms"
        else:
            return f"{self._seconds:.3f}s"

    def __repr__(self) -> str:
        """Representation."""
        return f"ProcessingTime({self._seconds})"

    def is_fast(self, threshold: float = 1.0) -> bool:
        """
        Check if processing time is fast.

        Args:
            threshold: Threshold in seconds

        Returns:
            bool: True if processing time is below threshold
        """
        return self._seconds <= threshold

    def is_slow(self, threshold: float = 5.0) -> bool:
        """
        Check if processing time is slow.

        Args:
            threshold: Threshold in seconds

        Returns:
            bool: True if processing time is above threshold
        """
        return self._seconds >= threshold

    def add(self, other: "ProcessingTime") -> "ProcessingTime":
        """
        Add another processing time.

        Args:
            other: Another processing time to add

        Returns:
            ProcessingTime: New processing time with sum
        """
        return ProcessingTime(self._seconds + other._seconds)

    def multiply(self, factor: float) -> "ProcessingTime":
        """
        Multiply processing time by a factor.

        Args:
            factor: Multiplication factor

        Returns:
            ProcessingTime: New processing time multiplied by factor
        """
        return ProcessingTime(self._seconds * factor)


class QualityScore:
    """
    Value object representing a quality score.

    This immutable value object encapsulates quality scoring logic and validation.
    """

    def __init__(self, score: float):
        """
        Initialize quality score.

        Args:
            score: Quality score (must be between 0 and 1)

        Raises:
            ValueError: If score is not between 0 and 1
        """
        if not (0.0 <= score <= 1.0):
            raise ValueError("Quality score must be between 0 and 1")
        self._score = score

    @property
    def score(self) -> float:
        """Get the quality score."""
        return self._score

    def __eq__(self, other) -> bool:
        """Check equality with another QualityScore."""
        if not isinstance(other, QualityScore):
            return False
        return abs(self._score - other._score) < 1e-9  # Float comparison

    def __hash__(self) -> int:
        """Get hash of the quality score."""
        return hash(round(self._score, 9))  # Round for consistent hashing

    def __str__(self) -> str:
        """String representation."""
        return f"{self._score:.3f}"

    def __repr__(self) -> str:
        """Representation."""
        return f"QualityScore({self._score})"

    def is_excellent(self) -> bool:
        """Check if quality score is excellent (>= 0.9)."""
        return self._score >= 0.9

    def is_good(self) -> bool:
        """Check if quality score is good (>= 0.7)."""
        return self._score >= 0.7

    def is_poor(self) -> bool:
        """Check if quality score is poor (< 0.5)."""
        return self._score < 0.5

    def get_grade(self) -> str:
        """
        Get letter grade for quality score.

        Returns:
            str: Letter grade (A, B, C, D, F)
        """
        if self._score >= 0.9:
            return "A"
        elif self._score >= 0.8:
            return "B"
        elif self._score >= 0.7:
            return "C"
        elif self._score >= 0.6:
            return "D"
        else:
            return "F"

    def compare_to(self, other: "QualityScore") -> float:
        """
        Compare this score to another.

        Args:
            other: Another quality score

        Returns:
            float: Difference (positive = better, negative = worse)
        """
        return self._score - other._score

    def is_better_than(self, other: "QualityScore") -> bool:
        """
        Check if this score is better than another.

        Args:
            other: Another quality score

        Returns:
            bool: True if this score is better
        """
        return self.compare_to(other) > 0
