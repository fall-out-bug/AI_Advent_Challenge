"""Unit tests for interest extraction service."""

import json
from unittest.mock import AsyncMock

import pytest

from src.application.personalization.interest_extraction_service import (
    InterestExtractionService,
    LLMClient,
)
from src.domain.personalization.user_memory_event import UserMemoryEvent


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response: str):
        """Initialize with mock response.

        Args:
            response: Mock LLM response text.
        """
        self.response = response
        self.calls = []

    async def generate(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 256
    ) -> str:
        """Generate mock response.

        Args:
            prompt: Input prompt (stored for verification).
            temperature: Temperature parameter.
            max_tokens: Max tokens parameter.

        Returns:
            Mock response text.
        """
        self.calls.append({"prompt": prompt, "temperature": temperature})
        return self.response


@pytest.mark.asyncio
async def test_extract_interests_from_python_conversation():
    """Test interest extraction from Python-themed conversation."""
    # Mock LLM response
    llm_response = json.dumps(
        {
            "summary": "User discussed Python development and Docker deployment",
            "interests": ["Python", "Docker", "Clean Architecture"],
        }
    )

    llm_client = MockLLMClient(llm_response)
    service = InterestExtractionService(llm_client, max_topics=7)

    # Sample events
    events = [
        UserMemoryEvent.create_user_event("123", "I'm learning Python"),
        UserMemoryEvent.create_assistant_event("123", "Excellent choice, sir."),
        UserMemoryEvent.create_user_event("123", "How do I deploy with Docker?"),
    ]

    # Extract
    summary, interests = await service.extract_interests(events, existing_topics=[])

    # Verify
    assert "Python" in summary or "Python" in interests
    assert "Python" in interests
    assert "Docker" in interests
    assert len(interests) <= 7
    assert len(interests) >= 1


@pytest.mark.asyncio
async def test_merge_interests_with_existing():
    """Test merging new interests with existing topics."""
    llm_response = json.dumps(
        {
            "summary": "User discussed Python and Clean Architecture",
            "interests": ["Python", "Clean Architecture", "Telegram bots"],
        }
    )

    llm_client = MockLLMClient(llm_response)
    service = InterestExtractionService(llm_client, max_topics=7)

    events = [
        UserMemoryEvent.create_user_event("123", "Python question"),
    ]

    existing_topics = ["Python", "Docker"]

    # Extract
    summary, interests = await service.extract_interests(events, existing_topics)

    # Verify merge: Python should be first (confirmed), then Docker, then new
    assert "Python" in interests
    assert "Docker" in interests  # Existing topic preserved
    assert len(interests) <= 7


@pytest.mark.asyncio
async def test_filter_sensitive_data():
    """Test that sensitive data is filtered from interests."""
    # LLM might return sensitive data (should be filtered)
    llm_response = json.dumps(
        {
            "summary": "User discussed API keys",
            "interests": [
                "Python",
                "sk-1234567890abcdefghijklmnopqrstuvwxyz",  # API key (should be filtered)
                "password=mysecret",  # Password (should be filtered)
                "Docker",
            ],
        }
    )

    llm_client = MockLLMClient(llm_response)
    service = InterestExtractionService(llm_client, max_topics=7)

    events = [
        UserMemoryEvent.create_user_event("123", "I use Python"),
    ]

    summary, interests = await service.extract_interests(events, existing_topics=[])

    # Verify sensitive data filtered
    assert "Python" in interests
    assert "Docker" in interests
    assert "sk-" not in " ".join(interests)
    assert "password" not in " ".join(interests).lower()


@pytest.mark.asyncio
async def test_json_parse_error_graceful_fallback():
    """Test graceful fallback on JSON parse errors."""
    # Invalid JSON response
    llm_response = "This is not valid JSON {"

    llm_client = MockLLMClient(llm_response)
    service = InterestExtractionService(llm_client, max_topics=7)

    events = [
        UserMemoryEvent.create_user_event("123", "Hello"),
    ]

    existing_topics = ["Python"]

    # Extract (should not raise, should fallback)
    summary, interests = await service.extract_interests(events, existing_topics)

    # Verify fallback: keep existing topics, basic summary
    assert interests == existing_topics  # Preserved
    assert len(summary) > 0  # Basic summary generated


@pytest.mark.asyncio
async def test_missing_json_keys_graceful_fallback():
    """Test graceful fallback on missing JSON keys."""
    # JSON missing required keys
    llm_response = json.dumps({"summary": "Some summary"})  # Missing "interests"

    llm_client = MockLLMClient(llm_response)
    service = InterestExtractionService(llm_client, max_topics=7)

    events = [
        UserMemoryEvent.create_user_event("123", "Hello"),
    ]

    existing_topics = ["Python"]

    # Extract (should not raise, should fallback)
    summary, interests = await service.extract_interests(events, existing_topics)

    # Verify fallback
    assert interests == existing_topics  # Preserved


@pytest.mark.asyncio
async def test_max_topics_constraint():
    """Test that max_topics constraint is enforced."""
    # LLM returns more topics than max
    llm_response = json.dumps(
        {
            "summary": "User discussed many topics",
            "interests": [
                "Python",
                "Docker",
                "Clean Architecture",
                "Telegram bots",
                "FastAPI",
                "PostgreSQL",
                "Redis",
                "Kubernetes",  # 8th topic (should be capped)
            ],
        }
    )

    llm_client = MockLLMClient(llm_response)
    service = InterestExtractionService(llm_client, max_topics=7)

    events = [
        UserMemoryEvent.create_user_event("123", "Topic question"),
    ]

    summary, interests = await service.extract_interests(events, existing_topics=[])

    # Verify max_topics constraint
    assert len(interests) <= 7


@pytest.mark.asyncio
async def test_empty_events_handling():
    """Test handling of empty events list."""
    llm_client = MockLLMClient('{"summary": "", "interests": []}')
    service = InterestExtractionService(llm_client, max_topics=7)

    existing_topics = ["Python"]

    # Extract with empty events
    summary, interests = await service.extract_interests([], existing_topics)

    # Should return existing topics
    assert interests == existing_topics
    assert summary == ""


@pytest.mark.asyncio
async def test_contains_sensitive_data():
    """Test sensitive data detection."""
    service = InterestExtractionService(MockLLMClient(""), max_topics=7)

    # Test API key pattern
    assert service._contains_sensitive_data("sk-1234567890abcdefghijklmnop")
    assert service._contains_sensitive_data("API_KEY=secret123")

    # Test password pattern
    assert service._contains_sensitive_data("password=mysecret")

    # Test file path pattern
    assert service._contains_sensitive_data("/home/user/data.txt")

    # Test valid topics (should not be filtered)
    assert not service._contains_sensitive_data("Python")
    assert not service._contains_sensitive_data("Docker")
    assert not service._contains_sensitive_data("Clean Architecture")
