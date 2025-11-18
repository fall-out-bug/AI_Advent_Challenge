"""Tests for Day 1 basic agent example."""

from __future__ import annotations

from examples.day01_basic_agent import BasicAgent, EchoTool


def test_echo_tool_returns_expected_prefix() -> None:
    """EchoTool should prefix the question with marker."""
    tool = EchoTool()
    result = tool.run("hello")
    assert "[echo_tool] You asked: hello" == result.content


def test_basic_agent_formats_reply() -> None:
    """BasicAgent should call tool and wrap content in reply prefix."""
    agent = BasicAgent(tool=EchoTool())
    reply = agent.handle("hello")
    assert reply.startswith("Agent reply -> ")
    assert "hello" in reply
