# Примеры кода для Cursor

Практические примеры ключевых модулей для быстрого старта.

---

## 1. agent/config.py

```python
"""Configuration management for Agent."""

from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MongoDBConfig:
    """MongoDB configuration."""

    uri: str = os.getenv(
        "MONGODB_URI",
        "mongodb://root:rootpassword@mongodb:27017/agent_db?authSource=admin"
    )
    database: str = "agent_db"
    collections: dict = None

    def __post_init__(self):
        self.collections = {
            "dialogs": "dialogs",
            "posts": "posts",
            "channels": "channels",
            "collection_jobs": "collection_jobs",
        }


@dataclass
class RedisConfig:
    """Redis configuration."""

    url: str = os.getenv(
        "REDIS_URL",
        "redis://:redispassword@redis:6379/0"
    )
    db: int = 0
    key_prefix: str = "agent:"
    ttl_seconds: int = 86400  # 24 hours


@dataclass
class MistralConfig:
    """Mistral model configuration."""

    model_name: str = os.getenv("MISTRAL_MODEL", "mistral-7b-instruct-v0.2")
    device: str = os.getenv("DEVICE", "cuda")
    max_tokens: int = int(os.getenv("MAX_TOKENS", "2048"))
    context_window: int = int(os.getenv("CONTEXT_WINDOW", "4096"))
    temperature: float = 0.7
    top_p: float = 0.9


@dataclass
class MCPToolsConfig:
    """MCP Tools server configuration."""

    base_url: str = os.getenv("MCP_TOOLS_URL", "http://mcp_tools:8001")
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_backoff_factor: float = 2.0


@dataclass
class DialogConfig:
    """Dialog management configuration."""

    history_limit_tokens: int = int(
        os.getenv("DIALOG_HISTORY_LIMIT_TOKENS", "8000")
    )
    summarize_trigger_ratio: float = 0.9  # 90% of limit
    max_history_items: int = 100


@dataclass
class Config:
    """Main configuration."""

    mongo: MongoDBConfig = None
    redis: RedisConfig = None
    mistral: MistralConfig = None
    mcp_tools: MCPToolsConfig = None
    dialog: DialogConfig = None
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        self.mongo = MongoDBConfig()
        self.redis = RedisConfig()
        self.mistral = MistralConfig()
        self.mcp_tools = MCPToolsConfig()
        self.dialog = DialogConfig()


# Singleton instance
config = Config()
```

---

## 2. agent/mcp_client.py

