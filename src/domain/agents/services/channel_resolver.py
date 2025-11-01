"""Channel resolution service.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import re
import logging
from typing import Optional, Callable

from src.presentation.mcp.client import MCPClientProtocol

logger = logging.getLogger(__name__)


class ChannelResolver:
    """Service for resolving human-readable channel names to usernames.
    
    Single responsibility: resolve channel hints to canonical usernames.
    """

    def __init__(self, mcp_client: MCPClientProtocol):
        """Initialize channel resolver.
        
        Args:
            mcp_client: MCP client for accessing channel metadata
        """
        self.mcp_client = mcp_client

    async def resolve(
        self,
        channel_hint: str,
        user_id: int,
        trace_callback: Optional[Callable[[str, str, str], None]] = None
    ) -> Optional[str]:
        """Resolve channel hint to username.
        
        Strategy:
        1. Check user's subscriptions first
        2. Search by metadata (title/username matching)
        3. Try transliteration-based guesses
        
        Args:
            channel_hint: Human-readable channel name or username
            user_id: Telegram user ID for subscription lookup
            trace_callback: Optional callback for tracing (tool_name, status, info)
            
        Returns:
            Resolved username or None if not found
        """
        sanitized = self._sanitize_channel_hint(channel_hint)
        if not sanitized:
            return None
        
        # Strategy 1: Check subscriptions
        username = await self._check_subscriptions(sanitized, user_id, trace_callback)
        if username:
            return username
        
        # Strategy 2: Search by metadata
        username = await self._resolve_via_metadata(sanitized, user_id, trace_callback)
        if username:
            return username
        
        # Strategy 3: Try transliteration guesses
        return await self._resolve_via_transliteration(sanitized, user_id, trace_callback)

    async def _check_subscriptions(
        self,
        channel_hint: str,
        user_id: int,
        trace_callback: Optional[callable]
    ) -> Optional[str]:
        """Check if channel exists in user's subscriptions.
        
        Args:
            channel_hint: Channel hint to search for
            user_id: User ID for subscription lookup
            trace_callback: Optional tracing callback
            
        Returns:
            Username if found, None otherwise
        """
        try:
            listed = await self.mcp_client.call_tool("list_channels", {"user_id": user_id})
            channels = listed.get("channels", []) if isinstance(listed, dict) else []
            
            if trace_callback:
                trace_callback("list_channels", "success", f"total={len(channels)}")
            
            query = self._norm(channel_hint)
            for ch in channels:
                uname = (ch.get("channel_username") or "").lstrip("@")
                if uname and self._norm(uname) == query:
                    return uname
                if uname and self._norm(uname).find(query) != -1:
                    return uname
        except Exception as e:
            logger.warning(f"Failed to check subscriptions: {e}")
            if trace_callback:
                trace_callback("list_channels", "error", str(e))
        return None

    async def _resolve_via_metadata(
        self,
        human_name: str,
        user_id: int,
        trace_callback: Optional[callable]
    ) -> Optional[str]:
        """Resolve channel using metadata title matching.
        
        Args:
            human_name: Human-readable channel name
            user_id: User ID for metadata lookup
            trace_callback: Optional tracing callback
            
        Returns:
            Username if found, None otherwise
        """
        query = self._norm(human_name)
        try:
            listed = await self.mcp_client.call_tool("list_channels", {"user_id": user_id})
            channels = listed.get("channels", []) if isinstance(listed, dict) else []
            
            for ch in channels:
                uname = (ch.get("channel_username") or "").lstrip("@")
                if not uname:
                    continue
                
                meta = await self.mcp_client.call_tool(
                    "get_channel_metadata", {"channel_username": uname, "user_id": user_id}
                )
                
                if trace_callback:
                    trace_callback("get_channel_metadata", "success", uname)
                
                title = (meta or {}).get("title") or (meta or {}).get("name")
                if title and self._approx_match(query, self._norm(str(title))):
                    return uname
        except Exception:
            return None
        return None

    async def _resolve_via_transliteration(
        self,
        human_name: str,
        user_id: int,
        trace_callback: Optional[callable]
    ) -> Optional[str]:
        """Resolve channel using transliteration guesses.
        
        Args:
            human_name: Human-readable channel name
            user_id: User ID for metadata lookup
            trace_callback: Optional tracing callback
            
        Returns:
            Username if found, None otherwise
        """
        query = self._norm(human_name)
        candidates = self._guess_usernames_from_human_name(human_name)
        
        for candidate in candidates:
            try:
                meta = await self.mcp_client.call_tool(
                    "get_channel_metadata", {"channel_username": candidate, "user_id": user_id}
                )
                
                if trace_callback:
                    trace_callback("get_channel_metadata", "success", candidate)
                
                title = (meta or {}).get("title") or (meta or {}).get("name")
                if title and self._approx_match(query, self._norm(str(title))):
                    return candidate
            except Exception:
                continue
        return None

    def _norm(self, s: str) -> str:
        """Normalize string for comparison.
        
        Args:
            s: String to normalize
            
        Returns:
            Normalized string (lowercase, stripped, @ removed)
        """
        return str(s).strip().lower().lstrip("@")

    def _approx_match(self, query: str, target: str) -> bool:
        """Loose match to account for minor inflections/typos.
        
        Args:
            query: Query string
            target: Target string to match against
            
        Returns:
            True if strings approximately match
        """
        if not query or not target:
            return False
        if query in target or target in query:
            return True
        if len(query) >= 4 and target.startswith(query[:4]):
            return True
        if len(query) > 4 and query[:-1] in target:
            return True
        return False

    def _guess_usernames_from_human_name(self, human: str) -> list[str]:
        """Generate username candidates from human-readable name.
        
        Args:
            human: Human-readable channel name
            
        Returns:
            List of candidate usernames
        """
        s = self._norm(human)
        if not s:
            return []
        
        translit_map = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
            "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
            "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
            "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
        }
        
        def transliterate(name: str) -> str:
            return "".join(translit_map.get(ch, ch) for ch in name)

        base = transliterate(s)
        candidates = {base, base.replace(" ", ""), base.replace(" ", "_")}
        candidates |= {"o" + c for c in list(candidates)}
        candidates = {re.sub(r"[^a-z0-9_]+", "", c) for c in candidates}
        return [c for c in candidates if c]

    def _sanitize_channel_hint(self, value: Optional[str]) -> str:
        """Sanitize channel hint from model output.
        
        Args:
            value: Raw channel hint value
            
        Returns:
            Sanitized channel hint
        """
        s = (value or "").strip().strip('"\'').strip()
        if not s:
            return s
        
        # Remove trailing days artifacts
        s = re.sub(r",?\s*\bdays\b\s*:\s*\d+\s*$", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+за\s+\d+\s*(?:дн|день|дня).*$", "", s, flags=re.IGNORECASE)
        s = re.sub(r"[\s,;]+$", "", s)
        return s

