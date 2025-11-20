import asyncio

import os
from datetime import datetime, timedelta

import pytest
from pymongo.errors import OperationFailure

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _set_test_db_env(monkeypatch):
    monkeypatch.setenv("DB_NAME", "butler_test")
    monkeypatch.setenv(
        "MONGODB_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    )


@pytest.fixture
async def repo():
    # Lazy import after env setup
    from src.infrastructure.database.mongo import close_client, get_db
    from src.infrastructure.repositories.task_repository import TaskRepository

    db = await get_db()
    try:
        await db.tasks.delete_many({})
    except OperationFailure as error:
        await close_client()
        details = getattr(error, "details", {}) or {}
        message = details.get("errmsg") or str(error)
        pytest.skip(f"MongoDB authentication required for task repository tests: {message}")
    repository = TaskRepository(db)
    try:
        yield repository
    finally:
        await db.tasks.delete_many({})
        await close_client()


async def test_create_and_get_task(repo):
    from src.domain.entities.task import TaskIn

    task_in = TaskIn(
        user_id=123,
        title="Buy milk",
        description="2L whole milk",
        deadline=(datetime.utcnow() + timedelta(days=1)).isoformat(),
        priority="medium",
        tags=["groceries"],
    )

    task_id = await repo.create_task(task_in)
    assert isinstance(task_id, str)

    tasks = await repo.list_tasks(user_id=123, status="active", limit=10)
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Buy milk"


async def test_update_and_delete_task(repo):
    from src.domain.entities.task import TaskIn

    task_in = TaskIn(user_id=999, title="Temp")
    task_id = await repo.create_task(task_in)

    updated = await repo.update_task(task_id, {"completed": True, "priority": "high"})
    assert updated is True

    tasks = await repo.list_tasks(user_id=999, status="completed", limit=10)
    assert len(tasks) == 1
    assert tasks[0]["priority"] == "high"
    assert tasks[0]["completed"] is True

    deleted = await repo.delete_task(task_id)
    assert deleted is True

    tasks_after = await repo.list_tasks(user_id=999, status="all", limit=10)
    assert all(t["id"] != task_id for t in tasks_after)
