"""Adapter for token analysis operations."""
import sys
from pathlib import Path
from typing import Any

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))

from src.domain.services.token_analyzer import TokenAnalyzer
from src.presentation.mcp.exceptions import MCPAdapterError


class TokenAdapter:
    """Adapter for token counting operations."""

    def __init__(self, token_analyzer: TokenAnalyzer) -> None:
        """Initialize token adapter."""
        self.token_analyzer = token_analyzer

    def count_text_tokens(self, text: str) -> dict[str, int]:
        """Count tokens in text."""
        try:
            token_count = self.token_analyzer.count_tokens(text)
            return {"count": int(token_count)}
        except Exception as e:
            raise MCPAdapterError(f"Failed to count tokens: {e}")