```python
"""HTTP client for MCP Tools server."""

import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Base exception for MCP client."""

    pass


class MCPToolNotFoundError(MCPClientError):
    """Tool not found error."""

    pass


class MCPTimeoutError(MCPClientError):
    """Tool timeout error."""

    pass


class MCPClient:
    """Async HTTP client for MCP Tools."""

    def __init__(self, base_url: str, timeout: int = 30, retries: int = 3):
        """Initialize MCP client.

        Args:
            base_url: Base URL of MCP Tools server (e.g., http://mcp_tools:8001)
            timeout: Request timeout in seconds
            retries: Number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.close()

    async def close(self):
        """Close session."""
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}{endpoint}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            async with self.session.request(
                method,
                url,
                timeout=timeout,
                **kwargs
            ) as resp:
                data = await resp.json()

                if resp.status >= 400:
                    error_msg = data.get("error", f"HTTP {resp.status}")
                    if resp.status == 404:
                        raise MCPToolNotFoundError(error_msg)
                    elif resp.status == 504:
                        raise MCPTimeoutError(error_msg)
                    else:
                        raise MCPClientError(error_msg)

                return data

        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"Request to {endpoint} timed out after {self.timeout}s")

    async def get_subscriptions(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get list of subscribed channels.

        Args:
            user_id: Optional user ID

        Returns:
            Dict with channels list
        """
        logger.info("Fetching subscriptions", extra={"user_id": user_id})
        payload = {}
        if user_id:
            payload["user_id"] = user_id

        return await self._request("POST", "/tools/get_subscriptions", json=payload)

    async def get_posts(
        self,
        channel_id: str,
        limit: int = 100,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get posts from channel.

        Args:
            channel_id: Channel ID
            limit: Max posts to retrieve
            date_from: Start date (optional)
            date_to: End date (optional)

        Returns:
            Dict with posts list
        """
        logger.info(
            "Fetching posts",
            extra={"channel_id": channel_id, "limit": limit}
        )

        payload = {
            "channel_id": channel_id,
            "limit": limit,
        }
        if date_from:
            payload["date_from"] = date_from.isoformat()
        if date_to:
            payload["date_to"] = date_to.isoformat()

        return await self._request("POST", "/tools/get_posts", json=payload)

    async def collect_posts(
        self,
        channel_id: str,
        wait_for_completion: bool = True,
        timeout_seconds: int = 30,
    ) -> Dict[str, Any]:
        """Trigger post collection for channel.

        Args:
            channel_id: Channel ID
            wait_for_completion: Wait for collection to finish
            timeout_seconds: Max wait time

        Returns:
            Dict with job status
        """
        logger.info(
            "Collecting posts",
            extra={"channel_id": channel_id, "wait": wait_for_completion}
        )

        payload = {
            "channel_id": channel_id,
            "wait_for_completion": wait_for_completion,
            "timeout_seconds": timeout_seconds,
        }

        return await self._request("POST", "/tools/collect_posts", json=payload)

    async def generate_summary(
        self,
        posts_text: str,
        posts_count: int,
        channel_name: str,
        language: str = "ru",
        style: str = "bullet_points",
    ) -> Dict[str, Any]:
        """Generate summary from posts.

        Args:
            posts_text: Combined posts text
            posts_count: Number of posts
            channel_name: Channel name
            language: Language code
            style: Summary style (bullet_points or paragraph)

        Returns:
            Dict with summary
        """
        logger.info(
            "Generating summary",
            extra={"posts_count": posts_count, "channel": channel_name}
        )

        payload = {
            "posts_text": posts_text,
            "posts_count": posts_count,
            "channel_name": channel_name,
            "language": language,
            "style": style,
        }

        return await self._request("POST", "/tools/generate_summary", json=payload)

    async def export_pdf(
        self,
        summary_text: str,
        title: str,
        channel_name: str,
        date_range: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Export summary to PDF.

        Args:
            summary_text: Summary text
            title: PDF title
            channel_name: Channel name
            date_range: Dict with "from" and "to" dates
            metadata: Optional metadata

        Returns:
            Dict with PDF path
        """
        logger.info(
            "Exporting to PDF",
            extra={"title": title, "channel": channel_name}
        )

        payload = {
            "summary_text": summary_text,
            "title": title,
            "channel_name": channel_name,
            "date_range": date_range,
            "metadata": metadata or {},
        }

        return await self._request("POST", "/tools/export_pdf", json=payload)
```

---

## 3. agent/dialog_manager.py

