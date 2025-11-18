"""Test fixtures for personalization use case integration tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.application.personalization.personalization_service import (
    PersonalizationServiceImpl,
)
from src.application.personalization.use_cases.personalized_reply import (
    PersonalizedReplyUseCase,
)
from src.application.personalization.use_cases.reset_personalization import (
    ResetPersonalizationUseCase,
)
from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository,
)
from src.infrastructure.personalization.profile_repository import (
    MongoUserProfileRepository,
)


@pytest.fixture
def profile_repo(real_mongodb):
    """Provide MongoUserProfileRepository instance."""
    client = real_mongodb.client
    return MongoUserProfileRepository(client, real_mongodb.name)


@pytest.fixture
def memory_repo(real_mongodb):
    """Provide MongoUserMemoryRepository instance."""
    client = real_mongodb.client
    return MongoUserMemoryRepository(client, real_mongodb.name)


@pytest.fixture
def personalization_service(profile_repo):
    """Provide PersonalizationServiceImpl instance."""
    return PersonalizationServiceImpl(profile_repo)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Добрый день, сэр. Чем могу быть полезен?")
    return client


@pytest.fixture
def personalized_reply_use_case(
    personalization_service, memory_repo, profile_repo, mock_llm_client
):
    """Provide PersonalizedReplyUseCase instance."""
    return PersonalizedReplyUseCase(
        personalization_service,
        memory_repo,
        profile_repo,
        mock_llm_client,
    )


@pytest.fixture
def reset_use_case(profile_repo, memory_repo):
    """Provide ResetPersonalizationUseCase instance."""
    return ResetPersonalizationUseCase(profile_repo, memory_repo)
