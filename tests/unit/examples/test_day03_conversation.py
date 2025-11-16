"""Unit tests for Day 3 conversation example."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

from examples.day03_conversation import ConversationalAgent, RequirementsSpec


def test_agent_builds_system_prompt_with_stop_condition() -> None:
    """Test that agent builds system prompt with stopping instructions."""
    agent = ConversationalAgent(llm_url="http://mock")
    prompt = agent._build_system_prompt()

    assert "requirements" in prompt.lower()
    assert "json" in prompt.lower()
    assert "stop" in prompt.lower() or "complete" in prompt.lower()
    assert "specification" in prompt.lower()

    agent.close()


def test_agent_extracts_spec_from_json_response() -> None:
    """Test that agent correctly extracts specification from JSON response."""
    json_response = """Here is the final specification:

{
    "title": "Task Management System",
    "description": "A system for managing tasks in a small team",
    "functional_requirements": ["Create tasks", "Assign tasks"],
    "non_functional_requirements": ["Response time < 1s"],
    "acceptance_criteria": ["All features work", "Tests pass"]
}

That's the complete specification."""

    agent = ConversationalAgent(llm_url="http://mock")

    spec = agent._extract_spec_from_response(json_response)

    assert spec is not None
    assert spec.title == "Task Management System"
    assert spec.description == "A system for managing tasks in a small team"
    assert len(spec.functional_requirements) == 2
    assert len(spec.non_functional_requirements) == 1
    assert len(spec.acceptance_criteria) == 2

    agent.close()


def test_agent_returns_none_for_non_json_response() -> None:
    """Test that agent returns None when no JSON found in response."""
    text_response = "I need more information. Can you tell me about the team size?"

    agent = ConversationalAgent(llm_url="http://mock")

    spec = agent._extract_spec_from_response(text_response)

    assert spec is None

    agent.close()


def test_requirements_spec_dataclass() -> None:
    """Test RequirementsSpec dataclass structure."""
    spec = RequirementsSpec(
        title="Test Project",
        description="Test description",
        functional_requirements=["Requirement 1", "Requirement 2"],
        non_functional_requirements=["Performance"],
        acceptance_criteria=["Criterion 1"],
    )

    assert spec.title == "Test Project"
    assert spec.description == "Test description"
    assert len(spec.functional_requirements) == 2
    assert len(spec.non_functional_requirements) == 1
    assert len(spec.acceptance_criteria) == 1


def test_agent_handles_multiturn_conversation() -> None:
    """Test that agent correctly manages conversation history."""
    mock_responses = [
        {
            "choices": [
                {
                    "message": {
                        "content": "What is the team size?",
                    }
                }
            ]
        },
        {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "title": "Final Spec",
                                "description": "Description",
                                "functional_requirements": ["Feature 1"],
                                "non_functional_requirements": ["Performance"],
                                "acceptance_criteria": ["Test 1"],
                            }
                        ),
                    }
                }
            ]
        },
    ]

    mock_response_objs = []
    for resp_data in mock_responses:
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = resp_data
        mock_response_objs.append(mock_resp)

    agent = ConversationalAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", side_effect=mock_response_objs):
        system_prompt = agent._build_system_prompt()
        agent._conversation_history.append({"role": "system", "content": system_prompt})

        # First turn: question
        response1 = agent._send_message("Team of 5 people", role="user")
        assert "team size" in response1.lower()

        # Second turn: final spec
        response2 = agent._send_message("", role="user")
        spec = agent._extract_spec_from_response(response2)
        assert spec is not None
        assert spec.title == "Final Spec"

    agent.close()

