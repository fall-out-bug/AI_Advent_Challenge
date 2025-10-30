import pytest
from datetime import time, datetime


def test_is_quiet_hours_within_quiet_time():
    from src.workers.schedulers import is_quiet_hours

    # 23:00 should be in quiet hours (22:00-08:00)
    dt = datetime(2025, 1, 1, 23, 0)
    assert is_quiet_hours(dt, quiet_start=22, quiet_end=8) is True


def test_is_quiet_hours_outside_quiet_time():
    from src.workers.schedulers import is_quiet_hours

    # 10:00 should NOT be in quiet hours
    dt = datetime(2025, 1, 1, 10, 0)
    assert is_quiet_hours(dt, quiet_start=22, quiet_end=8) is False


def test_is_time_to_send_matches():
    from src.workers.schedulers import is_time_to_send

    # 9:00 matches 9:00 target
    dt = datetime(2025, 1, 1, 9, 0)
    assert is_time_to_send(dt, target_time=time(9, 0), tolerance_minutes=1) is True


def test_is_time_to_send_within_tolerance():
    from src.workers.schedulers import is_time_to_send

    # 9:01 should be within 1 minute tolerance of 9:00
    dt = datetime(2025, 1, 1, 9, 1)
    assert is_time_to_send(dt, target_time=time(9, 0), tolerance_minutes=1) is True

