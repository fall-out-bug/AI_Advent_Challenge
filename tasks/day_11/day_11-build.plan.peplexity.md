<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Day 11: Intelligent Butler Bot with MCP Integration - Technical Specification

## 🎯 Project Overview

**Objective**: Build a 24/7 personal butler Telegram bot with natural language task management, automated summaries, and Telegram channel digests, fully integrated with MCP infrastructure.

**Core Features**:

- Natural language task input with LLM-powered parsing
- Intelligent clarifying questions when task details are unclear
- Scheduled daily summaries and reminders
- Automated Telegram channel digests
- Manual task management via menu buttons
- Full MCP integration for extensibility

**Architecture**:

```
┌──────────────────────┐
│  Telegram Bot        │
│  (aiogram)           │
│  • Natural language  │
│  • Menu interface    │
│  • Notifications     │
└──────────┬───────────┘
           │ REST/RPC
           ▼
┌──────────────────────┐    ┌──────────────────────┐
│  MCP Server          │◄───│  Orchestrator        │
│  (Reminder Tools)    │    │  (Intent Parser)     │
│  • add_task          │    │  • NLP processing    │
│  • list_tasks        │    │  • Clarifications    │
│  • update_task       │    │  • Summary generation│
│  • delete_task       │    └──────────┬───────────┘
│  • get_summary       │               │
│  • digest_channels   │               ▼
└──────────┬───────────┘    ┌──────────────────────┐
           │                │  Mistral-7B LLM      │
           │                │  (Local)             │
           │                └──────────────────────┘
           ▼
┌──────────────────────┐
│  MongoDB             │
│  • tasks             │
│  • channels          │
│  • history           │
│  • stats             │
└──────────────────────┘
```


***

## 📦 Technical Stack

### Bot Layer

- **Framework**: aiogram 3.x (async, modern Telegram Bot API)
- **Language**: Python 3.10+
- **Deployment**: Docker container


### MCP Layer

- **Framework**: FastMCP (Python MCP SDK)
- **Transport**: REST API
- **Integration**: Reuse existing Day 10 orchestrator


### LLM Layer

- **Primary**: Mistral-7B-Instruct-v0.2 (local, 4-bit)
- **Fallback**: ChadGPT/Perplexity API (optional)
- **Purpose**: Intent parsing, clarifications, digest summarization


### Storage

- **Database**: MongoDB 6.0+
- **Collections**: tasks, channels, history, stats
- **Backup**: Daily automated backups


### Infrastructure

- Docker Compose orchestration
- All services in isolated containers
- Local network only (no external exposure)

***

## 📋 Component 1: Telegram Bot (aiogram)

### 1.1 Bot Core Implementation

**File**: `telegram_bot/src/bot/butler_bot.py`

