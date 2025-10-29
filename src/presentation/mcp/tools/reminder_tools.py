"""MCP tools for task reminders backed by MongoDB."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from typing import Any, Dict

from src.presentation.mcp.server import mcp
from src.infrastructure.database.mongo import get_db
from src.infrastructure.monitoring.logger import get_logger
from src.infrastructure.repositories.task_repository import TaskRepository

logger = get_logger(name="mcp.reminder_tools")


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
        logger.warning("Invalid user_id", user_id=user_id)
        return {"status": "error", "error": "user_id must be a positive integer"}

    if not title or not isinstance(title, str):
        logger.warning("Missing or invalid title", user_id=user_id)
        return {"status": "error", "error": "title is required and must be a string"}

    if len(title) > 256:
        logger.warning("Title too long", user_id=user_id, length=len(title))
        title = title[:256]

    if description and len(description) > 2048:
        logger.warning("Description too long", user_id=user_id, length=len(description))
        description = description[:2048]

    if priority not in ("high", "medium", "low"):
        logger.warning("Invalid priority", user_id=user_id, priority=priority)
        priority = "medium"

    if tags:
        if len(tags) > 50:
            tags = tags[:50]
            logger.warning("Too many tags, truncating", user_id=user_id)
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
        logger.info("Task created", user_id=user_id, task_id=task_id)
        return {"task_id": task_id, "created_at": datetime.utcnow().isoformat(), "status": "created"}
    except Exception as e:
        logger.error("Failed to create task", user_id=user_id, error=str(e))
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
        logger.warning("Invalid user_id", user_id=user_id)
        return {"status": "error", "error": "user_id must be a positive integer", "tasks": [], "total": 0, "filtered": 0}

    if status not in ("all", "active", "completed"):
        logger.warning("Invalid status", user_id=user_id, status=status)
        status = "active"

    if not isinstance(limit, int) or limit < 1:
        limit = 100
    limit = min(limit, 500)

    try:
        repo = await _repo()
        tasks = await repo.list_tasks(user_id=user_id, status=status, limit=limit)
        total = len(await repo.list_tasks(user_id=user_id, status="all", limit=limit))
        logger.info("Tasks listed", user_id=user_id, status=status, count=len(tasks))
        return {"tasks": tasks, "total": total, "filtered": len(tasks)}
    except Exception as e:
        logger.error("Failed to list tasks", user_id=user_id, error=str(e))
        return {"status": "error", "error": f"Failed to list tasks: {str(e)}", "tasks": [], "total": 0, "filtered": 0}


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
        logger.warning("Invalid task_id", task_id=task_id)
        return {"status": "error", "error": "task_id is required and must be a string"}

    if not updates or not isinstance(updates, dict):
        logger.warning("Invalid updates", task_id=task_id)
        return {"status": "error", "error": "updates must be a non-empty dictionary"}

    # Validate update fields
    allowed_fields = {"title", "description", "deadline", "priority", "completed", "tags"}
    invalid_fields = set(updates.keys()) - allowed_fields
    if invalid_fields:
        logger.warning("Invalid update fields", task_id=task_id, fields=invalid_fields)
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

    try:
        repo = await _repo()
        ok = await repo.update_task(task_id, updates)
        if ok:
            logger.info("Task updated", task_id=task_id, fields=list(updates.keys()))
        else:
            logger.warning("Task not found for update", task_id=task_id)
        return {"task_id": task_id, "updated_fields": list(updates.keys()), "status": "updated" if ok else "not_found"}
    except Exception as e:
        logger.error("Failed to update task", task_id=task_id, error=str(e))
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
        logger.warning("Invalid task_id", task_id=task_id)
        return {"status": "error", "error": "task_id is required and must be a string"}

    try:
        repo = await _repo()
        ok = await repo.delete_task(task_id)
        if ok:
            logger.info("Task deleted", task_id=task_id)
        else:
            logger.warning("Task not found for deletion", task_id=task_id)
        return {"status": "deleted" if ok else "not_found", "task_id": task_id}
    except Exception as e:
        logger.error("Failed to delete task", task_id=task_id, error=str(e))
        return {"status": "error", "error": f"Failed to delete task: {str(e)}"}


@mcp.tool()
async def get_summary(user_id: int, timeframe: str = "today") -> Dict[str, Any]:
    """Get a summary of tasks for a timeframe."""

    from src.infrastructure.database.mongo import get_db
    from src.infrastructure.monitoring.logger import get_logger
    logger = get_logger(name="reminder_tools")
    
    print(f"[get_summary] CALLED with user_id={user_id}, timeframe={repr(timeframe)}", file=sys.stderr, flush=True)
    logger.info("get_summary called", user_id=user_id, timeframe=timeframe)
    
    # Initialize tasks early
    tasks = []
    print(f"[get_summary] DEBUG: Initialized tasks = {tasks}", file=sys.stderr, flush=True)

    try:
        db = await get_db()
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Ensure user_id is int (MongoDB stores it as int)
        user_id_int = int(user_id) if not isinstance(user_id, int) else user_id
        query: Dict[str, Any] = {"user_id": user_id_int}
        print(f"[get_summary] DEBUG: Starting query construction for user_id={user_id_int}, timeframe={repr(timeframe)}", file=sys.stderr, flush=True)
        print(f"[get_summary] DEBUG: timeframe == 'last_24h': {timeframe == 'last_24h'}", file=sys.stderr, flush=True)
        logger.info("Starting query construction", user_id=user_id_int, timeframe=timeframe)

        if timeframe == "today":
            # Use UTC date for start/end
            start_dt = datetime(now.year, now.month, now.day, 0, 0, 0, 0, tzinfo=timezone.utc)
            end_dt = start_dt + timedelta(days=1)
            query["deadline"] = {"$gte": start_dt.isoformat(), "$lt": end_dt.isoformat()}
        elif timeframe == "tomorrow":
            tomorrow_start = datetime(now.year, now.month, now.day, 0, 0, 0, 0, tzinfo=timezone.utc) + timedelta(days=1)
            end_dt = tomorrow_start + timedelta(days=1)
            query["deadline"] = {"$gte": tomorrow_start.isoformat(), "$lt": end_dt.isoformat()}
        elif timeframe == "week":
            start_dt = datetime(now.year, now.month, now.day, 0, 0, 0, 0, tzinfo=timezone.utc)
            end_dt = start_dt + timedelta(days=7)
            query["deadline"] = {"$gte": start_dt.isoformat(), "$lt": end_dt.isoformat()}
        elif timeframe == "last_24h":
            # For debug mode: show ALL active tasks (not completed) regardless of deadline
            # This will be handled separately below, skip query construction here
            pass
        elif timeframe == "last_7d":
            start = (now - timedelta(days=7)).isoformat()
            end = now.isoformat()
            query["deadline"] = {"$gte": start, "$lt": end}
        else:
            # No timeframe filter, show all tasks
            pass

        # For last_24h, fetch all tasks and filter in Python to avoid MongoDB query issues
        if timeframe == "last_24h":
            logger.info("Fetching all tasks for last_24h debug mode", user_id=user_id_int)
            try:
                # Direct query - no intermediate variables
                tasks_raw = await db.tasks.find({"user_id": user_id_int}).to_list(length=200)
                logger.info("Found all tasks", user_id=user_id_int, total=len(tasks_raw))
                
                # Filter and convert in one step
                tasks = []
                for t in tasks_raw:
                    if not t.get("completed", False):
                        # Convert _id to id immediately
                        task_dict = dict(t)
                        if "_id" in task_dict:
                            task_dict["id"] = str(task_dict.pop("_id"))
                        tasks.append(task_dict)
                
                logger.info("Filtered active tasks", user_id=user_id_int, active=len(tasks))
                
                # Return immediately with tasks
                return {
                    "tasks": tasks,
                    "stats": {
                        "total": len(tasks),
                        "completed": 0,
                        "overdue": 0,  # Skip overdue calculation for now
                        "high_priority": sum(1 for t in tasks if t.get("priority") == "high"),
                    },
                }
            except Exception as e:
                logger.error("Error fetching tasks for last_24h", user_id=user_id_int, error=str(e), exc_info=True)
                import traceback
                traceback.print_exc()
                tasks = []
        else:
            logger.info("Executing get_summary query", user_id=user_id_int, timeframe=timeframe, query=str(query))
            tasks = await db.tasks.find(query).to_list(length=200)
            logger.info("Found tasks", user_id=user_id_int, count=len(tasks))
        
        logger.info("After branch, tasks count", user_id=user_id_int, count=len(tasks))
        print(f"[get_summary] DEBUG: After branch, tasks count = {len(tasks)}, tasks type = {type(tasks)}", file=sys.stderr, flush=True)
        
        # CRITICAL: Save tasks count before any processing
        tasks_count_before_processing = len(tasks)
        print(f"[get_summary] DEBUG: Tasks count before processing = {tasks_count_before_processing}", file=sys.stderr, flush=True)
        
        total = len(tasks)
        print(f"[get_summary] DEBUG: Total = {total}", file=sys.stderr, flush=True)
        completed = sum(1 for t in tasks if t.get("completed"))
        print(f"[get_summary] DEBUG: Completed = {completed}", file=sys.stderr, flush=True)
        
        # Check overdue tasks - simplified to avoid timezone comparison issues
        # Just count tasks with deadline in the past (string comparison)
        overdue = 0
        try:
            now_iso_str = now.isoformat()
            print(f"[get_summary] DEBUG: Checking overdue, tasks count = {len(tasks)}", file=sys.stderr, flush=True)
            for t in tasks:
                deadline_str = t.get("deadline")
                if deadline_str and isinstance(deadline_str, str):
                    deadline_normalized = deadline_str.replace("Z", "+00:00")
                    if deadline_normalized < now_iso_str:
                        overdue += 1
        except Exception as overdue_err:
            print(f"[get_summary] DEBUG: Error in overdue check: {overdue_err}", file=sys.stderr, flush=True)
            import traceback
            print(f"[get_summary] DEBUG: Overdue traceback:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
            overdue = 0  # Skip overdue check if any error
        
        print(f"[get_summary] DEBUG: After overdue check, tasks count = {len(tasks)}", file=sys.stderr, flush=True)
        high_priority = sum(1 for t in tasks if t.get("priority") == "high")
        print(f"[get_summary] DEBUG: High priority = {high_priority}", file=sys.stderr, flush=True)

        # Convert _id to id for all tasks - create new list to avoid issues
        print(f"[get_summary] DEBUG: Before conversion, tasks count = {len(tasks)}", file=sys.stderr, flush=True)
        converted_tasks = []
        try:
            for t in tasks:
                task_copy = dict(t)  # Make a copy to avoid mutating original
                if "_id" in task_copy:
                    from bson import ObjectId  # local import to avoid global dependency in tests
                    task_copy["id"] = str(task_copy.pop("_id"))
                converted_tasks.append(task_copy)
            tasks = converted_tasks  # Replace with converted list
            print(f"[get_summary] DEBUG: After conversion, tasks count = {len(tasks)}", file=sys.stderr, flush=True)
        except Exception as conv_e:
            print(f"[get_summary] DEBUG: ERROR in conversion: {conv_e}", file=sys.stderr, flush=True)
            import traceback
            print(f"[get_summary] DEBUG: Conversion traceback:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
            # Use original tasks if conversion fails
            print(f"[get_summary] DEBUG: Using original tasks after conversion error", file=sys.stderr, flush=True)
        
        logger.info("Preparing return value", user_id=user_id_int, tasks_count=len(tasks), total_stats=total)
        print(f"[get_summary] DEBUG: Preparing return, tasks={len(tasks)}, total={total}", file=sys.stderr, flush=True)
        print(f"[get_summary] DEBUG: tasks is: {tasks}", file=sys.stderr, flush=True)
        print(f"[get_summary] DEBUG: tasks type: {type(tasks)}, len: {len(tasks) if hasattr(tasks, '__len__') else 'N/A'}", file=sys.stderr, flush=True)
        
        result = {
            "tasks": tasks.copy() if hasattr(tasks, 'copy') else list(tasks) if tasks else [],
            "stats": {
                "total": total,
                "completed": completed,
                "overdue": overdue,
                "high_priority": high_priority,
            },
        }
        print(f"[get_summary] DEBUG: Final result tasks count: {len(result['tasks'])}", file=sys.stderr, flush=True)
        print(f"[get_summary] DEBUG: Final result: {result}", file=sys.stderr, flush=True)
        return result
    except TypeError as e:
        print(f"[get_summary] DEBUG: TypeError caught: {e}", file=sys.stderr)
        if "can't compare offset-naive and offset-aware datetimes" in str(e):
            logger.error("Timezone comparison error in get_summary", user_id=user_id, timeframe=timeframe, error=str(e))
            # Return minimal valid result
            print(f"[get_summary] DEBUG: Returning empty result due to timezone error", file=sys.stderr)
            return {
                "tasks": [],
                "stats": {"total": 0, "completed": 0, "overdue": 0, "high_priority": 0},
            }
        print(f"[get_summary] DEBUG: TypeError not timezone-related, re-raising", file=sys.stderr)
        raise
    except Exception as e:
        print(f"[get_summary] DEBUG: Exception caught: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        print(f"[get_summary] DEBUG: Traceback:\n{traceback.format_exc()}", file=sys.stderr)
        logger.error("Error in get_summary", user_id=user_id, timeframe=timeframe, error=str(e), exc_info=True)
        raise