```python
"""Dialog history management in MongoDB."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import config

logger = logging.getLogger(__name__)


class DialogManager:
    """Manages dialog history in MongoDB."""

    def __init__(self, mongo_uri: str, database: str):
        """Initialize dialog manager.

        Args:
            mongo_uri: MongoDB connection URI
            database: Database name
        """
        self.mongo_uri = mongo_uri
        self.database_name = database
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(self.mongo_uri)
        self.db = self.client[self.database_name]
        logger.info("Connected to MongoDB", extra={"database": self.database_name})

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

    async def create_session(self, user_id: str) -> str:
        """Create new dialog session.

        Args:
            user_id: User ID

        Returns:
            Session ID
        """
        session_id = str(uuid4())
        await self.db.dialogs.insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "token_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        logger.info("Created session", extra={"session_id": session_id, "user_id": user_id})
        return session_id

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens: int = 0,
    ):
        """Add message to dialog history.

        Args:
            session_id: Session ID
            role: Message role (user/assistant)
            content: Message content
            tokens: Token count
        """
        message = {
            "role": role,
            "content": content,
            "tokens": tokens,
            "timestamp": datetime.utcnow(),
        }

        await self.db.dialogs.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$inc": {"token_count": tokens},
                "$set": {"updated_at": datetime.utcnow()},
            }
        )
        logger.debug(f"Added {role} message", extra={"session_id": session_id, "tokens": tokens})

    async def get_dialog_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get dialog history.

        Args:
            session_id: Session ID
            limit: Max messages to return

        Returns:
            List of messages
        """
        dialog = await self.db.dialogs.find_one({"session_id": session_id})

        if not dialog:
            return []

        messages = dialog.get("messages", [])
        if limit:
            messages = messages[-limit:]

        return messages

    async def get_dialog_text(self, session_id: str) -> str:
        """Get full dialog as text.

        Args:
            session_id: Session ID

        Returns:
            Formatted dialog text
        """
        messages = await self.get_dialog_history(session_id)
        text_parts = []

        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            text_parts.append(f"{role}:\n{content}\n")

        return "\n".join(text_parts)

    async def get_token_count(self, session_id: str) -> int:
        """Get current token count in session.

        Args:
            session_id: Session ID

        Returns:
            Token count
        """
        dialog = await self.db.dialogs.find_one(
            {"session_id": session_id},
            {"token_count": 1}
        )
        return dialog.get("token_count", 0) if dialog else 0

    async def should_summarize(self, session_id: str) -> bool:
        """Check if dialog history should be summarized.

        Args:
            session_id: Session ID

        Returns:
            True if should summarize
        """
        token_count = await self.get_token_count(session_id)
        limit = config.dialog.history_limit_tokens
        threshold = limit * config.dialog.summarize_trigger_ratio

        should = token_count > threshold
        if should:
            logger.warning(
                "Dialog history exceeds summarization threshold",
                extra={"session_id": session_id, "tokens": token_count, "threshold": threshold}
            )

        return should

    async def compress_history(
        self,
        session_id: str,
        summary: str,
    ):
        """Replace old history with summary.

        Args:
            session_id: Session ID
            summary: Summary text
        """
        await self.db.dialogs.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "messages": [{
                        "role": "system",
                        "content": f"[SUMMARY OF PREVIOUS CONVERSATION]\n{summary}",
                        "tokens": 0,
                        "timestamp": datetime.utcnow(),
                    }],
                    "token_count": 0,
                    "compressed_at": datetime.utcnow(),
                }
            }
        )
        logger.info("Compressed dialog history", extra={"session_id": session_id})

    async def cleanup_old_sessions(self, days: int = 7):
        """Delete sessions older than N days.

        Args:
            days: Age threshold in days
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.dialogs.delete_many({
            "updated_at": {"$lt": cutoff_date}
        })
        logger.info(
            "Cleaned up old sessions",
            extra={"deleted_count": result.deleted_count, "days": days}
        )
```

---

## 4. agent/agent.py