```python
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import logging

# FSM States for conversation flow
class TaskCreation(StatesGroup):
    waiting_for_task = State()
    waiting_for_clarification = State()

class ButlerBot:
    """
    Main Telegram butler bot with natural language processing
    and MCP integration.
    """

    def __init__(self, token: str, mcp_client, orchestrator):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.router = Router()
        self.mcp_client = mcp_client
        self.orchestrator = orchestrator

        # Quiet hours configuration
        self.quiet_hours_start = 22  # 10 PM
        self.quiet_hours_end = 8     # 8 AM

        # Setup handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Register all command and message handlers."""

        # Commands
        self.router.message(Command("start"))(self.cmd_start)
        self.router.message(Command("menu"))(self.cmd_menu)
        self.router.message(Command("summary"))(self.cmd_summary)
        self.router.message(Command("help"))(self.cmd_help)

        # Main menu callbacks
        self.router.callback_query(F.data == "tasks")(self.menu_tasks)
        self.router.callback_query(F.data == "channels")(self.menu_channels)
        self.router.callback_query(F.data == "summary")(self.show_summary)
        self.router.callback_query(F.data == "digest")(self.show_digest)

        # Task management callbacks
        self.router.callback_query(F.data == "add_task")(self.add_task_start)
        self.router.callback_query(F.data == "list_tasks")(self.list_tasks)
        self.router.callback_query(F.data.startswith("task_"))(self.task_action)

        # Channel management callbacks
        self.router.callback_query(F.data == "add_channel")(self.add_channel)
        self.router.callback_query(F.data == "list_channels")(self.list_channels)
        self.router.callback_query(F.data.startswith("channel_"))(self.channel_action)

        # Natural language input (default handler)
        self.router.message(F.text)(self.handle_natural_language)

        self.dp.include_router(self.router)

    async def cmd_start(self, message: Message):
        """Handle /start command - show welcome and main menu."""
        welcome_text = (
            "🎩 Здравствуйте! Я ваш персональный дворецкий.\n\n"
            "Я помогу:\n"
            "• 📝 Управлять задачами на естественном языке\n"
            "• ⏰ Напоминать о важных делах\n"
            "• 📊 Показывать ежедневные сводки\n"
            "• 📰 Готовить дайджесты Telegram-каналов\n\n"
            "Просто напишите задачу, и я её запомню!\n"
            "Или воспользуйтесь меню ниже."
        )

        keyboard = self._build_main_menu()
        await message.answer(welcome_text, reply_markup=keyboard)

    async def cmd_menu(self, message: Message):
        """Show main menu."""
        keyboard = self._build_main_menu()
        await message.answer("📋 Главное меню:", reply_markup=keyboard)

    async def cmd_summary(self, message: Message):
        """Show task summary via command."""
        await self.show_summary_impl(message.from_user.id, message)

    async def cmd_help(self, message: Message):
        """Show help information."""
        help_text = (
            "🎩 *Как пользоваться дворецким*\n\n"
            "*Создание задач:*\n"
            "Просто напишите: _\"Напомни поздравить жену 17 июня\"_\n"
            "Я пойму дату, суть задачи и сохраню её.\n\n"
            "*Команды:*\n"
            "/menu - Показать главное меню\n"
            "/summary - Сводка дел на сегодня\n"
            "/help - Эта справка\n\n"
            "*Меню:*\n"
            "• 📝 Задачи - управление задачами\n"
            "• 📰 Каналы - подписки на дайджесты\n"
            "• 📊 Сводка - дела на сегодня\n"
            "• 📮 Дайджест - новости каналов\n"
        )
        await message.answer(help_text, parse_mode="Markdown")

    async def handle_natural_language(self, message: Message, state: FSMContext):
        """
        Process natural language input with LLM.

        Flow:
        1. Send to orchestrator for intent parsing
        2. If unclear - ask clarifying questions
        3. If clear - create task via MCP
        4. Confirm to user
        """
        user_id = message.from_user.id
        text = message.text

        # Show typing indicator
        await message.bot.send_chat_action(user_id, "typing")

        # Parse intent via orchestrator
        intent = await self.orchestrator.parse_task_intent(text)

        if intent.get("needs_clarification"):
            # Ask clarifying questions
            questions = intent.get("questions", [])
            question_text = "\n".join(f"• {q}" for q in questions)

            await message.answer(
                f"🤔 Уточните, пожалуйста:\n\n{question_text}"
            )
            await state.set_state(TaskCreation.waiting_for_clarification)
            await state.update_data(original_text=text, intent=intent)

        else:
            # Create task via MCP
            task_data = {
                "title": intent.get("title"),
                "description": intent.get("description", ""),
                "deadline": intent.get("deadline"),
                "priority": intent.get("priority", "medium"),
                "tags": intent.get("tags", []),
                "user_id": user_id
            }

            result = await self.mcp_client.call_tool("add_task", task_data)

            # Format confirmation with emoji
            emoji = self._get_priority_emoji(task_data["priority"])
            deadline_str = self._format_deadline(task_data["deadline"])

            confirmation = (
                f"{emoji} *Задача добавлена!*\n\n"
                f"📌 {task_data['title']}\n"
                f"📅 {deadline_str}\n"
            )

            if task_data.get("tags"):
                tags_str = " ".join(f"#{tag}" for tag in task_data["tags"])
                confirmation += f"🏷 {tags_str}\n"

            await message.answer(confirmation, parse_mode="Markdown")

    async def show_summary_impl(self, user_id: int, message_or_query):
        """Get and display daily task summary."""

        # Get summary from MCP
        summary_data = await self.mcp_client.call_tool("get_summary", {
            "user_id": user_id,
            "timeframe": "today"
        })

        tasks = summary_data.get("tasks", [])

        if not tasks:
            text = "📭 На сегодня задач нет. Отдыхайте!"
        else:
            text = "📊 *Задачи на сегодня:*\n\n"

            for task in tasks:
                emoji = self._get_priority_emoji(task["priority"])
                status_emoji = "✅" if task.get("completed") else "⏳"

                text += (
                    f"{status_emoji} {emoji} *{task['title']}*\n"
                    f"   ⏰ {self._format_deadline(task['deadline'])}\n\n"
                )

        if isinstance(message_or_query, Message):
            await message_or_query.answer(text, parse_mode="Markdown")
        else:
            await message_or_query.message.edit_text(text, parse_mode="Markdown")

    def _build_main_menu(self):
        """Build main menu keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.button(text="📝 Задачи")
        builder.button(text="📰 Каналы")
        builder.button(text="📊 Сводка")
        builder.button(text="📮 Дайджест")
        builder.adjust(2, 2)
        return builder.as_markup(resize_keyboard=True)

    def _get_priority_emoji(self, priority: str) -> str:
        """Get emoji for task priority."""
        return {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }.get(priority, "⚪")

    def _format_deadline(self, deadline: str) -> str:
        """Format deadline for display."""
        # Implementation: parse and format date
        return deadline  # Placeholder

    async def is_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours."""
        from datetime import datetime
        current_hour = datetime.now().hour

        if self.quiet_hours_start > self.quiet_hours_end:
            # Crosses midnight (e.g., 22:00-08:00)
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end
        else:
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end

    async def run(self):
        """Start the bot."""
        await self.dp.start_polling(self.bot)
```


