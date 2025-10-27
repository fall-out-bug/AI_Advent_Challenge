"""Compression result value objects."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CompressionRatio:
    """
    Immutable compression ratio value object.

    Attributes:
        original_size: Original size in tokens
        compressed_size: Compressed size in tokens
        ratio: Compression ratio
    """

    original_size: int
    compressed_size: int
    ratio: float

    def __post_init__(self) -> None:
        """Validate and calculate compression ratio."""
        if self.original_size <= 0:
            raise ValueError("Original size must be positive")
        if self.compressed_size < 0:
            raise ValueError("Compressed size cannot be negative")

        calculated_ratio = self.compressed_size / self.original_size
        if abs(self.ratio - calculated_ratio) > 0.001:
            raise ValueError("Ratio does not match calculated value")

    @property
    def savings_percentage(self) -> float:
        """Calculate token savings percentage."""
        return (1 - self.ratio) * 100

    @property
    def is_compressed(self) -> bool:
        """Check if data was actually compressed."""
        return self.ratio < 1.0


@dataclass
class CompressionResult:
    """
    Comprehensive compression result value object.

    Attributes:
        compression_ratio: Compression ratio information
        method: Compression method used
        metadata: Optional additional metadata
    """

    compression_ratio: CompressionRatio
    method: str
    metadata: Optional[dict] = None

    @property
    def original_tokens(self) -> int:
        """Get original token count."""
        return self.compression_ratio.original_size

    @property
    def compressed_tokens(self) -> int:
        """Get compressed token count."""
        return self.compression_ratio.compressed_size

    @property
    def original_text(self) -> str:
        """Get original text."""
        if self.metadata:
            return self.metadata.get("original_text", "")
        return ""

    @property
    def compressed_text(self) -> str:
        """Get compressed text."""
        if self.metadata:
            return self.metadata.get("compressed_text", "")
        return ""

    def __post_init__(self) -> None:
        """Validate compression result."""
        if not self.method:
            raise ValueError("Compression method cannot be empty")
