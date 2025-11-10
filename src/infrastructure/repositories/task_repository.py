"""Task repository backed by MongoDB (Motor)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.entities.task import TaskIn


class TaskRepository:
    """Async repository for task documents.

    Purpose:
        Encapsulate CRUD operations and querying logic for tasks.

    Exceptions:
        ValueError: If provided IDs are invalid
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db

    async def create_task(self, task_in: TaskIn) -> str:
        """Insert a new task document and return its ID."""

        doc: Dict[str, Any] = {
            "user_id": task_in.user_id,
            "title": task_in.title[:256],
            "description": task_in.description or "",
            "deadline": task_in.deadline,
            "priority": task_in.priority,
            "tags": task_in.tags or [],
            "completed": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        result = await self._db.tasks.insert_one(doc)
        return str(result.inserted_id)

    async def list_tasks(
        self, user_id: int, status: str = "active", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List tasks filtered by status for a user."""

        query: Dict[str, Any] = {"user_id": user_id}
        if status == "active":
            query["completed"] = False
        elif status == "completed":
            query["completed"] = True

        limit = min(limit, 500)
        cursor = self._db.tasks.find(query).sort("created_at", -1).limit(limit)
        tasks = await cursor.to_list(length=limit)
        for t in tasks:
            t["id"] = str(t.pop("_id"))
        return tasks

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update given fields of a task. Returns True if modified."""

        allowed = {"title", "description", "deadline", "priority", "tags", "completed"}
        update_doc = {k: v for k, v in updates.items() if k in allowed}
        if not update_doc:
            return False
        update_doc["updated_at"] = datetime.utcnow().isoformat()

        oid = _to_object_id(task_id)
        result = await self._db.tasks.update_one({"_id": oid}, {"$set": update_doc})
        return result.modified_count > 0

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID. Returns True if deleted."""

        oid = _to_object_id(task_id)
        result = await self._db.tasks.delete_one({"_id": oid})
        return result.deleted_count > 0


def _to_object_id(task_id: str) -> ObjectId:
    try:
        return ObjectId(task_id)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("Invalid task_id") from exc
