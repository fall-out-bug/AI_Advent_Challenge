"""Unit tests for PersonalizedPrompt value object."""

from src.domain.personalization.personalized_prompt import PersonalizedPrompt


def test_personalized_prompt_creation():
    """Test personalized prompt creation."""
    prompt = PersonalizedPrompt(
        persona_section="You are Alfred",
        memory_context="Previous: User asked about Python",
        new_message="Tell me more",
        full_prompt="You are Alfred\n\nPrevious: User asked about Python\n\nUser: Tell me more\nButler:",
    )

    assert prompt.persona_section == "You are Alfred"
    assert prompt.memory_context == "Previous: User asked about Python"
    assert prompt.new_message == "Tell me more"
    assert "Tell me more" in prompt.full_prompt


def test_estimate_tokens():
    """Test token estimation calculation."""
    # 40 characters = ~10 tokens (40 / 4)
    prompt = PersonalizedPrompt(
        persona_section="You are Alfred",
        memory_context="Previous chat",
        new_message="Hello",
        full_prompt="A" * 40,  # 40 characters
    )

    assert prompt.estimate_tokens() == 10


def test_estimate_tokens_boundary():
    """Test token estimation with boundary values."""
    # 0 characters = 0 tokens
    prompt = PersonalizedPrompt(
        persona_section="",
        memory_context="",
        new_message="",
        full_prompt="",
    )

    assert prompt.estimate_tokens() == 0

    # 4 characters = 1 token
    prompt = PersonalizedPrompt(
        persona_section="",
        memory_context="",
        new_message="",
        full_prompt="test",
    )

    assert prompt.estimate_tokens() == 1


def test_is_within_limit():
    """Test is_within_limit() check."""
    # 4000 characters = 1000 tokens (within 2000 limit, exactly at 1000 limit)
    prompt = PersonalizedPrompt(
        persona_section="You are Alfred",
        memory_context="Previous chat",
        new_message="Hello",
        full_prompt="A" * 4000,
    )

    assert prompt.is_within_limit(2000) is True
    assert prompt.is_within_limit(1000) is True  # Exactly at limit
    assert prompt.is_within_limit(999) is False  # Below limit


def test_is_within_limit_exact_boundary():
    """Test is_within_limit() at exact boundary."""
    # 8000 characters = 2000 tokens (exactly at limit)
    prompt = PersonalizedPrompt(
        persona_section="",
        memory_context="",
        new_message="",
        full_prompt="A" * 8000,
    )

    assert prompt.is_within_limit(2000) is True
    assert prompt.is_within_limit(1999) is False


def test_is_within_limit_custom_limit():
    """Test is_within_limit() with custom limit."""
    # 4000 characters = 1000 tokens
    prompt = PersonalizedPrompt(
        persona_section="",
        memory_context="",
        new_message="",
        full_prompt="A" * 4000,
    )

    assert prompt.is_within_limit(1000) is True
    assert prompt.is_within_limit(500) is False


def test_estimate_tokens_large_prompt():
    """Test token estimation with large prompt."""
    # 20000 characters = 5000 tokens
    prompt = PersonalizedPrompt(
        persona_section="You are Alfred",
        memory_context="Previous chat",
        new_message="Hello",
        full_prompt="A" * 20000,
    )

    assert prompt.estimate_tokens() == 5000
    assert prompt.is_within_limit(2000) is False


def test_prompt_sections():
    """Test that all prompt sections are accessible."""
    prompt = PersonalizedPrompt(
        persona_section="Persona instructions",
        memory_context="Memory context",
        new_message="New message",
        full_prompt="Full prompt text",
    )

    assert prompt.persona_section == "Persona instructions"
    assert prompt.memory_context == "Memory context"
    assert prompt.new_message == "New message"
    assert prompt.full_prompt == "Full prompt text"
