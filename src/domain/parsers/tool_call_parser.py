"""Tool-call parsing utilities.

Provides robust extraction of tool invocation JSON from LLM text output
with multiple strategies and a heuristic fallback.

Public API:
- extract_json_from_text(text)
- extract_tool_from_text_heuristic(text)
- ToolCallParser.parse(text, strict=False)
- ToolCallParser.parse_with_fallback(text, max_attempts=3)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from raw model text.

    Strategy order:
    1) Direct JSON parse (entire text is JSON)
    2) Fenced blocks: ```json ... ``` or ``` ... ```
    3) Braces block: first balanced {...} that parses and looks like a tool call
    4) Multiline slice from first '{' to last '}'

    Args:
        text: Model output that may contain JSON.

    Returns:
        Parsed JSON dict or None if nothing valid found.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    content = text.strip()

    # Strategy 1: direct parse
    try:
        result = json.loads(content)
        logger.debug("Direct JSON parse successful")
        return result
    except json.JSONDecodeError:
        pass

    # Strategy 2: fenced blocks
    patterns_triple = [
        r"```json\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
        r"```(.*?)```",
    ]
    for pattern in patterns_triple:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if not match:
            continue
        json_str = match.group(1).strip()
        try:
            result = json.loads(json_str)
            logger.debug("JSON from triple-quotes parse successful")
            return result
        except json.JSONDecodeError:
            logger.debug("Failed to parse from triple-quotes: %s", json_str[:80])

    # Strategy 3: braces blocks (attempt nested tolerant find)
    brace_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    for match in re.finditer(brace_pattern, content):
        candidate = match.group(0)
        try:
            result = json.loads(candidate)
            if isinstance(result, dict) and ("tool" in result or "params" in result):
                logger.debug("JSON from braces parse successful")
                return result
        except json.JSONDecodeError:
            # Try fixing unquoted JSON
            fixed = _fix_unquoted_json(candidate)
            if fixed and fixed != candidate:
                try:
                    result = json.loads(fixed)
                    if isinstance(result, dict) and ("tool" in result or "params" in result):
                        logger.debug("JSON from fixed braces parse successful")
                        return result
                except json.JSONDecodeError:
                    pass
            logger.debug("Failed to parse from braces: %s", candidate[:80])

    # Strategy 4: slice from first '{' to last '}'
    first = content.find("{")
    last = content.rfind("}")
    if first != -1 and last != -1 and first < last:
        candidate = content[first : last + 1]
        try:
            result = json.loads(candidate)
            logger.debug("JSON from multiline slice successful")
            return result
        except json.JSONDecodeError:
            # Strategy 4b: try fixing unquoted keys/values (common Mistral issue)
            fixed = _fix_unquoted_json(candidate)
            if fixed and fixed != candidate:
                try:
                    result = json.loads(fixed)
                    logger.debug("JSON from fixed unquoted parse successful")
                    return result
                except json.JSONDecodeError:
                    logger.debug("Failed to parse fixed JSON: %s", fixed[:80])

    logger.warning("Could not extract JSON from text: %s", content[:120])
    return None


def _fix_unquoted_json(text: str) -> Optional[str]:
    """Fix common JSON issues: unquoted keys and string values.
    
    Args:
        text: JSON-like string with potential unquoted keys/values.
        
    Returns:
        Fixed JSON string or None if not fixable.
    """
    if not text or not text.strip().startswith("{"):
        return None
    
    try:
        # Try to add quotes around keys
        # Pattern: {key: value} -> {"key": value}
        import re
        
        # Fix keys: word after { or , or whitespace, followed by :
        fixed = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
        
        # Fix string values that look like words (after : and before , or })
        # But avoid numbers and booleans
        def fix_value(match):
            val = match.group(1)
            # Skip if it's a number, boolean, or already quoted
            if val in ("true", "false", "null") or val.replace(".", "").isdigit():
                return match.group(0)
            # Add quotes if it's a word-like value
            if re.match(r'^[a-zA-Zа-яА-ЯЁё][a-zA-Z0-9а-яА-ЯЁё\s\-_]*$', val):
                return f': "{val}"'
            return match.group(0)
        
        fixed = re.sub(r':\s*([^,}\]]+?)(?=\s*[,}\]])', fix_value, fixed)
        
        return fixed
    except Exception:
        return None


def extract_tool_from_text_heuristic(text: str) -> Optional[Dict[str, Any]]:
    """Heuristically extract tool name and params from plain text.

    This is a fallback when JSON is missing. It scans for known intents
    and pulls simple parameters like channel name and days (Russian/English).

    Args:
        text: Model output text.

    Returns:
        Dict with keys "tool" and "params", or None if not recognized.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    tools_map: Dict[str, List[str]] = {
        "get_channel_digest_by_name": [
            r"digest.*channel",
            r"дайджест.*канала?",
            r"дайджест\b",
        ],
        "get_channel_digest": [r"digest.*all", r"дайджест.*все"],
        "list_channels": [r"list.*channel", r"список.*каналов?"],
        "add_channel": [r"add.*channel", r"добавить.*канал"],
        "get_channel_metadata": [r"metadata.*channel", r"информация.*канала?"],
    }

    lower = text.lower()
    detected: Optional[str] = None
    for tool_name, patterns in tools_map.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                detected = tool_name
                break
        if detected:
            break

    if not detected:
        return None

    params: Dict[str, Any] = {}

    # channel name extraction
    channel_patterns = [
        r'canal[" ]*:?\s*["\']?([^"\'}\n]+)',
        r'канал\s*["\']?([^"\'}\n]+)',
        r'["\']?channel_name["\']?\s*:\s*["\']?([^"\'}\n]+)',
        r'по\s+([^\s\n]+)\s+за',  # e.g., "по Набока за 3 дня"
    ]
    # For listing, do not force channel extraction
    if detected != "list_channels":
        for pattern in channel_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                value = m.group(1).strip().strip('"\'')
                if value:
                    params["channel_name"] = value
                    break

    # days extraction
    days_patterns = [
        r"(\d+)\s*(?:дн|день|дня)",
        r'days?["\']?\s*:\s*(\d+)',
    ]
    for pattern in days_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                params["days"] = int(m.group(1))
            except ValueError:
                pass
            break

    if not params and detected not in ["list_channels"]:
        return None

    return {"tool": detected, "params": params}


