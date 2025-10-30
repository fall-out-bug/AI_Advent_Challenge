"""Schedule helpers for worker timing."""

from __future__ import annotations

from datetime import datetime, time


def is_quiet_hours(dt: datetime, quiet_start: int, quiet_end: int) -> bool:
    """Check if datetime is within quiet hours.

    Purpose:
        Determine if notifications should be suppressed (e.g., 22:00-08:00).

    Args:
        dt: Current datetime
        quiet_start: Quiet hours start hour (0-23)
        quiet_end: Quiet hours end hour (0-23)

    Returns:
        True if within quiet hours
    """
    current_hour = dt.hour
    if quiet_start > quiet_end:  # Crosses midnight (e.g., 22:00-08:00)
        return current_hour >= quiet_start or current_hour < quiet_end
    return quiet_start <= current_hour < quiet_end


def is_time_to_send(dt: datetime, target_time: time, tolerance_minutes: int = 1) -> bool:
    """Check if current time matches target within tolerance.

    Purpose:
        Determine if it's time to send a scheduled notification.

    Args:
        dt: Current datetime
        target_time: Target time (HH:MM)
        tolerance_minutes: Minutes of tolerance (default 1)

    Returns:
        True if within tolerance
    """
    current_time = dt.time()
    if current_time.hour != target_time.hour:
        return False
    return abs(current_time.minute - target_time.minute) <= tolerance_minutes

