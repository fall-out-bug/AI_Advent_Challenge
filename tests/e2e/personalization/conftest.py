"""Test fixtures for personalization E2E tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.clients.llm_client import get_llm_client


@pytest.fixture
def llm_client():
    """Provide LLM client for E2E tests."""
    # Use real LLM client if available, otherwise mock
    try:
        return get_llm_client()
    except Exception:
        # Fallback to mock for tests without LLM
        client = MagicMock()
        client.generate = AsyncMock(
            return_value="Добрый день, сэр. Надеюсь, день проходит без излишней драмы? Чем могу быть полезен?"
        )
        return client
