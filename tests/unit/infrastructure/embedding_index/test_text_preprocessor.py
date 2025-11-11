"""Tests for TextPreprocessor."""

from __future__ import annotations

from pathlib import Path

from src.infrastructure.embedding_index.preprocessing.text_preprocessor import (
    TextPreprocessor,
)


def test_preprocess_strips_front_matter(tmp_path: Path) -> None:
    """Ensure front matter is removed and whitespace normalised."""
    content = "---\ntitle: Sample\n---\nLine one\n\nLine two\r\n"
    file_path = tmp_path / "sample.md"
    file_path.write_text(content, encoding="utf-8")

    preprocessor = TextPreprocessor()
    result = preprocessor.preprocess(file_path)

    assert "title: Sample" not in result
    assert result == "Line one\n\nLine two"


def test_supports_filters_extensions(tmp_path: Path) -> None:
    """Ensure unsupported extensions are rejected."""
    preprocessor = TextPreprocessor()
    supported = tmp_path / "doc.md"
    unsupported = tmp_path / "image.png"
    supported.write_text("text", encoding="utf-8")
    unsupported.write_text("data", encoding="utf-8")

    assert preprocessor.supports(supported) is True
    assert preprocessor.supports(unsupported) is False
