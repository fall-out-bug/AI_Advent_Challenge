import pytest

from src.domain.input_processing.russian_parser import RussianInputParser


class TestRussianParser:
    def test_digest_basic(self):
        result = RussianInputParser.parse_digest_request(
            "Создай дайджест по Набока за 3 дня"
        )
        assert result is not None
        assert result["action"] == "digest"
        assert result["days"] == 3
        assert RussianInputParser.normalize_channel_name(result["channel"]) == "onaboka"

    @pytest.mark.parametrize(
        "text",
        [
            "дайджест по Набока",
            "получи дайджест по Набока за 5 дней",
            "по каналу Набока за 2 дня",
            "дайджест по @onaboka за 1 день",
        ],
    )
    def test_digest_variants(self, text):
        result = RussianInputParser.parse_digest_request(text)
        assert result is not None
        assert result["action"] == "digest"
        assert "channel" in result
        assert "days" in result

    def test_list_detection(self):
        for text in ["какие каналы", "список", "мои каналы", "all channels"]:
            assert RussianInputParser.parse_list_request(text) is True

    def test_empty_and_noise(self):
        assert RussianInputParser.parse_digest_request("") is None
        assert RussianInputParser.parse_list_request("") is False
        assert RussianInputParser.parse_digest_request("привет как дела") is None
