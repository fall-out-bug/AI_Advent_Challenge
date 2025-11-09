import pytest
from datetime import datetime

from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.domain.entities.intent import IntentParseResult


@pytest.fixture()
def orchestrator() -> IntentOrchestrator:
    return IntentOrchestrator(use_llm=False)  # Use fallback parser for tests


@pytest.mark.asyncio
async def test_parse_clear_intent_no_clarification(
    orchestrator: IntentOrchestrator,
) -> None:
    text = "Call mom on 2025-12-01 15:00 high"
    result = await orchestrator.parse_task_intent(text=text, context={})

    assert isinstance(result, IntentParseResult)
    assert result.needs_clarification is False
    assert result.title.lower().startswith("call mom")
    assert result.priority in {"low", "medium", "high"}
    assert isinstance(result.deadline_iso, str)


@pytest.mark.asyncio
async def test_parse_ambiguous_intent_needs_clarification(
    orchestrator: IntentOrchestrator,
) -> None:
    text = "Remind me to call mom tomorrow"
    result = await orchestrator.parse_task_intent(text=text, context={})

    assert result.needs_clarification is True
    assert result.questions, "Expected at least one clarifying question"
    assert any("when" in q.lower() or "deadline" in q.lower() for q in result.questions)


@pytest.mark.asyncio
async def test_parse_russian_time_expression(orchestrator: IntentOrchestrator) -> None:
    """Test parsing Russian time expressions like 'завтра в 9'."""
    text = "напомни завтра в 9 купить хлеба"
    result = await orchestrator.parse_task_intent(text=text, context={})

    assert isinstance(result, IntentParseResult)
    assert (
        result.needs_clarification is False
    ), "Should not need clarification when time is specified"
    assert result.deadline_iso is not None, "Should extract deadline from 'завтра в 9'"
    assert (
        "09:00" in result.deadline_iso or "9:00" in result.deadline_iso
    ), "Should parse 9 o'clock"


@pytest.mark.asyncio
async def test_parse_russian_time_with_am_pm(orchestrator: IntentOrchestrator) -> None:
    """Test parsing Russian time with AM/PM indicators."""
    text = "купить молоко завтра в 9 утра"
    result = await orchestrator.parse_task_intent(text=text, context={})

    assert isinstance(result, IntentParseResult)
    assert result.needs_clarification is False
    assert result.deadline_iso is not None


def test_validate_intent_completeness(orchestrator: IntentOrchestrator) -> None:
    # Missing deadline should be incomplete
    partial = IntentParseResult(
        title="Buy milk",
        description=None,
        deadline_iso=None,
        priority="low",
        tags=[],
        needs_clarification=False,
        questions=[],
    )
    complete, missing = orchestrator.validate_intent_completeness(partial)
    assert complete is False
    assert any(m in missing for m in ["deadline", "time", "date"])