### 1.2 Task Management Handlers

**File**: `telegram_bot/src/bot/handlers/tasks.py`

```python
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

async def menu_tasks(callback: CallbackQuery, mcp_client):
    """Show tasks submenu."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")],
        [InlineKeyboardButton(text="📋 Список задач", callback_data="list_tasks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

    await callback.message.edit_text(
        "📝 *Управление задачами*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def list_tasks(callback: CallbackQuery, mcp_client):
    """List all tasks with action buttons."""
    user_id = callback.from_user.id

    tasks = await mcp_client.call_tool("list_tasks", {"user_id": user_id})

    if not tasks.get("tasks"):
        await callback.answer("Нет активных задач")
        return

    # Build keyboard with task buttons
    keyboard_buttons = []
    for task in tasks["tasks"][:10]:  # Limit to 10 tasks
        emoji = "✅" if task.get("completed") else "⏳"
        button_text = f"{emoji} {task['title'][:30]}..."
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"task_{task['id']}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="tasks")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        "📋 *Ваши задачи:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def task_action(callback: CallbackQuery, mcp_client):
    """Handle task action (view/edit/delete/complete)."""
    task_id = callback.data.split("_")[1]

    # Get task details
    task = await mcp_client.call_tool("get_task", {"task_id": task_id})

    # Build task detail view
    emoji = "✅" if task.get("completed") else "⏳"
    text = (
        f"{emoji} *{task['title']}*\n\n"
        f"📝 {task.get('description', 'Нет описания')}\n"
        f"📅 {task.get('deadline', 'Без срока')}\n"
        f"🏷 Приоритет: {task.get('priority', 'средний')}\n"
    )

    # Action buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выполнить", callback_data=f"complete_{task_id}"),
            InlineKeyboardButton(text="⏸ Отложить", callback_data=f"postpone_{task_id}")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"detail_{task_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{task_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 К списку", callback_data="list_tasks")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
```


