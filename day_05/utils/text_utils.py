"""
Text utilities for chat application.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import unicodedata
from typing import List, Optional


def contains_any(haystack: str, needles: List[str]) -> bool:
    """
    Check if haystack contains any of the needles.
    
    Args:
        haystack: String to search in
        needles: List of strings to search for
        
    Returns:
        True if any needle is found in haystack
    """
    haystack_lower = haystack.lower()
    return any(needle in haystack_lower for needle in needles)


def normalize_for_trigger(text: str) -> str:
    """
    Normalize unicode and punctuation to improve trigger matching.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text with collapsed spaces
    """
    if not text:
        return ""
    
    # Unicode normalize and lower
    normalized = unicodedata.normalize('NFKC', text).lower()
    
    # Replace common separators with space
    separators = [
        "\u2013", "\u2014", "-", "_", "|", ",", ".", "!", "?", 
        "\u00A0", "\u2019", "\u2018", "\u201c", "\u201d", 
        "\"", "'", ":", ";", "(", ")", "[", "]", "{", "}"
    ]
    
    for separator in separators:
        normalized = normalized.replace(separator, " ")
    
    # Collapse spaces
    return " ".join(normalized.split())


def clamp_temperature(value: float) -> float:
    """
    Clamp and normalize temperature value.
    
    Args:
        value: Raw temperature in [0.0, 2.0]
        
    Returns:
        Clamped value in [0.0, 1.5] rounded to 2 decimals
        
    Raises:
        ValueError: If value is None or outside [0.0, 2.0]
        
    Example:
        clamp_temperature(1.234) -> 1.23
    """
    if value is None:
        raise ValueError("Temperature is required")
    if not (0.0 <= value <= 2.0):
        raise ValueError("Temperature must be within [0.0, 2.0]")
    value = min(max(value, 0.0), 1.5)
    return round(value, 2)


def resolve_effective_temperature(
    override: Optional[float],
    user_default: Optional[float],
    system_default: float = 0.7
) -> float:
    """
    Compute effective temperature with priority override > user_default > system_default.
    
    Args:
        override: One-off value for current message
        user_default: User's default value
        system_default: Fallback
        
    Returns:
        Effective temperature
        
    Raises:
        ValueError: From clamp_temperature
        
    Example:
        resolve_effective_temperature(1.2, None) -> 1.2
    """
    raw = override if override is not None else (
        user_default if user_default is not None else system_default
    )
    return clamp_temperature(raw)