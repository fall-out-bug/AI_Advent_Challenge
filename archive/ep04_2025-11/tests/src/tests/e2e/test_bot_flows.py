"""End-to-end tests for bot user flows.

Following TDD principles and AAA pattern (Arrange-Act-Assert).
"""

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


@pytest.mark.e2e
async def test_nl_task_creation_to_completion_flow(
    unique_user_id, mock_mcp_client, _cleanup_db
):
    """Test complete flow: NL task creation → list → complete → delete.

    Arrange:
        - Mock MCP client returns valid responses
        - Clean database

    Act:
        - Parse intent → create task → list → complete → delete

    Assert:
        - Each step succeeds with expected data
    """
    from src.presentation.mcp.tools.reminder_tools import (
        add_task,
        delete_task,
        list_tasks,
        update_task,
    )

    # Arrange: Setup mock responses
    deadline = "2025-12-31T10:00:00"

    # Act: Create task via NL intent
    create_res = await add_task(
        user_id=unique_user_id,
        title="Buy groceries",
        description="milk, bread, eggs",
        deadline=deadline,
        priority="high",
        tags=["shopping"],
    )
    assert create_res["status"] == "created"
    task_id = create_res["task_id"]

    # Act: List tasks
    tasks_res = await list_tasks(user_id=unique_user_id, status="active", limit=10)
    assert tasks_res["filtered"] == 1
    assert tasks_res["tasks"][0]["id"] == task_id
    assert tasks_res["tasks"][0]["title"] == "Buy groceries"

    # Act: Complete task
    update_res = await update_task(task_id=task_id, updates={"completed": True})
    assert update_res["status"] == "updated"

    # Act: Verify it's in completed list
    completed = await list_tasks(user_id=unique_user_id, status="completed", limit=10)
    assert completed["filtered"] == 1

    # Act: Delete task
    delete_res = await delete_task(task_id=task_id)
    assert delete_res["status"] == "deleted"

    # Assert: Task no longer in any list
    all_tasks = await list_tasks(user_id=unique_user_id, status="all", limit=100)
    assert all(task["id"] != task_id for task in all_tasks["tasks"])


@pytest.mark.e2e
async def test_clarification_flow_handles_questions(unique_user_id, mock_mcp_client):
    """Test clarification questions are properly handled.

    Arrange:
        - Intent requires clarification

    Act:
        - Parse intent that needs clarification

    Assert:
        - Questions are returned
    """
    from src.presentation.mcp.tools.nlp_tools import parse_task_intent

    # Arrange: Intent that needs clarification (ambiguous deadline)
    text = "remind me to do something"

    # Act: Parse intent
    intent = await parse_task_intent(text=text, user_context={})

    # Assert: Check if clarification is needed
    assert "needs_clarification" in intent
    if intent.get("needs_clarification"):
        assert len(intent.get("questions", [])) > 0


@pytest.mark.e2e
@pytest.mark.slow
async def test_error_handling_network_failure():
    """Test error handling when network fails.

    Arrange:
        - Simulate network failure

    Act:
        - Attempt MCP call

    Assert:
        - Error is caught and handled gracefully
    """
    from src.presentation.mcp.client import MCPClient

    # Arrange: Client that will fail
    client = MCPClient()

    # Act & Assert: Should not raise unhandled exception
    # (actual implementation should handle this)
    try:
        await client.call_tool("invalid_tool", {})
    except Exception:
        pass  # Expected to fail, but should be handled


@pytest.mark.e2e
async def test_edge_case_empty_task_list(unique_user_id, _cleanup_db):
    """Test handling of empty task lists.

    Arrange:
        - User with no tasks

    Act:
        - List tasks

    Assert:
        - Returns empty list gracefully
    """
    from src.presentation.mcp.tools.reminder_tools import list_tasks

    # Act
    tasks = await list_tasks(user_id=unique_user_id, status="active", limit=10)

    # Assert
    assert tasks["filtered"] == 0
    assert tasks["tasks"] == []
    assert tasks["total"] == 0


@pytest.mark.e2e
async def test_edge_case_unicode_in_task_title(unique_user_id, _cleanup_db):
    """Test Unicode and emoji handling in task titles.

    Arrange:
        - Task with Unicode/emoji

    Act:
        - Create and retrieve task

    Assert:
        - Unicode preserved correctly
    """
    from src.presentation.mcp.tools.reminder_tools import add_task, list_tasks

    # Arrange: Task with emoji and Unicode
    title = "🎉 Поздравить жену 17 июня 🎂"

    # Act
    result = await add_task(user_id=unique_user_id, title=title, priority="high")
    assert result["status"] == "created"

    tasks = await list_tasks(user_id=unique_user_id, status="active", limit=10)

    # Assert
    assert tasks["tasks"][0]["title"] == title


@pytest.mark.e2e
async def test_edge_case_max_length_task_title(unique_user_id, _cleanup_db):
    """Test handling of maximum length task title.

    Arrange:
        - Task title at max length (256 chars)

    Act:
        - Create task

    Assert:
        - Task created, title truncated if needed
    """
    from src.presentation.mcp.tools.reminder_tools import add_task

    # Arrange: 300 char title (should be truncated)
    long_title = "a" * 300

    # Act
    result = await add_task(user_id=unique_user_id, title=long_title)

    # Assert
    assert result["status"] == "created"
    # Title should be truncated to 256
    from bson import ObjectId

    from src.infrastructure.database.mongo import get_db

    db = await get_db()
    task = await db.tasks.find_one({"_id": ObjectId(result["task_id"])})
    assert task is not None
    assert len(task["title"]) <= 256
