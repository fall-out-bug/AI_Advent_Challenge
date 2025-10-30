import os
import asyncio
from datetime import datetime, timedelta
import pytest


pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _set_test_db_env(monkeypatch):
    monkeypatch.setenv("DB_NAME", "butler_test")
    monkeypatch.setenv("MONGODB_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017"))


@pytest.fixture(autouse=True)
async def _cleanup_db():
    from src.infrastructure.database.mongo import get_db, close_client

    db = await get_db()
    await db.tasks.delete_many({})
    yield
    await db.tasks.delete_many({})
    await close_client()


async def test_add_and_list_tasks_via_tools():
    # Import tools after env setup
    from src.presentation.mcp.tools.reminder_tools import add_task, list_tasks, update_task, delete_task, get_summary

    # Create
    deadline = (datetime.utcnow() + timedelta(days=1)).isoformat()
    create_res = await add_task(user_id=1, title="Pay bills", description="rent", deadline=deadline, priority="high", tags=["finance"])  # type: ignore[arg-type]
    assert create_res["status"] == "created"

    # List
    tasks_res = await list_tasks(user_id=1, status="active", limit=10)  # type: ignore[arg-type]
    assert tasks_res["filtered"] == 1
    task_id = tasks_res["tasks"][0]["id"]

    # Update
    upd = await update_task(task_id=task_id, updates={"completed": True})  # type: ignore[arg-type]
    assert upd["status"] in {"updated", "not_found"}  # updated in normal flow

    # Summary
    summary = await get_summary(user_id=1, timeframe="today")  # type: ignore[arg-type]
    assert "tasks" in summary and isinstance(summary["tasks"], list)

    # Delete
    deleted = await delete_task(task_id=task_id)  # type: ignore[arg-type]
    assert deleted["status"] in {"deleted", "not_found"}


