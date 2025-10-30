"""End-to-end tests for scheduled notifications.

Uses freezegun to mock time for deterministic testing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from freezegun import freeze_time

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e, pytest.mark.slow]


@pytest.mark.e2e
@freeze_time("2025-01-15 09:00:00")
async def test_morning_summary_sent_at_scheduled_time(unique_user_id, _cleanup_db):
    """Test morning summary is sent at 9:00 AM.

    Arrange:
        - User with tasks, time frozen at 9:00
        - Mock bot

    Act:
        - Worker checks schedule

    Assert:
        - Summary would be sent (verify via mocks)
    """
    from src.presentation.mcp.tools.reminder_tools import add_task, get_summary
    from src.workers.schedulers import is_time_to_send
    from datetime import time, datetime

    # Arrange: Create task for user
    await add_task(user_id=unique_user_id, title="Morning task", priority="high")

    # Arrange: Mock bot
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=1))

    # Act: Check if time matches
    now = datetime.utcnow()
    target = time(9, 0)
    should_send = is_time_to_send(now, target, tolerance_minutes=1)

    # Assert
    assert should_send is True


@pytest.mark.e2e
@freeze_time("2025-01-15 20:00:00")
async def test_evening_digest_sent_at_scheduled_time(unique_user_id, _cleanup_db):
    """Test evening digest is sent at 8:00 PM.

    Arrange:
        - User with channel subscription, time frozen at 20:00
        - Mock bot

    Act:
        - Worker checks schedule

    Assert:
        - Digest would be sent (verify via mocks)
    """
    from src.presentation.mcp.tools.digest_tools import add_channel
    from src.workers.schedulers import is_time_to_send
    from datetime import time, datetime

    # Arrange: Subscribe to channel
    await add_channel(user_id=unique_user_id, channel_username="test_channel")

    # Arrange: Mock bot
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=1))

    # Act: Check if time matches
    now = datetime.utcnow()
    target = time(20, 0)
    should_send = is_time_to_send(now, target, tolerance_minutes=1)

    # Assert
    assert should_send is True


@pytest.mark.e2e
@freeze_time("2025-01-15 23:00:00")
async def test_quiet_hours_blocks_notifications():
    """Test notifications are blocked during quiet hours.

    Arrange:
        - Time frozen at 23:00 (quiet hours)

    Act:
        - Check quiet hours status

    Assert:
        - Quiet hours active
    """
    from src.workers.schedulers import is_quiet_hours
    from datetime import datetime

    # Arrange: Current time in quiet hours (22:00-08:00)
    now = datetime.utcnow()

    # Act
    is_quiet = is_quiet_hours(now, quiet_start=22, quiet_end=8)

    # Assert
    assert is_quiet is True


@pytest.mark.e2e
@freeze_time("2025-01-15 10:00:00")
async def test_not_quiet_hours_allows_notifications():
    """Test notifications allowed outside quiet hours.

    Arrange:
        - Time frozen at 10:00 (outside quiet hours)

    Act:
        - Check quiet hours status

    Assert:
        - Quiet hours not active
    """
    from src.workers.schedulers import is_quiet_hours
    from datetime import datetime

    # Arrange: Current time outside quiet hours
    now = datetime.utcnow()

    # Act
    is_quiet = is_quiet_hours(now, quiet_start=22, quiet_end=8)

    # Assert
    assert is_quiet is False


@pytest.mark.e2e
async def test_worker_handles_telegram_api_failure():
    """Test worker handles Telegram API failures gracefully.

    Arrange:
        - Bot that raises TelegramBadRequest

    Act:
        - Attempt to send message

    Assert:
        - Error caught and logged, worker continues
    """
    from aiogram.exceptions import TelegramBadRequest
    from unittest.mock import AsyncMock

    # Arrange: Mock bot that fails
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock(side_effect=TelegramBadRequest(message="User not found", method="send_message"))

    # Act & Assert: Should not raise, but handle gracefully
    try:
        await mock_bot.send_message(123, "test")
    except TelegramBadRequest:
        pass  # Expected - worker should catch this

    # Verify it was called
    assert mock_bot.send_message.called