class ToolCallParser:
    """Full parser for tool-call extraction with fallbacks.

    Methods are static for ease of use and testability.
    """

    @staticmethod
    def parse(text: str, strict: bool = False) -> Optional[Dict[str, Any]]:
        """Parse tool call from text using JSON-first then heuristics.

        Args:
            text: Model output text.
            strict: If True, only JSON parsing is allowed.

        Returns:
            Dict with keys "tool" and "params", or None.
        """
        json_result = extract_json_from_text(text)
        if json_result and ToolCallParser._validate_tool_call(json_result):
            logger.info("JSON parse successful: %s", json_result.get("tool"))
            return json_result

        if strict:
            return None

        heuristic = extract_tool_from_text_heuristic(text)
        if heuristic:
            logger.info("Heuristic parse successful: %s", heuristic.get("tool"))
            return heuristic

        logger.warning("Could not parse tool call from text")
        return None

    @staticmethod
    def parse_with_fallback(text: str, max_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """Parse with multiple attempts and fragment fallbacks.

        Args:
            text: Model output text.
            max_attempts: Max attempts (best-effort; used for fragment loop bound).

        Returns:
            Parsed tool-call dict or None.
        """
        cleaned = ToolCallParser._clean_text(text)

        result = ToolCallParser.parse(cleaned, strict=True)
        if result:
            return result

        result = ToolCallParser.parse(cleaned, strict=False)
        if result:
            return result

        fragments = [frag for frag in cleaned.split("\n\n") if frag.strip()]
        attempts = 0
        for frag in fragments:
            if attempts >= max_attempts:
                break
            attempts += 1
            result = ToolCallParser.parse(frag, strict=False)
            if result:
                logger.debug("Parsed from fragment")
                return result

        return None

    @staticmethod
    def _validate_tool_call(tool_call: Dict[str, Any]) -> bool:
        """Validate basic structure of a tool-call dict.

        Args:
            tool_call: Candidate dict.

        Returns:
            True if valid.
        """
        if not isinstance(tool_call, dict):
            return False
        if "tool" not in tool_call or "params" not in tool_call:
            return False
        if not isinstance(tool_call["tool"], str):
            return False
        params = tool_call.get("params")
        if params is not None and not isinstance(params, dict):
            return False
        return True

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove common wrappers and system markup from model output.

        Args:
            text: Raw model response text.

        Returns:
            Cleaned text suitable for parsing.
        """
        if not isinstance(text, str):
            return ""

        remove_patterns = [
            r"Available tools:.*?(?=\n\n|\Z)",
            r"<\|im_start\|>.*?<\|im_end\|>",
            r"\[INST\].*?\[/INST\]",
            r">>>.*?<<<",
        ]
        cleaned = text
        for pattern in remove_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.strip()


