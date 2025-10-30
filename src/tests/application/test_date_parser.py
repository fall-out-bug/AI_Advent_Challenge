import pytest


def test_parse_datetime_iso_returns_iso():
    from src.application.services.date_parser import DateParser

    parser = DateParser(tz="UTC", locale="en")
    result = parser.parse_datetime("2025-12-31T10:00:00", tz="UTC")
    assert result == "2025-12-31T10:00:00+00:00"


def test_parse_datetime_natural_language():
    from src.application.services.date_parser import DateParser

    parser = DateParser(tz="UTC", locale="en")
    result = parser.parse_datetime("tomorrow at 5pm", tz="UTC")
    assert result is not None
    assert "+00:00" in result or "Z" in result


def test_parse_datetime_invalid_returns_none():
    from src.application.services.date_parser import DateParser

    parser = DateParser(tz="UTC", locale="en")
    result = parser.parse_datetime("not a date", tz="UTC")
    assert result is None

