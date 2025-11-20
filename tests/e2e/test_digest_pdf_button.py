"""E2E tests for bot button click → PDF generation → file sent.

Following TDD principles:
- Tests verify complete user workflow
- Isolated test environment
- Test data cleanup
- Expected results documented
- Runs in docker/compose environment
"""

import base64
import types
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

try:
    from aiogram.types import CallbackQuery, Chat, Message, User
except Exception:
    pytest.skip("aiogram is required for E2E tests", allow_module_level=True)

import src.presentation.bot.handlers.menu as menu_mod
from src.infrastructure.cache.pdf_cache import get_pdf_cache


class FakeMessage:
    """Fake message for testing."""

    def __init__(self, user_id: int = 123) -> None:
        self.sent: list[str] = []
        self.documents: list[dict] = []
        self.chat_actions: list[str] = []
        self.chat = types.SimpleNamespace(id=123)
        self.from_user = types.SimpleNamespace(id=user_id)

        async def send_chat_action(chat_id: int, action: str) -> None:
            self.chat_actions.append(action)

        self.bot = types.SimpleNamespace(send_chat_action=send_chat_action)

    async def answer(self, text: str) -> None:
        """Answer with text message."""
        self.sent.append(text)

    async def answer_document(self, document: bytes, filename: str) -> None:
        """Answer with document."""
        self.documents.append({"document": document, "filename": filename})


