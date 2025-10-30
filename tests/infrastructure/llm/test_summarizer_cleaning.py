import pytest

from src.infrastructure.llm.summarizer import _clean_text_for_summary


def test_clean_text_removes_urls_and_normalizes_whitespace() -> None:
    raw = "Check this https://example.com/page?utm_source=x  now\n\n  please"
    cleaned = _clean_text_for_summary(raw)
    assert "http" not in cleaned
    assert "utm_" not in cleaned
    assert "  " not in cleaned
    assert cleaned.endswith("please")


def test_clean_text_removes_trailing_markers() -> None:
    raw = "Новость об обновлении... читать далее"
    cleaned = _clean_text_for_summary(raw)
    assert "читать далее" not in cleaned.lower()
    assert cleaned.endswith("обновлении")
