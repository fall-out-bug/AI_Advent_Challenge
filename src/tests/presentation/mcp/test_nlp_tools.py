import pytest


@pytest.mark.asyncio
async def test_parse_task_intent_tool_returns_dict():
    from src.presentation.mcp.tools.nlp_tools import parse_task_intent

    res = await parse_task_intent("buy milk at 5pm", user_context={"tz": "UTC"})  # type: ignore[arg-type]
    assert isinstance(res, dict)
    assert "title" in res
    assert "priority" in res


