"""Unit tests for Day 8 token handling example."""

from __future__ import annotations

from examples.day08_token_handling import TokenAnalysis, TokenHandlingAgent


def test_agent_analyzes_text() -> None:
    """Test that agent analyzes text token usage."""
    agent = TokenHandlingAgent(token_limit=100)

    analysis = agent.analyze_text("Hello world")

    assert analysis.token_count > 0
    assert analysis.char_count == len("Hello world")
    assert analysis.tokens_per_char > 0
    assert isinstance(analysis.exceeds_limit, bool)


def test_agent_detects_exceeded_limit() -> None:
    """Test that agent detects when text exceeds token limit."""
    agent = TokenHandlingAgent(token_limit=10)

    short_text = "Hello"
    long_text = "This is a very long text that should definitely exceed the token limit of 10 tokens."

    short_analysis = agent.analyze_text(short_text)
    long_analysis = agent.analyze_text(long_text)

    assert not short_analysis.exceeds_limit
    assert long_analysis.exceeds_limit


def test_agent_truncates_text() -> None:
    """Test that agent truncates text to fit token limit."""
    agent = TokenHandlingAgent(token_limit=20)

    long_text = "This is a very long text that needs to be truncated to fit within the token limit."

    truncated = agent.truncate_text(long_text, max_tokens=20)

    # Verify truncated text is shorter and within limit
    truncated_analysis = agent.analyze_text(truncated)
    assert truncated_analysis.token_count <= 20
    assert len(truncated) < len(long_text)
    assert truncated.endswith("...")


def test_agent_summarizes_text() -> None:
    """Test that agent summarizes text to fit token limit."""
    agent = TokenHandlingAgent(token_limit=50)

    long_text = """This is the first sentence. This is the second sentence.
    This is the third sentence. This is the fourth sentence. This is the fifth sentence.
    This is a very long text that should definitely exceed the token limit when fully included.
    Additional sentences to ensure the text is long enough to require summarization."""

    summary = agent.summarize_text(long_text, target_tokens=50)

    # Verify summary is within token limit
    summary_analysis = agent.analyze_text(summary)
    assert summary_analysis.token_count <= 50
    assert "[Summary:" in summary


def test_token_analysis_dataclass() -> None:
    """Test TokenAnalysis dataclass structure."""
    analysis = TokenAnalysis(
        text="test",
        token_count=5,
        char_count=4,
        tokens_per_char=1.25,
        exceeds_limit=False,
        limit=100,
    )

    assert analysis.text == "test"
    assert analysis.token_count == 5
    assert analysis.char_count == 4
    assert analysis.tokens_per_char == 1.25
    assert analysis.exceeds_limit is False
    assert analysis.limit == 100


def test_agent_compares_requests() -> None:
    """Test that agent compares different request sizes."""
    agent = TokenHandlingAgent(token_limit=100)

    short = "Hello"
    long_text = (
        "This is a longer text with more content that should still be within limits."
    )
    overflow = (
        "This is a very long text that definitely exceeds the token limit and needs to be handled properly."
        * 10
    )

    # Verify analysis works for all sizes
    short_analysis = agent.analyze_text(short)
    long_analysis = agent.analyze_text(long_text)
    overflow_analysis = agent.analyze_text(overflow)

    assert short_analysis.token_count < long_analysis.token_count
    assert long_analysis.token_count < overflow_analysis.token_count
    assert overflow_analysis.exceeds_limit
