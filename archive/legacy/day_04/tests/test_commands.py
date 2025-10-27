import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from terminal_chat_v4 import DedChatV4, _contains_any, _normalize_for_trigger


def test_contains_any_and_normalize():
	assert _contains_any("ну покеда уже", ["покеда"]) is True
	# unicode dash and punctuation variants for "не душни"
	norm = _normalize_for_trigger("Не—душни!")
	assert "не душни" in norm


@pytest.mark.parametrize("text,expected", [
	("Ладно, не душни, по делу", 0.0),
	("Давай, разгоняй идеи", 1.2),
	("Эй, потише, дед", 0.7),
])
def test_apply_interactive_temperature(text, expected):
	chat = DedChatV4()
	chat.apply_interactive_temperature(text)
	assert chat.default_temperature == expected


def test_print_includes_model_and_temp_in_explain(capsys):
	chat = DedChatV4()
	chat.current_api = "chadgpt"
	chat.explain_mode = True
	chat.print_ded_message("привет", 0.7)
	out = capsys.readouterr().out
	assert "T=0.70" in out
	assert "chadgpt:gpt-5-mini" in out


def test_print_includes_suffix_in_normal_mode(capsys):
	chat = DedChatV4()
	chat.current_api = "perplexity"
	chat.explain_mode = False
	chat.print_ded_message("привет", 1.2)
	out = capsys.readouterr().out
	assert "(T=1.2" in out  # suffix shows raw eff value
	assert "perplexity:" in out


