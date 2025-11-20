"""Data processing functions for Test Agent testing."""

from typing import List, Optional


def filter_even(numbers: List[int]) -> List[int]:
    """Filter even numbers from list.

    Args:
        numbers: List of integers.

    Returns:
        List containing only even numbers.

    Example:
        >>> filter_even([1, 2, 3, 4, 5])
        [2, 4]
    """
    return [n for n in numbers if n % 2 == 0]


def calculate_average(numbers: List[float]) -> float:
    """Calculate average of numbers.

    Args:
        numbers: List of numbers.

    Returns:
        Average value.

    Raises:
        ValueError: If list is empty.

    Example:
        >>> calculate_average([1.0, 2.0, 3.0])
        2.0
        >>> calculate_average([])
        Traceback (most recent call last):
        ...
        ValueError: Cannot calculate average of empty list
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)


def find_max(numbers: List[int]) -> Optional[int]:
    """Find maximum value in list.

    Args:
        numbers: List of integers.

    Returns:
        Maximum value, or None if list is empty.

    Example:
        >>> find_max([1, 5, 3, 2])
        5
        >>> find_max([]) is None
        True
    """
    if not numbers:
        return None
    return max(numbers)


def process_data(data: List[dict], filter_key: str, value: any) -> List[dict]:
    """Filter data by key-value pair.

    Args:
        data: List of dictionaries.
        filter_key: Key to filter by.
        value: Value to match.

    Returns:
        Filtered list of dictionaries.

    Example:
        >>> data = [{"type": "A", "value": 1}, {"type": "B", "value": 2}]
        >>> process_data(data, "type", "A")
        [{"type": "A", "value": 1}]
    """
    return [item for item in data if item.get(filter_key) == value]
