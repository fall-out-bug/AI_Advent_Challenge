import pytest

from src.domain.parsers.tool_call_parser import (
    extract_json_from_text,
    extract_tool_from_text_heuristic,
    ToolCallParser,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            '{"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока"}}',
            {"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока"}},
        ),
        (
            """Вот JSON:\n```json\n{\"tool\": \"list_channels\", \"params\": {}}\n```\n""",
            {"tool": "list_channels", "params": {}},
        ),
        (
            "Пример:\n{\n  \"tool\": \"add_channel\",\n  \"params\": {\n    \"channel_name\": \"python\"\n  }\n}\n",
            {"tool": "add_channel", "params": {"channel_name": "python"}},
        ),
        (
            """{
  "tool": "get_channel_digest_by_name",
  "params": {
    "channel_name": "Набока",
    "days": 3
  }
}""",
            {"tool": "get_channel_digest_by_name", "params": {"channel_name": "Набока", "days": 3}},
        ),
    ],
)
def test_extract_json_from_text(text, expected):
    assert extract_json_from_text(text) == expected


def test_extract_json_from_text_none():
    assert extract_json_from_text("") is None
    assert extract_json_from_text(None) is None  # type: ignore[arg-type]


def test_extract_tool_from_text_heuristic_russian_days():
    messy = "Хочу дайджест по каналу Набока за 3 дня"
    result = extract_tool_from_text_heuristic(messy)
    assert result is not None
    assert result["tool"] in {"get_channel_digest_by_name", "get_channel_digest"}
    assert result["params"].get("days") == 3


def test_extract_tool_from_text_heuristic_list_channels():
    messy = "Покажи список каналов"
    result = extract_tool_from_text_heuristic(messy)
    assert result == {"tool": "list_channels", "params": {}}


def test_parser_parse_strict_success():
    text = '{"tool": "list_channels", "params": {}}'
    parsed = ToolCallParser.parse(text, strict=True)
    assert parsed == {"tool": "list_channels", "params": {}}


def test_parser_parse_strict_fails_then_heuristic():
    text = "Сделай дайджест по Набока за 2 дня"
    parsed = ToolCallParser.parse(text, strict=False)
    assert parsed is not None
    assert parsed["tool"] in {"get_channel_digest_by_name", "get_channel_digest"}


def test_parse_with_fallback_fragments():
    text = """
Какие каналы у меня?

```json
{"tool": "list_channels", "params": {}}
```
"""
    parsed = ToolCallParser.parse_with_fallback(text)
    assert parsed == {"tool": "list_channels", "params": {}}


