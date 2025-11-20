"""Unit tests for ChunkingStrategy value object."""

import pytest

from src.domain.test_agent.value_objects.chunking_strategy import ChunkingStrategy


def test_chunking_strategy_creation_with_valid_types():
    """Test ChunkingStrategy creation with valid strategy types."""
    # Arrange & Act
    function_based = ChunkingStrategy("function_based")
    class_based = ChunkingStrategy("class_based")
    sliding_window = ChunkingStrategy("sliding_window")

    # Assert
    assert function_based.strategy_type == "function_based"
    assert class_based.strategy_type == "class_based"
    assert sliding_window.strategy_type == "sliding_window"


def test_chunking_strategy_function_based_type():
    """Test ChunkingStrategy with function_based type."""
    # Arrange & Act
    strategy = ChunkingStrategy("function_based")

    # Assert
    assert strategy.strategy_type == "function_based"
    assert strategy.is_function_based() is True
    assert strategy.is_class_based() is False
    assert strategy.is_sliding_window() is False


def test_chunking_strategy_class_based_type():
    """Test ChunkingStrategy with class_based type."""
    # Arrange & Act
    strategy = ChunkingStrategy("class_based")

    # Assert
    assert strategy.strategy_type == "class_based"
    assert strategy.is_function_based() is False
    assert strategy.is_class_based() is True
    assert strategy.is_sliding_window() is False


def test_chunking_strategy_sliding_window_type():
    """Test ChunkingStrategy with sliding_window type."""
    # Arrange & Act
    strategy = ChunkingStrategy("sliding_window")

    # Assert
    assert strategy.strategy_type == "sliding_window"
    assert strategy.is_function_based() is False
    assert strategy.is_class_based() is False
    assert strategy.is_sliding_window() is True


def test_chunking_strategy_equality():
    """Test ChunkingStrategy equality comparison."""
    # Arrange
    strategy1 = ChunkingStrategy("function_based")
    strategy2 = ChunkingStrategy("function_based")
    strategy3 = ChunkingStrategy("class_based")

    # Act & Assert
    assert strategy1 == strategy2
    assert strategy1 != strategy3
    assert hash(strategy1) == hash(strategy2)
    assert hash(strategy1) != hash(strategy3)


def test_chunking_strategy_immutability():
    """Test ChunkingStrategy immutability."""
    # Arrange
    strategy = ChunkingStrategy("function_based")

    # Act & Assert - attempting to modify should raise AttributeError
    with pytest.raises(AttributeError):
        strategy.strategy_type = "class_based"  # type: ignore


def test_invalid_strategy_type_raises_error():
    """Test ChunkingStrategy raises error for invalid strategy type."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="Invalid strategy type"):
        ChunkingStrategy("invalid_strategy")

    with pytest.raises(ValueError, match="Invalid strategy type"):
        ChunkingStrategy("")

    with pytest.raises(ValueError, match="Invalid strategy type"):
        ChunkingStrategy("FUNCTION_BASED")  # Case sensitive
