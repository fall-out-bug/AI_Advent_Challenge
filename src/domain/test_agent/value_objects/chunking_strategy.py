"""ChunkingStrategy value object."""

from dataclasses import dataclass

# Valid strategy types
VALID_STRATEGY_TYPES = {"function_based", "class_based", "sliding_window"}


@dataclass(frozen=True)
class ChunkingStrategy:
    """
    Value object representing a chunking strategy for code splitting.

    Purpose:
        Immutable value object that encapsulates the strategy type for chunking
        large code modules into smaller pieces that fit within token limits.

    Attributes:
        strategy_type: Type of chunking strategy. Must be one of:
            - "function_based": Split code by functions
            - "class_based": Split code by classes
            - "sliding_window": Split code using sliding window approach

    Example:
        >>> strategy = ChunkingStrategy("function_based")
        >>> strategy.is_function_based()
        True
        >>> strategy.strategy_type
        'function_based'
    """

    strategy_type: str

    def __post_init__(self) -> None:
        """Validate ChunkingStrategy attributes."""
        if self.strategy_type not in VALID_STRATEGY_TYPES:
            raise ValueError(
                f"Invalid strategy type: {self.strategy_type}. "
                f"Must be one of {VALID_STRATEGY_TYPES}"
            )

    def is_function_based(self) -> bool:
        """Check if strategy is function-based."""
        return self.strategy_type == "function_based"

    def is_class_based(self) -> bool:
        """Check if strategy is class-based."""
        return self.strategy_type == "class_based"

    def is_sliding_window(self) -> bool:
        """Check if strategy is sliding window."""
        return self.strategy_type == "sliding_window"
