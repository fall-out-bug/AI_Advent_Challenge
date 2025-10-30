import pytest


def test_intent_parse_result_schema():
    from src.domain.entities.intent import IntentParseResult

    data = {
        "title": "Buy milk",
        "description": "2L whole",
        "deadline": None,
        "priority": "medium",
        "tags": ["groceries"],
        "needs_clarification": False,
        "questions": [],
    }

    result = IntentParseResult(**data)
    assert result.title == "Buy milk"
    assert result.priority == "medium"


def test_intent_priority_validation():
    from src.domain.entities.intent import IntentParseResult

    with pytest.raises(Exception):
        IntentParseResult(
            title="X",
            description="",
            deadline=None,
            priority="urgent",  # invalid
            tags=[],
            needs_clarification=False,
            questions=[],
        )


def test_clarification_question_model():
    from src.domain.entities.intent import ClarificationQuestion

    q = ClarificationQuestion(text="When is the deadline?", key="deadline")
    assert q.key == "deadline"