***

## 📋 Component 2: MCP Reminder Server

### 2.1 Core Reminder Tools

**File**: `mcp_server/src/tools/reminder_tools.py`

```python
from mcp.server.fastmcp import FastMCP, Context
from datetime import datetime, timedelta
from typing import Any
import logging

mcp = FastMCP(
    "Butler Reminder Server",
    instructions="24/7 personal assistant with task management and digest features"
)

@mcp.tool()
async def add_task(
    user_id: int,
    title: str,
    description: str = "",
    deadline: str | None = None,
    priority: str = "medium",
    tags: list[str] = None,
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Add a new task to the reminder system.

    Args:
        user_id: Telegram user ID
        title: Task title (max 256 chars)
        description: Detailed description
        deadline: ISO format datetime or null
        priority: low, medium, high
        tags: List of tags for categorization
        ctx: MCP context

    Returns:
        {
            "task_id": str,
            "created_at": str,
            "status": "created"
        }
    """
    from database import db

    task_doc = {
        "user_id": user_id,
        "title": title[:256],
        "description": description,
        "deadline": deadline,
        "priority": priority,
        "tags": tags or [],
        "completed": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    result = await db.tasks.insert_one(task_doc)

    # Log action
    await db.history.insert_one({
        "user_id": user_id,
        "action": "task_created",
        "task_id": str(result.inserted_id),
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "task_id": str(result.inserted_id),
        "created_at": task_doc["created_at"],
        "status": "created"
    }

@mcp.tool()
async def list_tasks(
    user_id: int,
    status: str = "active",
    limit: int = 100,
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    List user tasks with filtering.

    Args:
        user_id: Telegram user ID
        status: active, completed, all
        limit: Max tasks to return (default 100, max 500)
        ctx: MCP context

    Returns:
        {
            "tasks": list[dict],
            "total": int,
            "filtered": int
        }
    """
    from database import db

    query = {"user_id": user_id}

    if status == "active":
        query["completed"] = False
    elif status == "completed":
        query["completed"] = True

    limit = min(limit, 500)  # Enforce max limit

    cursor = db.tasks.find(query).sort("created_at", -1).limit(limit)
    tasks = await cursor.to_list(length=limit)

    # Convert ObjectId to string
    for task in tasks:
        task["id"] = str(task.pop("_id"))

    total = await db.tasks.count_documents({"user_id": user_id})

    return {
        "tasks": tasks,
        "total": total,
        "filtered": len(tasks)
    }

@mcp.tool()
async def update_task(
    task_id: str,
    updates: dict[str, Any],
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Update task fields.

    Args:
        task_id: Task ID to update
        updates: Fields to update (title, description, deadline, priority, tags)
        ctx: MCP context

    Returns:
        {
            "task_id": str,
            "updated_fields": list[str],
            "status": "updated"
        }
    """
    from database import db
    from bson import ObjectId

    allowed_fields = ["title", "description", "deadline", "priority", "tags", "completed"]
    update_doc = {k: v for k, v in updates.items() if k in allowed_fields}
    update_doc["updated_at"] = datetime.utcnow().isoformat()

    result = await db.tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": update_doc}
    )

    if result.modified_count == 0:
        return {"status": "not_found", "task_id": task_id}

    # Log action
    await db.history.insert_one({
        "action": "task_updated",
        "task_id": task_id,
        "updates": list(update_doc.keys()),
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "task_id": task_id,
        "updated_fields": list(update_doc.keys()),
        "status": "updated"
    }

@mcp.tool()
async def delete_task(
    task_id: str,
    ctx: Context | None = None
) -> dict[str, str]:
    """
    Delete a task.

    Args:
        task_id: Task ID to delete
        ctx: MCP context

    Returns:
        {"status": "deleted", "task_id": str}
    """
    from database import db
    from bson import ObjectId

    result = await db.tasks.delete_one({"_id": ObjectId(task_id)})

    if result.deleted_count == 0:
        return {"status": "not_found", "task_id": task_id}

    # Log deletion
    await db.history.insert_one({
        "action": "task_deleted",
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {"status": "deleted", "task_id": task_id}

@mcp.tool()
async def get_summary(
    user_id: int,
    timeframe: str = "today",
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Get task summary for specified timeframe.

    Args:
        user_id: Telegram user ID
        timeframe: today, tomorrow, week, all
        ctx: MCP context

    Returns:
        {
            "tasks": list[dict],
            "stats": {
                "total": int,
                "completed": int,
                "overdue": int,
                "high_priority": int
            }
        }
    """
    from database import db

    # Calculate date range
    now = datetime.utcnow()

    if timeframe == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif timeframe == "tomorrow":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = start + timedelta(days=1)
    elif timeframe == "week":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    else:
        # All active tasks
        start = None
        end = None

    query = {"user_id": user_id, "completed": False}

    if start and end:
        query["deadline"] = {"$gte": start.isoformat(), "$lt": end.isoformat()}

    tasks = await db.tasks.find(query).to_list(length=100)

    # Calculate stats
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed"))
    overdue = sum(1 for t in tasks if t.get("deadline") and datetime.fromisoformat(t["deadline"]) < now)
    high_priority = sum(1 for t in tasks if t.get("priority") == "high")

    # Format tasks
    for task in tasks:
        task["id"] = str(task.pop("_id"))

    return {
        "tasks": tasks,
        "stats": {
            "total": total,
            "completed": completed,
            "overdue": overdue,
            "high_priority": high_priority
        }
    }
```


