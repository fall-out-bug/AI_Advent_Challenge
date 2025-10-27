import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from temperature_utils import clamp_temperature
from terminal_chat_v4 import DedChatV4


@pytest.mark.asyncio
async def test_apply_interactive_temperature_rules():
	chat = DedChatV4()
	# default
	assert chat.default_temperature == 0.7

	# "не душни" -> 0.0
	chat.apply_interactive_temperature("Ладно, не душни, по делу")
	assert chat.default_temperature == 0.0

	# "разгоняй" -> 1.2
	chat.apply_interactive_temperature("Ну-ка разгоняй идеи")
	assert chat.default_temperature == 1.2

	# "потише" -> 0.7
	chat.apply_interactive_temperature("Эй, потише там")
	assert chat.default_temperature == 0.7


def test_parse_temp_override_formats():
	chat = DedChatV4()
	over, text = chat.parse_temp_override("temp=1.2 Привет")
	assert over == 1.2 and text == "Привет"

	# no override
	over, text = chat.parse_temp_override("Привет")
	assert over is None and text == "Привет"


