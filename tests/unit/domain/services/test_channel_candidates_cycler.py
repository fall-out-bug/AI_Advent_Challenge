"""Tests for CycleChannelCandidatesService."""

import pytest

from src.domain.services.channel_candidates_cycler import CycleChannelCandidatesService
from src.domain.value_objects.channel_resolution import ChannelSearchResult


def create_test_candidates(count: int = 3) -> list[ChannelSearchResult]:
    """Create test candidates."""
    return [
        ChannelSearchResult(
            username=f"channel_{i}",
            title=f"Channel {i}",
            description=f"Description {i}",
            chat_id=i,
        )
        for i in range(1, count + 1)
    ]


def test_cycle_candidates_advances_on_decline():
    """Test that decline advances to next candidate.

    Purpose:
        Test that calling decline() moves to next candidate.
    """
    # Arrange
    candidates = create_test_candidates(3)
    cycler = CycleChannelCandidatesService(candidates)

    # Assert initial state
    assert cycler.current().username == "channel_1"
    assert cycler.index == 0
    assert cycler.has_next() is True
    assert cycler.is_exhausted() is False

    # Act: decline first candidate
    new_cycler = cycler.decline()

    # Assert: new state, original unchanged (immutable)
    assert new_cycler.current().username == "channel_2"
    assert new_cycler.index == 1
    assert cycler.index == 0  # Original unchanged
    assert new_cycler.has_next() is True
    assert new_cycler.is_exhausted() is False


def test_cycle_candidates_exhausts_after_last():
    """Test that cycler exhausts after last candidate.

    Purpose:
        Test that after declining all candidates, is_exhausted returns True.
    """
    # Arrange
    candidates = create_test_candidates(3)
    cycler = CycleChannelCandidatesService(candidates)

    # Act: decline all candidates
    cycler = cycler.decline()  # Move to 2
    cycler = cycler.decline()  # Move to 3

    # Assert: exhausted
    assert cycler.current().username == "channel_3"
    assert cycler.index == 2
    assert cycler.has_next() is False
    assert cycler.is_exhausted() is True


def test_cycle_candidates_single_candidate():
    """Test with single candidate.

    Purpose:
        Test that single candidate works correctly.
    """
    # Arrange
    candidates = create_test_candidates(1)
    cycler = CycleChannelCandidatesService(candidates)

    # Assert
    assert cycler.current().username == "channel_1"
    assert cycler.has_next() is False
    # Single candidate at index 0 is exhausted (no next, cannot decline)
    assert cycler.is_exhausted() is True

    # Act: decline should raise IndexError
    with pytest.raises(IndexError, match="No more candidates"):
        cycler.decline()


def test_cycle_candidates_empty_list():
    """Test with empty candidates list.

    Purpose:
        Test that empty list is handled correctly.
    """
    # Arrange
    candidates = []
    cycler = CycleChannelCandidatesService(candidates, index=0)

    # Assert
    assert cycler.is_exhausted() is True
    assert cycler.has_next() is False
    # current() should raise IndexError
    with pytest.raises(IndexError, match="No candidates available"):
        cycler.current()


def test_cycle_candidates_immutability():
    """Test that cycler is immutable.

    Purpose:
        Test that decline() returns new instance, original unchanged.
    """
    # Arrange
    candidates = create_test_candidates(3)
    cycler1 = CycleChannelCandidatesService(candidates)

    # Act
    cycler2 = cycler1.decline()
    cycler3 = cycler2.decline()

    # Assert: all instances are different
    assert cycler1.index == 0
    assert cycler2.index == 1
    assert cycler3.index == 2
    assert cycler1 is not cycler2
    assert cycler2 is not cycler3