### 2.2 Channel Digest Tools

**File**: `mcp_server/src/tools/digest_tools.py`

```python
@mcp.tool()
async def add_channel(
    user_id: int,
    channel_username: str,
    tags: list[str] = None,
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Subscribe to Telegram channel for digest.

    Args:
        user_id: Telegram user ID
        channel_username: Channel username (without @)
        tags: Optional annotation tags
        ctx: MCP context

    Returns:
        {
            "channel_id": str,
            "status": "subscribed"
        }
    """
    from database import db

    # Check if already subscribed
    existing = await db.channels.find_one({
        "user_id": user_id,
        "channel_username": channel_username
    })

    if existing:
        return {
            "channel_id": str(existing["_id"]),
            "status": "already_subscribed"
        }

    channel_doc = {
        "user_id": user_id,
        "channel_username": channel_username,
        "tags": tags or [],
        "subscribed_at": datetime.utcnow().isoformat(),
        "last_digest": None,
        "active": True
    }

    result = await db.channels.insert_one(channel_doc)

    return {
        "channel_id": str(result.inserted_id),
        "status": "subscribed"
    }

@mcp.tool()
async def get_channel_digest(
    user_id: int,
    hours: int = 24,
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Generate digest from subscribed channels.

    Args:
        user_id: Telegram user ID
        hours: Hours to look back (default 24)
        ctx: MCP context

    Returns:
        {
            "digests": [
                {
                    "channel": str,
                    "summary": str,  # 2-3 sentences
                    "post_count": int,
                    "tags": list[str]
                }
            ],
            "generated_at": str
        }
    """
    from database import db
    from telegram_utils import fetch_channel_posts
    from llm_client import summarize_posts

    # Get user's subscribed channels
    channels = await db.channels.find({
        "user_id": user_id,
        "active": True
    }).to_list(length=100)  # Max 100 channels

    digests = []
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    for channel in channels:
        # Fetch recent posts
        posts = await fetch_channel_posts(
            channel["channel_username"],
            since=cutoff_time
        )

        if not posts:
            continue

        # Generate summary using LLM
        summary = await summarize_posts(posts, max_sentences=3)

        digests.append({
            "channel": channel["channel_username"],
            "summary": summary,
            "post_count": len(posts),
            "tags": channel.get("tags", [])
        })

        # Update last digest time
        await db.channels.update_one(
            {"_id": channel["_id"]},
            {"$set": {"last_digest": datetime.utcnow().isoformat()}}
        )

    return {
        "digests": digests,
        "generated_at": datetime.utcnow().isoformat()
    }
```


