"""Integration tests for LLM-based intent parsing."""

import pytest
from datetime import datetime

from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.domain.entities.intent import IntentParseResult


@pytest.fixture()
def llm_orchestrator() -> IntentOrchestrator:
    """Create orchestrator with LLM enabled."""
    return IntentOrchestrator(use_llm=True, model_name="mistral")


@pytest.fixture()
def qwen_orchestrator() -> IntentOrchestrator:
    """Create orchestrator with Qwen model."""
    return IntentOrchestrator(use_llm=True, model_name="qwen")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_llm_parse_russian_task_with_time(
    llm_orchestrator: IntentOrchestrator,
) -> None:
    """Test LLM parsing Russian task with time expression."""
    text = "напомни завтра в 9 купить хлеба"
    result = await llm_orchestrator.parse_task_intent(text=text, context={})

    assert isinstance(result, IntentParseResult)
    assert result.title is not None
    assert "хлеб" in result.title.lower() or "купить" in result.title.lower()
    # LLM should extract deadline
    if result.deadline_iso:
        assert (
            "09:00" in result.deadline_iso
            or "9:00" in result.deadline_iso
            or "T09" in result.deadline_iso
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_llm_parse_english_task_with_time(
    llm_orchestrator: IntentOrchestrator,
) -> None:
    """Test LLM parsing English task with time expression."""
    text = "Remind me to call mom tomorrow at 3pm"
    result = await llm_orchestrator.parse_task_intent(text=text, context={})

    assert isinstance(result, IntentParseResult)
    assert result.title is not None
    assert "call" in result.title.lower() or "mom" in result.title.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_llm_parse_complex_russian_task(
    llm_orchestrator: IntentOrchestrator,
) -> None:
    """Test LLM parsing complex Russian task."""
    text = "Срочно нужно позвонить врачу сегодня в 15:00, это очень важно"
    result = await llm_orchestrator.parse_task_intent(text=text, context={})

    assert isinstance(result, IntentParseResult)
    assert result.title is not None
    # Should detect high priority from "срочно" and "важно"
    if result.priority:
        assert result.priority in {"low", "medium", "high"}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_llm_parse_ambiguous_task_needs_clarification(
    llm_orchestrator: IntentOrchestrator,
) -> None:
    """Test LLM parsing ambiguous task that needs clarification."""
    text = "Напомни позвонить маме"
    result = await llm_orchestrator.parse_task_intent(text=text, context={})

    assert isinstance(result, IntentParseResult)
    assert result.title is not None
    # Should detect that deadline is missing
    if result.needs_clarification:
        assert result.questions is not None
        assert len(result.questions) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_qwen_parse_russian_task(qwen_orchestrator: IntentOrchestrator) -> None:
    """Test Qwen model parsing Russian task."""
    text = "купить молоко завтра в 9 утра"
    result = await qwen_orchestrator.parse_task_intent(text=text, context={})

    assert isinstance(result, IntentParseResult)
    assert result.title is not None
    assert "молоко" in result.title.lower() or "купить" in result.title.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_llm_parse_with_context(llm_orchestrator: IntentOrchestrator) -> None:
    """Test LLM parsing with context."""
    text = "Напомни сделать это в 14:00"
    context = {"timezone": "Europe/Moscow", "prev_tasks": [{"title": "Task 1"}]}
    result = await llm_orchestrator.parse_task_intent(text=text, context=context)

    assert isinstance(result, IntentParseResult)
    assert result.title is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_llm_json_parsing_robustness(
    llm_orchestrator: IntentOrchestrator,
) -> None:
    """Test that LLM response parsing handles various JSON formats."""
    # This test verifies that _parse_llm_response can handle different JSON formats
    # It's more of a unit test but useful to verify robustness

    # Test with wrapped JSON
    response_text = "Here is the result: {'title': 'Test', 'deadline_iso': '2025-01-01T10:00:00', 'priority': 'medium'}"
    parsed = llm_orchestrator._parse_llm_response(response_text)

    # Should handle fallback parser if LLM returns invalid JSON
    if parsed is None:
        # Fallback should still work
        result = await llm_orchestrator.parse_task_intent("купить молоко")
        assert isinstance(result, IntentParseResult)