```python
"""Main Agent logic with tool calling."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re

from mistral_common.protocol.instruct.messages import UserMessage
from mistralai.client import MistralClient

from config import config
from mcp_client import MCPClient
from dialog_manager import DialogManager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Ты — AI помощник для сбора и обработки новостных дайджестов из Telegram-каналов.

Твои обязанности:
1. Парсить намерение пользователя (какой канал, за какой период)
2. Использовать доступные инструменты (tools) для получения данных
3. Обработать результаты и создать отчет

Доступные инструменты:
- get_subscriptions(): получить список каналов
- get_posts(channel_id, limit, date_from, date_to): получить посты
- collect_posts(channel_id): запустить фоновый сбор постов
- generate_summary(posts_text, channel_name): создать саммари
- export_pdf(summary_text, title, channel_name, date_range): сохранить PDF

Процесс:
1. Получи список подписок
2. Найди нужный канал по названию пользователя
3. Получи посты с правильным date_from
4. Если постов < 5, запусти collect_posts и повтори
5. Объедини посты в текст
6. Создай саммари
7. Экспортируй в PDF

Правила:
- Всегда проверяй наличие постов
- Если канал не найден, спроси у пользователя
- Логируй все действия
- Обрабатывай ошибки gracefully
"""


class Agent:
    """Main Agent for digest collection."""

    def __init__(self):
        """Initialize agent."""
        self.mcp_client = MCPClient(
            base_url=config.mcp_tools.base_url,
            timeout=config.mcp_tools.timeout_seconds,
        )
        self.dialog_manager = DialogManager(
            mongo_uri=config.mongo.uri,
            database=config.mongo.database,
        )
        self.mistral_client = MistralClient(
            model=config.mistral.model_name,
        )
        self.session_id: Optional[str] = None

    async def initialize(self):
        """Initialize connections."""
        await self.dialog_manager.connect()
        logger.info("Agent initialized")

    async def shutdown(self):
        """Shutdown connections."""
        await self.mcp_client.close()
        await self.dialog_manager.close()
        logger.info("Agent shutdown")

    async def start_session(self, user_id: str = "default_user"):
        """Start new dialog session.

        Args:
            user_id: User identifier
        """
        self.session_id = await self.dialog_manager.create_session(user_id)
        logger.info(f"Started session {self.session_id}")

    def _parse_days_from_text(self, text: str) -> int:
        """Extract days count from user input.

        Args:
            text: User message

        Returns:
            Days count (default 3)
        """
        # Match patterns like "3 дня", "за 3 дня", "последние 3 дня"
        match = re.search(r'(\d+)\s*(?:дн|день)', text)
        if match:
            return int(match.group(1))
        return 3  # default

    def _calculate_date_range(self, days: int) -> tuple:
        """Calculate date range for query.

        Args:
            days: Number of days back

        Returns:
            Tuple of (date_from, date_to)
        """
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)
        return date_from, date_to

    async def _find_channel(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Find channel by name in subscriptions.

        Args:
            channel_name: Channel name to find

        Returns:
            Channel dict or None
        """
        try:
            subs_response = await self.mcp_client.get_subscriptions()
            channels = subs_response.get("data", [])

            # Try exact match first
            for channel in channels:
                if channel["channel_name"].lower() == channel_name.lower():
                    return channel

            # Try partial match
            for channel in channels:
                if channel_name.lower() in channel["channel_name"].lower():
                    return channel

            return None

        except Exception as e:
            logger.error(f"Failed to find channel: {e}")
            raise

    async def _get_posts(
        self,
        channel_id: str,
        days: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get posts from channel.

        Args:
            channel_id: Channel ID
            days: Days back

        Returns:
            List of posts
        """
        date_from, date_to = self._calculate_date_range(days)

        try:
            posts_response = await self.mcp_client.get_posts(
                channel_id=channel_id,
                limit=100,
                date_from=date_from,
                date_to=date_to,
            )
            posts = posts_response.get("data", [])
            logger.info(f"Retrieved {len(posts)} posts from {channel_id}")
            return posts

        except Exception as e:
            logger.warning(f"Failed to get posts: {e}, attempting collection...")
            return []

    async def _trigger_collection_and_retry(
        self,
        channel_id: str,
        days: int = 3,
    ) -> List[Dict[str, Any]]:
        """Trigger post collection and retry fetch.

        Args:
            channel_id: Channel ID
            days: Days back

        Returns:
            List of posts
        """
        try:
            logger.info(f"Triggering collection for {channel_id}")
            await self.mcp_client.collect_posts(
                channel_id=channel_id,
                wait_for_completion=True,
                timeout_seconds=30,
            )

            # Wait a bit for collection to complete
            await asyncio.sleep(5)

            # Retry fetching posts
            return await self._get_posts(channel_id, days)

        except Exception as e:
            logger.error(f"Collection failed: {e}")
            raise

    async def process_user_input(self, user_input: str) -> str:
        """Process user input and generate digest.

        Args:
            user_input: User message

        Returns:
            Response message or PDF path
        """
        if not self.session_id:
            await self.start_session()

        # Store user message in history
        await self.dialog_manager.add_message(
            self.session_id,
            "user",
            user_input,
        )

        try:
            # Parse intent
            days = self._parse_days_from_text(user_input)
            logger.info(f"Parsed days: {days}")

            # Find channel
            channel_name = "Набока"  # Default, could be extracted better
            if "канал" in user_input:
                # Extract channel name from input
                pass

            channel = await self._find_channel(channel_name)
            if not channel:
                error_msg = f"Канал '{channel_name}' не найден. Проверьте название."
                await self.dialog_manager.add_message(self.session_id, "assistant", error_msg)
                return error_msg

            logger.info(f"Found channel: {channel['channel_id']}")

            # Get posts
            posts = await self._get_posts(channel["channel_id"], days)

            # Retry with collection if needed
            if len(posts) < 5:
                logger.info("Posts count < 5, triggering collection...")
                posts = await self._trigger_collection_and_retry(channel["channel_id"], days)

            if not posts:
                error_msg = f"Не удалось получить посты за последние {days} дней"
                await self.dialog_manager.add_message(self.session_id, "assistant", error_msg)
                return error_msg

            # Prepare posts text
            posts_text = "\n\n".join([
                f"[{post['date']}]\n{post['text']}"
                for post in posts
            ])

            # Generate summary
            summary_response = await self.mcp_client.generate_summary(
                posts_text=posts_text,
                posts_count=len(posts),
                channel_name=channel["channel_name"],
            )
            summary = summary_response["summary"]

            # Export to PDF
            date_from, date_to = self._calculate_date_range(days)
            pdf_response = await self.mcp_client.export_pdf(
                summary_text=summary,
                title=f"Дайджест {channel['channel_name']}",
                channel_name=channel["channel_id"],
                date_range={
                    "from": date_from.date().isoformat(),
                    "to": date_to.date().isoformat(),
                },
                metadata={
                    "posts_count": len(posts),
                    "generated_at": datetime.utcnow().isoformat(),
                },
            )

            pdf_path = pdf_response.get("pdf_path")

            # Prepare response
            response_msg = (
                f"✅ Дайджест готов!\n"
                f"📄 Файл: {pdf_path}\n"
                f"📊 Статистика:\n"
                f"   - Постов: {len(posts)}\n"
                f"   - Компрессия: {summary_response.get('compression_ratio', 0):.1%}"
            )

            # Store response in history
            await self.dialog_manager.add_message(self.session_id, "assistant", response_msg)

            return response_msg

        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            error_response = f"Ошибка: {str(e)}"
            await self.dialog_manager.add_message(self.session_id, "assistant", error_response)
            return error_response


async def main():
    """Main entry point."""
    logging.basicConfig(level=config.log_level)

    agent = Agent()

    try:
        await agent.initialize()

        # Example usage
        user_input = "собери мне дайджест по Набоке за последние 3 дня"
        response = await agent.process_user_input(user_input)
        print(response)

    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. mcp_tools/tools/subscriptions.py

```python
"""Get subscriptions tool."""