***

## 📋 Component 3: Background Workers

### 3.1 Scheduled Summary Worker

**File**: `workers/summary_worker.py`

```python
import asyncio
from datetime import datetime, time
from telegram_bot.src.bot.butler_bot import ButlerBot

class SummaryWorker:
    """
    Background worker for scheduled summaries and reminders.
    Runs 24/7 and sends notifications at configured times.
    """

    def __init__(self, bot: ButlerBot, mcp_client, config: dict):
        self.bot = bot
        self.mcp_client = mcp_client
        self.config = config

        # Schedule times
        self.morning_summary_time = time(9, 0)  # 9:00 AM
        self.digest_time = time(20, 0)  # 8:00 PM

    async def run(self):
        """Main worker loop."""
        while True:
            try:
                await self.check_and_send_summaries()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Summary worker error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error

    async def check_and_send_summaries(self):
        """Check if it's time to send scheduled notifications."""
        now = datetime.now()
        current_time = now.time()

        # Morning summary
        if self._is_time_to_send(current_time, self.morning_summary_time):
            if not await self.bot.is_quiet_hours():
                await self.send_morning_summary()

        # Evening digest
        if self._is_time_to_send(current_time, self.digest_time):
            if not await self.bot.is_quiet_hours():
                await self.send_evening_digest()

    def _is_time_to_send(self, current: time, target: time) -> bool:
        """Check if current time matches target (within 1 minute)."""
        return (
            current.hour == target.hour and
            abs(current.minute - target.minute) <= 1
        )

    async def send_morning_summary(self):
        """Send morning task summary to all users."""
        from database import db

        # Get all active users
        users = await db.tasks.distinct("user_id")

        for user_id in users:
            try:
                # Get summary
                summary = await self.mcp_client.call_tool("get_summary", {
                    "user_id": user_id,
                    "timeframe": "today"
                })

                tasks = summary.get("tasks", [])
                stats = summary.get("stats", {})

                if not tasks:
                    text = "🌅 Доброе утро! На сегодня задач нет."
                else:
                    text = (
                        f"🌅 *Доброе утро!*\n\n"
                        f"📊 Задач на сегодня: {stats['total']}\n"
                        f"🔴 Приоритетных: {stats['high_priority']}\n\n"
                        f"*Ваши задачи:*\n\n"
                    )

                    for task in tasks[:5]:  # Top 5
                        emoji = self.bot._get_priority_emoji(task["priority"])
                        text += f"{emoji} {task['title']}\n"

                    if len(tasks) > 5:
                        text += f"\n_...и ещё {len(tasks) - 5}_"

                await self.bot.bot.send_message(
                    user_id,
                    text,
                    parse_mode="Markdown"
                )

            except Exception as e:
                logging.error(f"Error sending summary to {user_id}: {e}")

    async def send_evening_digest(self):
        """Send evening channel digest to all users."""
        from database import db

        # Get users with channel subscriptions
        channel_docs = await db.channels.find({"active": True}).to_list(length=None)
        user_ids = set(doc["user_id"] for doc in channel_docs)

        for user_id in user_ids:
            try:
                # Get digest
                digest_data = await self.mcp_client.call_tool(
                    "get_channel_digest",
                    {"user_id": user_id, "hours": 24}
                )

                digests = digest_data.get("digests", [])

                if not digests:
                    continue

                text = "📰 *Дайджест каналов за сегодня:*\n\n"

                for digest in digests:
                    channel_name = digest["channel"]
                    summary = digest["summary"]
                    post_count = digest["post_count"]

                    text += (
                        f"📌 *{channel_name}* ({post_count} постов)\n"
                        f"{summary}\n\n"
                    )

                await self.bot.bot.send_message(
                    user_id,
                    text,
                    parse_mode="Markdown"
                )

            except Exception as e:
                logging.error(f"Error sending digest to {user_id}: {e}")
```


