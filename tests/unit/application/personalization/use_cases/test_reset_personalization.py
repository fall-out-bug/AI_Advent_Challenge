"""Tests for ResetPersonalizationUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.application.personalization.dtos import ResetPersonalizationInput
from src.application.personalization.use_cases.reset_personalization import (
    ResetPersonalizationUseCase,
)


@pytest.fixture
def mock_profile_repo():
    """Mock profile repository."""
    repo = MagicMock()
    repo.reset = AsyncMock()
    return repo


@pytest.fixture
def mock_memory_repo():
    """Mock memory repository."""
    repo = MagicMock()
    repo.count_events = AsyncMock(return_value=50)
    repo.compress = AsyncMock()
    return repo


@pytest.fixture
def use_case(mock_profile_repo, mock_memory_repo):
    """Create use case instance."""
    return ResetPersonalizationUseCase(mock_profile_repo, mock_memory_repo)


@pytest.mark.asyncio
async def test_execute_resets_successfully(use_case, mock_profile_repo, mock_memory_repo):
    """Test successful reset operation."""
    input_data = ResetPersonalizationInput(user_id="123")
    output = await use_case.execute(input_data)

    assert output.success is True
    assert output.profile_reset is True
    assert output.memory_deleted_count == 50
    mock_profile_repo.reset.assert_called_once_with("123")
    mock_memory_repo.compress.assert_called_once_with("123", "", keep_last_n=0)


@pytest.mark.asyncio
async def test_execute_handles_errors(use_case, mock_profile_repo):
    """Test error handling during reset."""
    mock_profile_repo.reset.side_effect = Exception("DB error")

    input_data = ResetPersonalizationInput(user_id="123")
    output = await use_case.execute(input_data)

    assert output.success is False
    assert output.profile_reset is False
    assert output.memory_deleted_count == 0


@pytest.mark.asyncio
async def test_execute_with_zero_memory(use_case, mock_memory_repo):
    """Test reset when user has no memory events."""
    mock_memory_repo.count_events.return_value = 0

    input_data = ResetPersonalizationInput(user_id="123")
    output = await use_case.execute(input_data)

    assert output.success is True
    assert output.memory_deleted_count == 0

