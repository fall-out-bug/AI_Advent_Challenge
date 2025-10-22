import os
import sys
import pytest

# Ensure project root (day_04) is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from temperature_utils import clamp_temperature, resolve_effective_temperature


@pytest.mark.parametrize("inp, outp", [
	(0.0, 0.0),
	(0.2, 0.2),
	(1.234, 1.23),
	(1.9, 1.5),
])
def test_clamp_ok(inp, outp):
	assert clamp_temperature(inp) == outp


@pytest.mark.parametrize("inp", [-0.1, 2.1])
def test_clamp_fail(inp):
	with pytest.raises(ValueError):
		clamp_temperature(inp)


def test_resolve_priority():
	assert resolve_effective_temperature(1.2, None, 0.7) == 1.2
	assert resolve_effective_temperature(None, 1.0, 0.7) == 1.0
	assert resolve_effective_temperature(None, None, 0.7) == 0.7


