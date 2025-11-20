"""Simple functions for Test Agent testing."""


def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Sum of a and b.

    Example:
        >>> add(2, 3)
        5
    """
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Difference of a and b.

    Example:
        >>> subtract(5, 3)
        2
    """
    return a - b
