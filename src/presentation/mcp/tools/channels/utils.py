"""Utilities for channel tools.

Following Python Zen:
- Simple is better than complex
- DRY principle
"""

import re
from src.infrastructure.database.mongo import get_db


async def get_database():
    """Get database handle.
    
    Returns:
        MongoDB database instance
    """
    return await get_db()


def normalize_channel_name(s: str) -> str:
    """Normalize string for channel name comparison.
    
    Args:
        s: String to normalize
        
    Returns:
        Normalized string (lowercase, stripped, @ removed)
    """
    return str(s).strip().lower().lstrip("@")


def guess_usernames_from_human_name(human: str) -> list[str]:
    """Generate username candidates from human-readable name.
    
    Args:
        human: Human-readable channel name
        
    Returns:
        List of candidate usernames
    """
    s = normalize_channel_name(human)
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