***

## 📋 Component 4: Docker Configuration

### 4.1 Docker Compose

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: butler-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init:/docker-entrypoint-initdb.d
    environment:
      MONGO_INITDB_DATABASE: butler
    restart: unless-stopped
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/butler --quiet
      interval: 30s
      timeout: 10s
      retries: 3

  mcp-server:
    build:
      context: ./mcp_server
      dockerfile: Dockerfile
    container_name: butler-mcp-server
    ports:
      - "8005:8005"
    depends_on:
      - mongodb
    environment:
      - MONGODB_URL=mongodb://mongodb:27017/butler
      - MCP_PORT=8005
    volumes:
      - ./mcp_server/logs:/app/logs
    restart: unless-stopped

  telegram-bot:
    build:
      context: ./telegram_bot
      dockerfile: Dockerfile
    container_name: butler-telegram-bot
    depends_on:
      - mcp-server
      - mongodb
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - MCP_SERVER_URL=http://mcp-server:8005
      - MONGODB_URL=mongodb://mongodb:27017/butler
    volumes:
      - ./telegram_bot/logs:/app/logs
    restart: unless-stopped

  summary-worker:
    build:
      context: ./workers
      dockerfile: Dockerfile
    container_name: butler-summary-worker
    depends_on:
      - mcp-server
      - mongodb
      - telegram-bot
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - MCP_SERVER_URL=http://mcp-server:8005
      - MONGODB_URL=mongodb://mongodb:27017/butler
    restart: unless-stopped

volumes:
  mongodb_data:
```


### 4.2 Configuration File

**File**: `config/butler_config.yaml`

```yaml
bot:
  quiet_hours:
    start: 22  # 10 PM
    end: 8     # 8 AM

  limits:
    max_tasks: 500
    max_channels: 100
    max_history: 10000
    max_message_length: 4096

schedule:
  morning_summary: "09:00"
  evening_digest: "20:00"
  check_interval: 60  # seconds

llm:
  model: "mistral-7b-instruct-v0.2"
  temperature: 0.2
  max_tokens: 512
  fallback_providers:
    - "chadgpt"
    - "perplexity"

database:
  name: "butler"
  collections:
    - tasks
    - channels
    - history
    - stats

mcp:
  server_url: "http://localhost:8005"
  timeout: 30
  retry_attempts: 3
```


***

## 📋 Implementation Timeline

### Phase 1: Core Infrastructure (Day 1 - 8 hours)

- [ ] Setup MongoDB schemas
- [ ] MCP reminder tools (add, list, update, delete)
- [ ] Basic bot structure with aiogram
- [ ] Docker configuration


### Phase 2: NLP Integration (Day 2 - 6 hours)

- [ ] Orchestrator integration for intent parsing
- [ ] Clarifying questions logic
- [ ] Natural language task creation


### Phase 3: Bot Interface (Day 3 - 6 hours)

- [ ] Menu system implementation
- [ ] Task management UI
- [ ] Channel subscription UI


### Phase 4: Summaries \& Digests (Day 4 - 8 hours)

- [ ] Summary generation
- [ ] Channel digest tools
- [ ] Background worker implementation
- [ ] Scheduled notifications


### Phase 5: Testing \& Polish (Day 5 - 4 hours)

- [ ] End-to-end testing
- [ ] Error handling
- [ ] Documentation
- [ ] Deployment

**Total**: ~32 hours (4-5 working days)

***

## ✅ Success Criteria

- [ ] Bot responds to natural language task input
- [ ] Clarifying questions work correctly
- [ ] Tasks stored in MongoDB with full CRUD
- [ ] Manual task management via menu
- [ ] Daily summaries sent at 9 AM
- [ ] Channel digests sent at 8 PM
- [ ] Quiet hours respected (22:00-08:00)
- [ ] All services run 24/7 in Docker
- [ ] MCP tools accessible externally
- [ ] Emoji-rich, user-friendly interface

***

**Status**: Ready for implementation with Cursor AI assistance
