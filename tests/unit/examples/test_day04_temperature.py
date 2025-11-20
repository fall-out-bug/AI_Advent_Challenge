"""Unit tests for Day 4 temperature comparison example."""

from __future__ import annotations

from unittest.mock import Mock, patch

from examples.day04_temperature import TemperatureAgent, TemperatureResult


def test_agent_generates_response_with_temperature() -> None:
    """Test that agent generates response with specified temperature."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Test response with temperature 0.7",
                }
            }
        ],
        "usage": {"total_tokens": 50},
    }

    agent = TemperatureAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        result = agent.generate_response("Test prompt", temperature=0.7)

        assert result.temperature == 0.7
        assert "temperature 0.7" in result.response
        assert result.tokens_used == 50
        assert 0.0 <= result.creativity_score <= 1.0

    agent.close()


def test_agent_compares_multiple_temperatures() -> None:
    """Test that agent runs prompt with multiple temperature values."""

    def mock_post_side_effect(*args: any, **kwargs: any) -> Mock:
        temp = kwargs.get("json", {}).get("temperature", 0.0)
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": f"Response at temperature {temp}",
                    }
                }
            ],
            "usage": {"total_tokens": 30 + int(temp * 10)},
        }
        return mock_resp

    agent = TemperatureAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", side_effect=mock_post_side_effect):
        results = agent.compare_temperatures("Test", [0.0, 0.7, 1.2])

        assert len(results) == 3
        assert results[0].temperature == 0.0
        assert results[1].temperature == 0.7
        assert results[2].temperature == 1.2

        # Verify responses contain temperature values
        assert "0.0" in results[0].response or "0" in results[0].response
        assert "0.7" in results[1].response
        assert "1.2" in results[2].response

    agent.close()


def test_temperature_result_dataclass() -> None:
    """Test TemperatureResult dataclass structure."""
    result = TemperatureResult(
        temperature=0.5,
        response="Test response",
        tokens_used=100,
        creativity_score=0.75,
    )

    assert result.temperature == 0.5
    assert result.response == "Test response"
    assert result.tokens_used == 100
    assert result.creativity_score == 0.75


def test_creativity_score_calculation() -> None:
    """Test that creativity score is calculated from response diversity."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    # Response with many unique words (high creativity)
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "A B C D E F G H I J",
                }
            }
        ],
        "usage": {"total_tokens": 50},
    }

    agent = TemperatureAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        result = agent.generate_response("Test", temperature=1.0)

        # All words unique, so creativity should be 1.0
        assert result.creativity_score == 1.0

    agent.close()