class FakeCall:
    """Fake callback query for testing."""

    def __init__(self, user_id: int = 123) -> None:
        self.from_user = types.SimpleNamespace(id=user_id)
        self.message = FakeMessage(user_id=user_id)
        self.answered = False

    async def answer(self, text: str | None = None, show_alert: bool = False) -> None:
        """Answer callback query."""
        self.answered = True


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear PDF cache before each test."""
    cache = get_pdf_cache()
    cache.clear()
    yield
    cache.clear()


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_digest_button_click_generates_and_sends_pdf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2E: User clicks Digest button → PDF generated → PDF sent.

    Scenario:
    1. User clicks "Digest" button
    2. Bot shows upload action
    3. Bot calls MCP tools to generate PDF
    4. Bot sends PDF document to user
    5. User receives PDF file
    """
    tool_calls = []

    class FakeClient:
        """Mock MCP client for testing."""

        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            """Mock tool calls."""
            tool_calls.append((tool_name, arguments))

            if tool_name == "get_posts_from_db":
                return {
                    "posts_by_channel": {
                        "channel1": [
                            {
                                "text": "Post 1 from channel1",
                                "date": datetime.utcnow().isoformat(),
                                "message_id": "1",
                                "channel_username": "channel1",
                            },
                            {
                                "text": "Post 2 from channel1",
                                "date": (
                                    datetime.utcnow() - timedelta(hours=1)
                                ).isoformat(),
                                "message_id": "2",
                                "channel_username": "channel1",
                            },
                        ],
                        "channel2": [
                            {
                                "text": "Post 1 from channel2",
                                "date": datetime.utcnow().isoformat(),
                                "message_id": "3",
                                "channel_username": "channel2",
                            },
                        ],
                    },
                    "total_posts": 3,
                    "channels_count": 2,
                }
            elif tool_name == "summarize_posts":
                channel = arguments.get("channel_username", "unknown")
                return {
                    "summary": f"Summary of posts from {channel}",
                    "post_count": len(arguments.get("posts", [])),
                    "channel": channel,
                }
            elif tool_name == "format_digest_markdown":
                return {
                    "markdown": "# Channel Digest\n\n## Channel1\nSummary\n\n## Channel2\nSummary",
                    "sections_count": 2,
                }
            elif tool_name == "combine_markdown_sections":
                return {
                    "combined_markdown": "# Channel Digest\n\nContent",
                    "total_chars": 100,
                }
            elif tool_name == "convert_markdown_to_pdf":
                pdf_bytes = b"%PDF-1.4\nfake pdf content"
                return {
                    "pdf_bytes": base64.b64encode(pdf_bytes).decode(),
                    "file_size": len(pdf_bytes),
                    "pages": 1,
                }
            return {}

    monkeypatch.setattr(menu_mod, "MCPClient", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)

    # Verify workflow
    assert call.answered is True  # Callback answered
    assert "upload_document" in call.message.chat_actions  # Upload action shown

    # Verify MCP tools were called in correct order
    assert len(tool_calls) >= 5
    assert tool_calls[0][0] == "get_posts_from_db"
    assert tool_calls[1][0] == "summarize_posts"  # For channel1
    assert tool_calls[2][0] == "summarize_posts"  # For channel2
    assert tool_calls[3][0] == "format_digest_markdown"
    assert tool_calls[4][0] == "combine_markdown_sections"
    assert tool_calls[5][0] == "convert_markdown_to_pdf"

    # Verify PDF was sent
    assert len(call.message.documents) == 1
    assert call.message.documents[0]["filename"].endswith(".pdf")
    assert call.message.documents[0]["filename"].startswith("digest_")

    # Verify PDF content
    pdf_bytes = call.message.documents[0]["document"]
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_digest_button_click_no_posts_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2E: User clicks Digest button → No posts → Informative message.

    Scenario:
    1. User clicks "Digest" button
    2. No posts found in database
    3. Bot sends informative message
    """

    class FakeClient:
        """Mock MCP client for testing."""

        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            """Mock tool calls."""
            if tool_name == "get_posts_from_db":
                return {
                    "posts_by_channel": {},
                    "total_posts": 0,
                    "channels_count": 0,
                }
            return {}

    monkeypatch.setattr(menu_mod, "MCPClient", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)

    # Verify informative message sent
    assert len(call.message.sent) > 0
    assert any(
        "No new posts" in msg or "no posts" in msg.lower() for msg in call.message.sent
    )

    # Verify no PDF was sent
    assert len(call.message.documents) == 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_digest_button_click_cached_pdf_sent_immediately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2E: User clicks Digest button → Cached PDF → Sent immediately.

    Scenario:
    1. User clicks "Digest" button
    2. PDF is cached (from previous request)
    3. Bot sends cached PDF immediately
    4. No MCP tool calls made
    """
    tool_calls = []

    class FakeClient:
        """Mock MCP client for testing."""

        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            """Mock tool calls (should not be called)."""
            tool_calls.append(tool_name)
            return {}

    monkeypatch.setattr(menu_mod, "MCPClient", lambda: FakeClient())

    # Setup: Cache PDF
    cache = get_pdf_cache()
    pdf_bytes = b"%PDF-1.4\ncached pdf content"
    now = datetime.utcnow()
    date_hour = now.strftime("%Y-%m-%d-%H")
    cache.set(user_id=123, date_hour=date_hour, pdf_bytes=pdf_bytes)

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)

    # Verify no MCP tools were called (cache hit)
    assert len(tool_calls) == 0

    # Verify PDF was sent from cache
    assert len(call.message.documents) == 1
    assert call.message.documents[0]["document"] == pdf_bytes


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_digest_button_click_pdf_error_fallback_to_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2E: User clicks Digest button → PDF error → Fallback to text digest.

    Scenario:
    1. User clicks "Digest" button
    2. PDF generation fails
    3. Bot falls back to text digest
    4. User receives text digest
    """

    class FakeClient:
        """Mock MCP client for testing."""

        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            """Mock tool calls."""
            if tool_name == "get_posts_from_db":
                return {
                    "posts_by_channel": {
                        "channel1": [
                            {
                                "text": "Post 1",
                                "date": datetime.utcnow().isoformat(),
                                "message_id": "1",
                            },
                        ],
                    },
                    "total_posts": 1,
                    "channels_count": 1,
                }
            elif tool_name == "summarize_posts":
                return {
                    "summary": "Summary text",
                    "post_count": 1,
                    "channel": "channel1",
                }
            elif tool_name == "format_digest_markdown":
                return {
                    "markdown": "# Digest\n\nContent",
                    "sections_count": 1,
                }
            elif tool_name == "combine_markdown_sections":
                return {
                    "combined_markdown": "# Digest\n\nContent",
                    "total_chars": 50,
                }
            elif tool_name == "convert_markdown_to_pdf":
                # Simulate PDF generation error
                return {
                    "error": "PDF generation failed",
                    "pdf_bytes": "",
                    "file_size": 0,
                    "pages": 0,
                }
            elif tool_name == "get_channel_digest":
                # Fallback tool
                return {
                    "digests": [{"channel": "channel1", "summary": "Fallback summary"}]
                }
            return {}

    monkeypatch.setattr(menu_mod, "MCPClient", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)

    # Verify fallback to text digest
    assert len(call.message.sent) > 0
    assert any(
        "📰" in msg or "Fallback" in msg or "summary" in msg.lower()
        for msg in call.message.sent
    )

    # Verify no PDF was sent
    assert len(call.message.documents) == 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_digest_button_click_multiple_channels_processed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2E: User clicks Digest button → Multiple channels → All processed in PDF.

    Scenario:
    1. User clicks "Digest" button
    2. Multiple channels have posts
    3. All channels are summarized
    4. PDF contains all channel summaries
    """
    tool_calls = []

    class FakeClient:
        """Mock MCP client for testing."""

        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            """Mock tool calls."""
            tool_calls.append(tool_name)

            if tool_name == "get_posts_from_db":
                posts = {
                    f"channel{i}": [
                        {
                            "text": f"Post from channel{i}",
                            "date": datetime.utcnow().isoformat(),
                            "message_id": str(i),
                        },
                    ]
                    for i in range(5)
                }
                return {
                    "posts_by_channel": posts,
                    "total_posts": 5,
                    "channels_count": 5,
                }
            elif tool_name == "summarize_posts":
                return {
                    "summary": "Summary",
                    "post_count": 1,
                    "channel": arguments.get("channel_username", "unknown"),
                }
            elif tool_name == "format_digest_markdown":
                return {
                    "markdown": "# Digest\n\n"
                    + "\n\n".join([f"## Channel{i}" for i in range(5)]),
                    "sections_count": 5,
                }
            elif tool_name == "combine_markdown_sections":
                return {
                    "combined_markdown": "# Digest\n\nContent",
                    "total_chars": 100,
                }
            elif tool_name == "convert_markdown_to_pdf":
                pdf_bytes = b"%PDF-1.4\nfake pdf"
                return {
                    "pdf_bytes": base64.b64encode(pdf_bytes).decode(),
                    "file_size": len(pdf_bytes),
                    "pages": 1,
                }
            return {}

    monkeypatch.setattr(menu_mod, "MCPClient", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)

    # Verify all channels were summarized
    summarize_calls = [call for call in tool_calls if call == "summarize_posts"]
    assert len(summarize_calls) == 5  # One per channel

    # Verify PDF was sent
    assert len(call.message.documents) == 1
