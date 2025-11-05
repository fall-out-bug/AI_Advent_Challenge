"""Service for cycling through channel search candidates.

Following Python Zen: Simple is better than complex.
Following Domain-Driven Design: Pure domain logic, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.domain.value_objects.channel_resolution import ChannelSearchResult


@dataclass(frozen=True)
class CycleChannelCandidatesService:
    """Service for cycling through channel search candidates.
    
    Purpose:
        Manages state for cycling through top-N candidates during subscription.
        Immutable: decline() returns new instance with advanced index.
    
    Attributes:
        candidates: List of ChannelSearchResult candidates
        index: Current candidate index (0-based)
    """
    
    candidates: List[ChannelSearchResult]
    index: int = 0
    
    def __post_init__(self) -> None:
        """Validate state."""
        if self.index < 0:
            raise ValueError(f"Index must be >= 0, got {self.index}")
        # Allow empty candidates list (but index must be 0)
        if not self.candidates and self.index != 0:
            raise ValueError(f"Index must be 0 for empty candidates list, got {self.index}")
        if self.candidates and self.index >= len(self.candidates):
            raise ValueError(
                f"Index {self.index} out of range for {len(self.candidates)} candidates"
            )
    
    def current(self) -> ChannelSearchResult:
        """Get current candidate.
        
        Returns:
            Current ChannelSearchResult
        
        Raises:
            IndexError: If no candidates available or index out of range
        """
        if not self.candidates:
            raise IndexError("No candidates available")
        if self.index >= len(self.candidates):
            raise IndexError(f"Index {self.index} out of range")
        return self.candidates[self.index]
    
    def decline(self) -> CycleChannelCandidatesService:
        """Advance to next candidate on decline.
        
        Purpose:
            Returns new immutable instance with index advanced by 1.
            Original instance remains unchanged.
        
        Returns:
            New CycleChannelCandidatesService with advanced index
        
        Raises:
            IndexError: If already at last candidate
        """
        if not self.has_next():
            raise IndexError("No more candidates available")
        
        # Return new instance with incremented index
        return CycleChannelCandidatesService(
            candidates=self.candidates,
            index=self.index + 1,
        )
    
    def has_next(self) -> bool:
        """Check if there are more candidates after current.
        
        Returns:
            True if there is at least one more candidate, False otherwise
        """
        return self.index < len(self.candidates) - 1
    
    def is_exhausted(self) -> bool:
        """Check if all candidates have been exhausted.
        
        Purpose:
            Returns True if current candidate is the last one and
            cannot be declined further, or if no candidates available.
        
        Returns:
            True if exhausted, False otherwise
        """
        if not self.candidates:
            return True
        return not self.has_next()
    
    def remaining_count(self) -> int:
        """Get count of remaining candidates (excluding current).
        
        Returns:
            Number of candidates after current
        """
        if not self.candidates:
            return 0
        return max(0, len(self.candidates) - self.index - 1)

