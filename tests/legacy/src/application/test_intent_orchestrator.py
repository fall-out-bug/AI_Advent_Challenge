import pytest


class DummyLLM:
    async def generate(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 256
    ) -> str:  # noqa: D401
        # Return a simple JSON for parsing
        return (
            '{"title":"Buy milk","description":"2L","deadline":null,'
            '"priority":"low","tags":["groceries"],"needs_clarification":false,'
            '"questions":[]}'
        )


@pytest.mark.asyncio
async def test_parse_task_intent_basic():
    from src.application.orchestration.intent_orchestrator import IntentOrchestrator

    orchestrator = IntentOrchestrator(llm=DummyLLM())
    result = await orchestrator.parse_task_intent("buy milk tomorrow", context={})
    assert result.title == "Buy milk"
    assert result.priority == "low"


@pytest.mark.asyncio
async def test_refine_with_answers_merges():
    from src.application.orchestration.intent_orchestrator import IntentOrchestrator
    from src.domain.entities.intent import ClarificationQuestion, IntentParseResult

    orchestrator = IntentOrchestrator(llm=DummyLLM())
    base = IntentParseResult(
        title="Buy",
        description="",
        deadline=None,
        priority="medium",
        tags=[],
        needs_clarification=True,
        questions=[ClarificationQuestion(text="When?", key="deadline")],
    )
    refined = await orchestrator.refine_with_answers(base, ["2025-12-31T10:00:00"])
    assert refined.deadline == "2025-12-31T10:00:00"
    assert refined.needs_clarification is False
