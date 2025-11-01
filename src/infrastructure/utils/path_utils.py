"""Path utilities for shared package imports.

Following Python Zen: "Don't repeat yourself".
"""

import sys
from pathlib import Path
from typing import Optional


_SHARED_PATH_ADDED = False


def ensure_shared_in_path() -> Optional[Path]:
    """Ensure shared package is in Python path.
    
    Purpose:
        Add shared package directory to sys.path once.
        Returns None if shared directory doesn't exist.
    
    Returns:
        Path to shared directory or None if not found
    
    Example:
        >>> shared_path = ensure_shared_in_path()
        >>> if shared_path:
        ...     from shared_package.clients.unified_client import UnifiedModelClient
    """
    global _SHARED_PATH_ADDED
    
    if _SHARED_PATH_ADDED:
        return None
    
    # Find project root (4 levels up from src/infrastructure/utils)
    _root = Path(__file__).parent.parent.parent.parent
    shared_path = _root / "shared"
    
    if shared_path.exists() and shared_path.is_dir():
        shared_str = str(shared_path)
        if shared_str not in sys.path:
            sys.path.insert(0, shared_str)
        _SHARED_PATH_ADDED = True
        return shared_path
    
    return None


