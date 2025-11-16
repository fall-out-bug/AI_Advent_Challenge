"""Unit tests for Day 2 output schema example."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

from examples.day02_output_schema import StructuredAgent, WeatherResponse


def test_agent_builds_prompt_with_schema() -> None:
    """Test that agent builds prompt with schema instructions."""
    agent = StructuredAgent(llm_url="http://mock")
    prompt = agent._build_prompt("What is the weather?")

    assert "location" in prompt.lower()
    assert "temperature" in prompt.lower()
    assert "json" in prompt.lower()
    assert "What is the weather?" in prompt

    agent.close()


def test_agent_parses_json_response() -> None:
    """Test that agent correctly parses structured JSON response."""
    mock_data = {
        "location": "Moscow",
        "temperature": 15.5,
        "condition": "Sunny",
        "humidity": 70,
    }

    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(mock_data),
                }
            }
        ]
    }

    agent = StructuredAgent(llm_url="http://mock")

    with patch.object(agent._client, "post", return_value=mock_response):
        result = agent.handle("What is the weather?")
        assert isinstance(result, WeatherResponse)
        assert result.location == "Moscow"
        assert result.temperature == 15.5
        assert result.condition == "Sunny"
        assert result.humidity == 70

    agent.close()


def test_weather_response_dataclass() -> None:
    """Test WeatherResponse dataclass structure."""
    response = WeatherResponse(
        location="Paris",
        temperature=20.0,
        condition="Cloudy",
        humidity=60,
    )

    assert response.location == "Paris"
    assert response.temperature == 20.0
    assert response.condition == "Cloudy"
    assert response.humidity == 60

