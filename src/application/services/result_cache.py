"""Result cache service for caching tool execution results.

Following Python Zen: "Simple is better than complex."
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class ResultCache:
    """Thread-safe cache for tool execution results with TTL.
    
    The cache stores results of tool executions keyed by tool name
    and a hash of the arguments. Results expire after a TTL period.
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000) -> None:
        """Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cached entries
            max_size: Maximum number of entries
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def get(self, tool_name: str, args: Dict[str, Any]) -> Optional[Any]:
        """Get cached result if available and not expired.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._make_key(tool_name, args)
        
        with self._lock:
            if cache_key not in self._cache:
                return None
            
            entry = self._cache[cache_key]
            if self._is_expired(entry):
                del self._cache[cache_key]
                logger.debug(f"Cache entry expired: {cache_key}")
                return None
            
            return entry["result"]

    def set(self, tool_name: str, args: Dict[str, Any], result: Any) -> None:
        """Store result in cache.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            result: Result to cache
        """
        cache_key = self._make_key(tool_name, args)
        
        with self._lock:
            # Evict oldest entry if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[cache_key] = {
                "result": result,
                "timestamp": time.time(),
            }

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "entries": self._get_entry_keys(),
            }

    def _make_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Create cache key from tool name and args.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Cache key string
        """
        args_json = json.dumps(args, sort_keys=True)
        args_hash = hashlib.md5(args_json.encode()).hexdigest()
        return f"{tool_name}:{args_hash}"

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired.
        
        Args:
            entry: Cache entry
            
        Returns:
            True if expired
        """
        age = time.time() - entry["timestamp"]
        return age > self.ttl_seconds

    def _evict_oldest(self) -> None:
        """Evict oldest cache entry."""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]["timestamp"]
        )
        del self._cache[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key}")

    def _get_entry_keys(self) -> list[str]:
        """Get list of cache entry keys.
        
        Returns:
            List of cache keys
        """
        return list(self._cache.keys())

