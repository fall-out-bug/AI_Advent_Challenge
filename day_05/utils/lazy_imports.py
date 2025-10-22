"""
Lazy loading utilities for imports.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

from typing import Any, Optional
import sys
import os


class LazyImport:
    """Lazy import wrapper for expensive modules."""
    
    def __init__(self, module_name: str):
        """Initialize lazy import."""
        self._module_name = module_name
        self._module: Optional[Any] = None
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute from lazily loaded module."""
        if self._module is None:
            self._module = __import__(self._module_name, fromlist=[name])
        return getattr(self._module, name)


def lazy_import(module_name: str):
    """Create lazy import wrapper."""
    return LazyImport(module_name)


def conditional_import(module_name: str, fallback: Any = None):
    """Import module with fallback if not available."""
    try:
        return __import__(module_name)
    except ImportError:
        return fallback


def get_shared_sdk_path() -> str:
    """Get path to shared SDK."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
        'shared'
    )


def add_shared_sdk_to_path():
    """Add shared SDK to Python path."""
    shared_path = get_shared_sdk_path()
    if shared_path not in sys.path:
        sys.path.append(shared_path)


# Lazy imports for expensive modules
httpx = lazy_import('httpx')
asyncio = lazy_import('asyncio')
unicodedata = lazy_import('unicodedata')
shutil = lazy_import('shutil')
textwrap = lazy_import('textwrap')
functools = lazy_import('functools')
dataclasses = lazy_import('dataclasses')
