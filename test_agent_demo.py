"""Simple module for testing the Test Agent."""

from typing import List, Optional


class MathUtils:
    """Utility class for mathematical operations."""

    @staticmethod
    def add(a: float, b: float) -> float:
        """Add two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            Sum of a and b.
        """
        return a + b

    @staticmethod
    def subtract(a: float, b: float) -> float:
        """Subtract b from a.

        Args:
            a: First number.
            b: Second number.

        Returns:
            Difference of a and b.
        """
        return a - b

    @staticmethod
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            Product of a and b.
        """
        return a * b

    @staticmethod
    def divide(a: float, b: float) -> float:
        """Divide a by b.

        Args:
            a: Numerator.
            b: Denominator.

        Returns:
            Quotient of a and b.

        Raises:
            ValueError: If b is zero.
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def calculate_sum(numbers: List[float]) -> float:
    """Calculate sum of a list of numbers.

    Args:
        numbers: List of numbers to sum.

    Returns:
        Sum of all numbers.
    """
    return sum(numbers)


def find_max(numbers: List[float]) -> Optional[float]:
    """Find maximum value in a list.

    Args:
        numbers: List of numbers.

    Returns:
        Maximum value, or None if list is empty.
    """
    if not numbers:
        return None
    return max(numbers)
