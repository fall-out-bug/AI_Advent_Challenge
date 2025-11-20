"""Unit tests for Day 6 Chain of Thought comparison example."""

from __future__ import annotations

from unittest.mock import Mock, patch

from examples.day06_chain_of_thought import CoTAgent, CoTComparison


def test_agent_generates_direct_response() -> None:
    """Test that agent generates direct response without CoT."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "x = 4",
                }
            }
        ]
    }

    agent = CoTAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        response = agent._generate_response("2x + 6 = 14", use_cot=False)

        assert "x = 4" in response
        # Verify prompt doesn't include CoT instructions
        call_args = agent._client.post.call_args
        messages = call_args[1]["json"]["messages"]
        assert "step by step" not in messages[0]["content"].lower()

    agent.close()


def test_agent_generates_cot_response() -> None:
    """Test that agent generates response with CoT instructions."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Step 1: Subtract 6 from both sides... x = 4",
                }
            }
        ]
    }

    agent = CoTAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        response = agent._generate_response("2x + 6 = 14", use_cot=True)

        assert "x = 4" in response
        # Verify prompt includes CoT instructions
        call_args = agent._client.post.call_args
        messages = call_args[1]["json"]["messages"]
        assert "step by step" in messages[0]["content"].lower()

    agent.close()


def test_agent_extracts_answer() -> None:
    """Test that agent extracts answer from response."""
    agent = CoTAgent(llm_url="http://mock")

    # Test with explicit answer marker
    response1 = "The answer is: 4"
    answer1 = agent._extract_answer(response1, "2x + 6 = 14")
    assert "4" in answer1 or answer1 == "4"

    # Test with equation
    response2 = "x = 4"
    answer2 = agent._extract_answer(response2, "2x + 6 = 14")
    assert "4" in answer2 or answer2 == "4"

    # Test without clear marker
    response3 = "Some text without a clear answer"
    answer3 = agent._extract_answer(response3, "unknown problem")
    # Should return None or find a number if present
    assert answer3 is None or answer3.isdigit()

    agent.close()


def test_agent_checks_correctness() -> None:
    """Test that agent checks answer correctness."""
    agent = CoTAgent(llm_url="http://mock")

    # Correct answer for "2x + 6 = 14"
    is_correct = agent._check_correctness("4", "2x + 6 = 14")
    assert is_correct is True

    # Incorrect answer
    is_incorrect = agent._check_correctness("5", "2x + 6 = 14")
    assert is_incorrect is False

    # Unknown problem
    is_unknown = agent._check_correctness("42", "Unknown problem")
    assert is_unknown is None

    agent.close()


def test_agent_compares_cot() -> None:
    """Test that agent compares direct vs CoT responses."""

    def mock_post_side_effect(*args: any, **kwargs: any) -> Mock:
        messages = kwargs.get("json", {}).get("messages", [])
        use_cot = "step by step" in messages[0]["content"].lower()

        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        if use_cot:
            content = "Step 1: Subtract 6. Step 2: Divide by 2. Answer: x = 4"
        else:
            content = "x = 4"
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": content,
                    }
                }
            ]
        }
        return mock_resp

    agent = CoTAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", side_effect=mock_post_side_effect):
        comparison = agent.compare_cot("2x + 6 = 14")

        assert comparison.problem == "2x + 6 = 14"
        assert comparison.direct_response == "x = 4"
        assert (
            "Step 1" in comparison.cot_response
            or "Answer: x = 4" in comparison.cot_response
        )
        assert "4" in comparison.direct_answer or comparison.direct_answer == "4"
        assert "4" in comparison.cot_answer or comparison.cot_answer == "4"
        assert comparison.is_correct_direct is True
        assert comparison.is_correct_cot is True

    agent.close()


def test_cot_comparison_dataclass() -> None:
    """Test CoTComparison dataclass structure."""
    comparison = CoTComparison(
        problem="test problem",
        direct_response="direct answer",
        cot_response="cot answer",
        direct_answer="answer1",
        cot_answer="answer2",
        is_correct_direct=True,
        is_correct_cot=True,
    )

    assert comparison.problem == "test problem"
    assert comparison.direct_response == "direct answer"
    assert comparison.cot_response == "cot answer"
    assert comparison.direct_answer == "answer1"
    assert comparison.cot_answer == "answer2"
    assert comparison.is_correct_direct is True
    assert comparison.is_correct_cot is True