import logging
from typing import List, Dict, Any

from ..db.mongo import MongoClient

logger = logging.getLogger(__name__)


class SubscriptionsTool:
    """Get subscriptions from database."""

    def __init__(self, mongo: MongoClient):
        """Initialize.

        Args:
            mongo: MongoDB client
        """
        self.mongo = mongo

    async def execute(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get subscriptions.

        Args:
            user_id: Optional user ID

        Returns:
            List of channels
        """
        try:
            channels = await self.mongo.get_all_channels()
            logger.info(f"Retrieved {len(channels)} channels", extra={"user_id": user_id})
            return channels
        except Exception as e:
            logger.error(f"Failed to get subscriptions: {e}")
            raise
```

---

## 6. mcp_tools/tools/posts.py

```python
"""Get posts tool."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..db.mongo import MongoClient
from ..db.redis import RedisCache

logger = logging.getLogger(__name__)


class PostsTool:
    """Get posts from database with caching."""

    def __init__(self, mongo: MongoClient, redis: RedisCache):
        """Initialize.

        Args:
            mongo: MongoDB client
            redis: Redis cache
        """
        self.mongo = mongo
        self.redis = redis

    async def execute(
        self,
        channel_id: str,
        limit: int = 100,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get posts.

        Args:
            channel_id: Channel ID
            limit: Max posts
            date_from: Start date
            date_to: End date

        Returns:
            Dict with posts and metadata
        """
        # Try cache first
        cache_key = f"posts:{channel_id}:{date_from}:{date_to}"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Using cached posts for {channel_id}")
            return {**cached, "cached": True}

        try:
            posts = await self.mongo.get_posts(
                channel_id=channel_id,
                limit=limit,
                date_from=date_from,
                date_to=date_to,
            )

            result = {
                "channel_id": channel_id,
                "posts_count": len(posts),
                "data": posts,
                "cached": False,
            }

            # Cache for 1 hour
            await self.redis.set(cache_key, result, ttl=3600)

            logger.info(
                f"Retrieved {len(posts)} posts",
                extra={"channel_id": channel_id, "cached": False}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get posts: {e}")
            raise
```

---

## 7. Dockerfile для Agent

```dockerfile
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m -u 1000 agent
RUN chown -R agent:agent /app
USER agent

ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

CMD ["python3", "main.py"]
```

---

## 8. Dockerfile для MCP Tools

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 mcp
RUN chown -R mcp:mcp /app
USER mcp

ENV PYTHONUNBUFFERED=1

EXPOSE 8001 8002 8003 8004

CMD ["python3", "main.py"]
```

---

## 9. Примеры запуска

### Локальная разработка

```bash
# 1. Установить зависимости
pip install -r agent/requirements.txt
pip install -r mcp_tools/requirements.txt

# 2. Запустить MongoDB и Redis
docker run -d -p 27017:27017 mongo:7.0-alpine
docker run -d -p 6379:6379 redis:7-alpine

# 3. Запустить MCP Tools сервер
cd mcp_tools
python main.py

# 4. В другом терминале: запустить Agent
cd agent
python main.py
```

### Docker Compose

```bash
docker-compose up -d
docker-compose logs -f agent
```

---

## 10. requirements.txt

### agent/requirements.txt

```
motor==3.3.1                          # Async MongoDB driver
aiohttp==3.9.0                        # Async HTTP client
mistralai==0.0.7                      # Mistral API
mistral-common==0.0.3                 # Mistral common
python-dotenv==1.0.0                  # ENV management
tenacity==8.2.3                       # Retry logic
pydantic==2.5.0                       # Data validation
python-logging-loki==0.3.2            # Logging
```

### mcp_tools/requirements.txt

```
fastapi==0.104.1                      # Web framework
uvicorn==0.24.0                       # ASGI server
motor==3.3.1                          # Async MongoDB
redis==5.0.0                          # Redis client
aioredis==2.0.1                       # Async Redis
pydantic==2.5.0                       # Data validation
python-dotenv==1.0.0                  # ENV management
pymupdf==1.23.4                       # PDF generation (fitz)
reportlab==4.0.9                      # PDF generation
mistralai==0.0.7                      # Mistral for summarization
```

---

## Дополнительные советы для Cursor

1. **Попроси Cursor добавить:**
   - Логирование через структурированные логи (JSON)
   - Metrics через Prometheus
   - Unit tests через pytest
   - Integration tests с testcontainers

2. **Используй комплит в Cursor:**
   - Копируй код модуля и спроси "расширь с error handling"
   - "Добавь typing и docstrings"
   - "Напиши 5 unit tests для этого"

3. **Для отладки:**
   - Добавь debug logging везде где вызываются MCP tools
   - Используй `docker-compose logs -f --tail=100` для просмотра
   - Проверяй MongoDB через mongo shell: `docker exec -it agent_mongodb mongosh`
