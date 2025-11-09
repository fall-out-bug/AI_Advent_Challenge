"""MCP tools for task reminders backed by MongoDB."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.di.factories import create_task_summary_use_case
from src.infrastructure.logging import get_logger
from src.infrastructure.repositories.task_repository import TaskRepository
from src.presentation.mcp.server import mcp

from ._summary_helpers import _build_summary_query, _compute_task_stats

logger = get_logger("mcp.reminder_tools")
_settings = get_settings()


async def _repo() -> TaskRepository:
    db = await get_db()
    return TaskRepository(db)


@mcp.tool()
async def add_task(
    user_id: int,
    title: str,
    description: str = "",
    deadline: str | None = None,
    priority: str = "medium",
    tags: list[str] | None = None,
) -> Dict[str, Any]:
    """Add a new task to the reminder system.

    Args:
        user_id: User ID (must be > 0)
        title: Task title (max 256 chars, required)
        description: Task description (max 2048 chars)
        deadline: ISO format deadline string
        priority: Priority level (high/medium/low)
        tags: List of tag strings (max 50 tags, each max 32 chars)

    Returns:
        Dict with task_id, created_at, status

    Exceptions:
        Returns error dict on validation failure
    """
    # Validation
    if not isinstance(user_id, int) or user_id <= 0:
        logger.warning("Invalid user_id", extra={"user_id": user_id})
        return {"status": "error", "error": "user_id must be a positive integer"}

    if not title or not isinstance(title, str):
        logger.warning(
            "Missing or invalid title", extra={"user_id": user_id}
        )
        return {"status": "error", "error": "title is required and must be a string"}

    if len(title) > 256:
        logger.warning(
            "Title too long",
            extra={"user_id": user_id, "length": len(title)},
        )
        title = title[:256]

    if description and len(description) > 2048:
        logger.warning(
            "Description too long",
            extra={"user_id": user_id, "length": len(description)},
        )
        description = description[:2048]

    if priority not in ("high", "medium", "low"):
        logger.warning(
            "Invalid priority",
            extra={"user_id": user_id, "priority": priority},
        )
        priority = "medium"

    if tags:
        if len(tags) > 50:
            tags = tags[:50]
            logger.warning(
                "Too many tags, truncating", extra={"user_id": user_id}
            )
        tags = [str(tag)[:32] for tag in tags if tag]

    try:
        from src.domain.entities.task import TaskIn

        repo = await _repo()
        task_in = TaskIn(
            user_id=user_id,
            title=title,
            description=description,
            deadline=deadline,
            priority=priority,
            tags=tags or [],
        )
        task_id = await repo.create_task(task_in)
        logger.info(
            "Task created", extra={"user_id": user_id, "task_id": task_id}
        )
        return {
            "task_id": task_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "created",
        }
    except Exception as e:
        logger.error(
            "Failed to create task",
            extra={"user_id": user_id, "error": str(e)},
        )
        return {"status": "error", "error": f"Failed to create task: {str(e)}"}


@mcp.tool()
async def list_tasks(
    user_id: int,
    status: str = "active",
    limit: int = 100,
) -> Dict[str, Any]:
    """List user tasks with filtering.

    Args:
        user_id: User ID (must be > 0)
        status: Filter status (all/active/completed, default: active)
        limit: Maximum tasks to return (max 500, default: 100)

    Returns:
        Dict with tasks list, total count, filtered count
    """
    # Validation
    if not isinstance(user_id, int) or user_id <= 0:
        logger.warning("Invalid user_id", extra={"user_id": user_id})
        return {
            "status": "error",
            "error": "user_id must be a positive integer",
            "tasks": [],
            "total": 0,
            "filtered": 0,
        }

    if status not in ("all", "active", "completed"):
        logger.warning(
            "Invalid status",
            extra={"user_id": user_id, "status": status},
        )
        status = "active"

    if not isinstance(limit, int) or limit < 1:
        limit = 100
    limit = min(limit, 500)

    try:
        repo = await _repo()
        tasks = await repo.list_tasks(user_id=user_id, status=status, limit=limit)
        total = len(await repo.list_tasks(user_id=user_id, status="all", limit=limit))
        logger.info(
            "Tasks listed",
            extra={"user_id": user_id, "status": status, "count": len(tasks)},
        )
        return {"tasks": tasks, "total": total, "filtered": len(tasks)}
    except Exception as e:
        logger.error(
            "Failed to list tasks",
            extra={"user_id": user_id, "error": str(e)},
        )
        return {
            "status": "error",
            "error": f"Failed to list tasks: {str(e)}",
            "tasks": [],
            "total": 0,
            "filtered": 0,
        }


@mcp.tool()
async def update_task(task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update task fields by ID.

    Args:
        task_id: Task ID string (required)
        updates: Dict of fields to update

    Returns:
        Dict with task_id, updated_fields, status
    """
    # Validation
    if not task_id or not isinstance(task_id, str):
        logger.warning("Invalid task_id", extra={"task_id": task_id})
        return {"status": "error", "error": "task_id is required and must be a string"}

    if not updates or not isinstance(updates, dict):
        logger.warning("Invalid updates", extra={"task_id": task_id})
        return {"status": "error", "error": "updates must be a non-empty dictionary"}

    # Validate update fields
    allowed_fields = {
        "title",
        "description",
        "deadline",
        "priority",
        "completed",
        "tags",
    }
    invalid_fields = set(updates.keys()) - allowed_fields
    if invalid_fields:
        logger.warning(
            "Invalid update fields",
            extra={"task_id": task_id, "fields": invalid_fields},
        )
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

    try:
        repo = await _repo()
        ok = await repo.update_task(task_id, updates)
        if ok:
            logger.info(
                "Task updated",
                extra={"task_id": task_id, "fields": list(updates.keys())},
            )
        else:
            logger.warning(
                "Task not found for update", extra={"task_id": task_id}
            )
        return {
            "task_id": task_id,
            "updated_fields": list(updates.keys()),
            "status": "updated" if ok else "not_found",
        }
    except Exception as e:
        logger.error(
            "Failed to update task",
            extra={"task_id": task_id, "error": str(e)},
        )
        return {"status": "error", "error": f"Failed to update task: {str(e)}"}


