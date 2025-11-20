"""Text preprocessing utilities for embedding index pipeline."""

from __future__ import annotations

import re
from pathlib import Path

from src.infrastructure.logging import get_logger

_FRONT_MATTER_PATTERN = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


class TextPreprocessor:
    """Convert supported documents into normalised plain text.

    Purpose:
        Provide a minimal preprocessing step that strips markdown front matter
        and normalises whitespace before chunking.
    """

    _SUPPORTED_EXTENSIONS = {
        ".md",
        ".markdown",
        ".txt",
    }

    def __init__(self, *, encoding: str = "utf-8") -> None:
        """Initialise preprocessor.

        Purpose:
            Configure text decoding behaviour.

        Args:
            encoding: Preferred file encoding.
        """
        self._encoding = encoding
        self._logger = get_logger(__name__)

    def supports(self, path: Path) -> bool:
        """Return True when the file extension is supported."""
        return path.suffix.lower() in self._SUPPORTED_EXTENSIONS

    def preprocess(self, path: Path) -> str:
        """Convert file contents into normalised plain text."""
        raw = self._read_text(path)
        if not raw.strip():
            return ""
        text = self._strip_front_matter(raw)
        return self._normalise_whitespace(text)

    def _read_text(self, path: Path) -> str:
        """Read file contents using tolerant decoding."""
        try:
            return path.read_text(encoding=self._encoding)
        except UnicodeDecodeError as error:
            self._logger.warning(
                "failed_to_decode_file",
                path=str(path),
                error=str(error),
            )
            return path.read_text(encoding=self._encoding, errors="ignore")

    def _strip_front_matter(self, text: str) -> str:
        """Remove YAML front matter if present."""
        return _FRONT_MATTER_PATTERN.sub("", text, count=1)

    def _normalise_whitespace(self, text: str) -> str:
        """Normalise whitespace and trim trailing spaces."""
        lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
        cleaned = "\n".join(lines)
        return re.sub(r"\n{3,}", "\n\n", cleaned).strip()
