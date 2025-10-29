"""Task management handlers."""

from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from src.presentation.mcp.client import get_mcp_client
from src.infrastructure.monitoring.logger import get_logger

logger = get_logger(name="butler_bot.tasks")

MAX_ITEMS_PER_PAGE = 10

router = Router()
_mcp = get_mcp_client()


def build_tasks_menu() -> InlineKeyboardBuilder:
    """Build tasks submenu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Task", callback_data="tasks:add")
    builder.button(text="📋 List Tasks", callback_data="tasks:list")
    builder.button(text="🔙 Back", callback_data="menu:main")
    builder.adjust(2, 1)
    return builder


def _get_priority_emoji(priority: str) -> str:
    """Get emoji for priority."""
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")


def _format_task_summary(task: dict) -> str:
    """Format a task for display in list."""
    emoji = _get_priority_emoji(task.get("priority", "medium"))
    status = "✅" if task.get("completed") else "⏳"
    title = task.get("title", "Untitled")[:40]
    return f"{status} {emoji} {title}"


@router.callback_query(F.data == "tasks:list")
async def callback_list_tasks(callback: CallbackQuery) -> None:
    """List user tasks."""
    user_id = callback.from_user.id
    try:
        tasks_res = await _mcp.call_tool("list_tasks", {"user_id": user_id, "status": "active", "limit": MAX_ITEMS_PER_PAGE})
        tasks = tasks_res.get("tasks", [])
        
        if not tasks:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 Back", callback_data="menu:tasks")
            await callback.message.edit_text("No active tasks.", reply_markup=keyboard.as_markup())
            await callback.answer()
            return

        builder = InlineKeyboardBuilder()
        for task in tasks:
            task_id = task.get("id", "")
            builder.button(text=_format_task_summary(task), callback_data=f"task:detail:{task_id}")
        builder.button(text="🔙 Back", callback_data="menu:tasks")
        builder.adjust(1)

        text = f"📋 Active Tasks ({len(tasks)}):"
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
    except Exception as e:
        logger.error("Failed to list tasks", user_id=user_id, error=str(e))
        await callback.answer("❌ Failed to load tasks. Please try again.", show_alert=True)


@router.callback_query(F.data.startswith("task:detail:"))
async def callback_task_detail(callback: CallbackQuery) -> None:
    """Show task details."""
    task_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    try:
        tasks_res = await _mcp.call_tool("list_tasks", {"user_id": user_id, "status": "all", "limit": 100})
        task = next((t for t in tasks_res.get("tasks", []) if t.get("id") == task_id), None)

        if not task:
            await callback.answer("Task not found", show_alert=True)
            return

        emoji = _get_priority_emoji(task.get("priority", "medium"))
        status = "✅ Completed" if task.get("completed") else "⏳ Active"
        text = f"{status}\n{emoji} *{task.get('title', 'Untitled')}*\n\n"
        if task.get("description"):
            text += f"📝 {task.get('description')}\n"
        if task.get("deadline"):
            text += f"📅 {task.get('deadline')}\n"
        text += f"🏷 Priority: {task.get('priority', 'medium')}"

        builder = InlineKeyboardBuilder()
        if not task.get("completed"):
            builder.button(text="✅ Complete", callback_data=f"task:complete:{task_id}")
        builder.button(text="🗑 Delete", callback_data=f"task:delete:{task_id}")
        builder.button(text="🔙 Back", callback_data="tasks:list")
        builder.adjust(1)

        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error("Failed to show task detail", user_id=user_id, task_id=task_id, error=str(e))
        await callback.answer("❌ Failed to load task. Please try again.", show_alert=True)


@router.callback_query(F.data.startswith("task:complete:"))
async def callback_task_complete(callback: CallbackQuery) -> None:
    """Mark task as completed."""
    task_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    
    try:
        result = await _mcp.call_tool("update_task", {"task_id": task_id, "updates": {"completed": True}})
        if result.get("status") == "updated":
            await callback.answer("Task completed ✅")
            await callback_task_detail(callback)
        else:
            await callback.answer("❌ Failed to complete task", show_alert=True)
    except Exception as e:
        logger.error("Failed to complete task", user_id=user_id, task_id=task_id, error=str(e))
        await callback.answer("❌ Failed to complete task", show_alert=True)


@router.callback_query(F.data.startswith("task:delete:"))
async def callback_task_delete(callback: CallbackQuery) -> None:
    """Delete a task."""
    task_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id
    
    try:
        result = await _mcp.call_tool("delete_task", {"task_id": task_id})
        if result.get("status") == "deleted":
            await callback.answer("Task deleted 🗑")
            await callback_list_tasks(callback)
        else:
            await callback.answer("❌ Failed to delete task", show_alert=True)
    except Exception as e:
        logger.error("Failed to delete task", user_id=user_id, task_id=task_id, error=str(e))
        await callback.answer("❌ Failed to delete task", show_alert=True)


@router.callback_query(F.data == "tasks:add")
async def callback_task_add(callback: CallbackQuery) -> None:
    """Prompt user to add task via natural language."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Back", callback_data="menu:tasks")
    await callback.message.edit_text(
        "Please send a task description in natural language.\nExample: 'Buy milk tomorrow at 5pm'",
        reply_markup=keyboard.as_markup(),
    )
    await callback.answer()