@mcp.tool()
async def delete_task(task_id: str) -> Dict[str, str]:
    """Delete a task by ID.

    Args:
        task_id: Task ID string (required)

    Returns:
        Dict with status and task_id
    """
    # Validation
    if not task_id or not isinstance(task_id, str):
        logger.warning("Invalid task_id", extra={"task_id": task_id})
        return {"status": "error", "error": "task_id is required and must be a string"}

    try:
        repo = await _repo()
        ok = await repo.delete_task(task_id)
        if ok:
            logger.info("Task deleted", extra={"task_id": task_id})
        else:
            logger.warning(
                "Task not found for deletion", extra={"task_id": task_id}
            )
        return {"status": "deleted" if ok else "not_found", "task_id": task_id}
    except Exception as e:
        logger.error(
            "Failed to delete task",
            extra={"task_id": task_id, "error": str(e)},
        )
        return {"status": "error", "error": f"Failed to delete task: {str(e)}"}


@mcp.tool()
async def get_summary(user_id: int, timeframe: str = "today") -> Dict[str, Any]:
    """Get a summary of tasks for a timeframe.

    Purpose:
        Fetch tasks for user within timeframe and compute statistics.
        Supports both old and new summarization implementations via feature flag.

    Args:
        user_id: Telegram user ID.
        timeframe: Timeframe for filtering (today/week/all/last_24h).

    Returns:
        Dictionary with tasks list and statistics.
    """
    # Check feature flag
    if _settings.use_new_summarization:
        try:
            logger.info(
                "Using new summarization system",
                extra={"user_id": user_id, "timeframe": timeframe},
            )
            use_case = create_task_summary_use_case()
            result = await use_case.execute(user_id=user_id, timeframe=timeframe)

            # Convert to expected format (backward compatibility)
            # Ensure tasks have 'id' field instead of '_id'
            tasks = []
            for task in result.tasks:
                task_dict = dict(task)
                if "_id" in task_dict:
                    task_dict["id"] = str(task_dict.pop("_id"))
                tasks.append(task_dict)

            return {
                "tasks": tasks,
                "stats": result.stats,
                "_metadata": {
                    "method": "new",
                    "generated_at": result.generated_at.isoformat(),
                },
            }
        except Exception as e:
            logger.error(
                "Error in new summarization, falling back to old",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            # Fall through to old implementation

    # Old implementation (fallback or feature flag disabled)
    logger.debug(
        "Using old summarization system",
        extra={"user_id": user_id, "timeframe": timeframe},
    )
    db = await get_db()
    now = datetime.now(timezone.utc)

    # Build query (may be empty for last_24h)
    query = _build_summary_query(user_id=user_id, timeframe=timeframe, now=now)

    # Fetch tasks
    if timeframe == "last_24h":
        tasks_raw = await db.tasks.find({"user_id": int(user_id)}).to_list(length=200)
        tasks = []
        for t in tasks_raw:
            if not t.get("completed", False):
                task_dict = dict(t)
                if "_id" in task_dict:
                    task_dict["id"] = str(task_dict.pop("_id"))
                tasks.append(task_dict)
    else:
        tasks = await db.tasks.find(query).to_list(length=200)

    # Convert _id to id for all tasks
    converted_tasks = []
    for t in tasks:
        task_copy = dict(t)
        if "_id" in task_copy:
            task_copy["id"] = str(task_copy.pop("_id"))
        converted_tasks.append(task_copy)
    tasks = converted_tasks

    # Compute stats using string-based comparison
    stats = _compute_task_stats(tasks, now_iso=now.isoformat())

    return {"tasks": tasks, "stats": stats}
