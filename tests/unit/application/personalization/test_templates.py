"""Tests for prompt templates."""

import pytest

from src.application.personalization.templates import (
    format_full_prompt,
    format_memory_context,
    format_persona_section,
)


def test_format_persona_section():
    """Test persona section formatting."""
    section = format_persona_section(
        "Alfred-style дворецкий", "witty", "ru", ["Python", "AI"]
    )

    assert "Alfred" in section
    assert "witty" in section
    assert "ru" in section
    assert "Python" in section
    assert "AI" in section


def test_format_persona_section_empty_topics():
    """Test persona section with empty topics."""
    section = format_persona_section("Alfred-style дворецкий", "witty", "ru", [])

    assert "Alfred" in section
    assert "general topics" in section


def test_format_memory_context_with_summary():
    """Test memory context with summary."""
    context = format_memory_context(
        "User asked about Python", ["- User: Hello", "- Butler: Good day"]
    )

    assert "Summary" in context
    assert "Python" in context
    assert "Recent conversation" in context
    assert "Hello" in context


def test_format_memory_context_without_summary():
    """Test memory context without summary."""
    context = format_memory_context(None, ["- User: Hello"])

    assert "Summary" not in context
    assert "Hello" in context
    assert "Recent conversation" in context


def test_format_memory_context_empty():
    """Test memory context with no summary and no events."""
    context = format_memory_context(None, [])

    assert context == ""


def test_format_memory_context_only_summary():
    """Test memory context with only summary, no events."""
    context = format_memory_context("User likes Python", [])

    assert "Summary" in context
    assert "Python" in context
    assert "Recent conversation" not in context


def test_format_full_prompt():
    """Test full prompt assembly."""
    prompt = format_full_prompt("You are Alfred", "Previous context", "Hello")

    assert "Alfred" in prompt
    assert "Previous context" in prompt
    assert "User: Hello" in prompt
    assert "Butler:" in prompt


def test_format_full_prompt_empty_context():
    """Test full prompt with empty memory context."""
    prompt = format_full_prompt("You are Alfred", "", "Hello")

    assert "Alfred" in prompt
    assert "User: Hello" in prompt
    assert "(No previous context)" in prompt


def test_format_persona_section_single_topic():
    """Test persona section with single topic."""
    section = format_persona_section(
        "Alfred-style дворецкий", "witty", "ru", ["Python"]
    )

    assert "Python" in section
    assert ", " not in section or section.count("Python") == 1
