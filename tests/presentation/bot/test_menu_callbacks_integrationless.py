import asyncio
import types

import pytest

try:
    from aiogram.types import CallbackQuery, Chat, Message, User
except Exception:
    pytest.skip("aiogram is required for menu tests", allow_module_level=True)

import src.presentation.bot.handlers.menu as menu_mod
from src.infrastructure.cache.pdf_cache import get_pdf_cache


@pytest.fixture(autouse=True)
def reset_pdf_cache() -> None:
    """Ensure each test starts with a clean PDF cache."""
    cache = get_pdf_cache()
    cache.clear()
    yield
    cache.clear()


class FakeMessage:
    def __init__(self) -> None:
        self.sent: list[str] = []
        self.documents: list[dict] = []
        self.chat_actions: list[str] = []
        self.chat = types.SimpleNamespace(id=123)

        # Create bot attribute
        async def send_chat_action(chat_id: int, action: str) -> None:
            self.chat_actions.append(action)

        self.bot = types.SimpleNamespace(send_chat_action=send_chat_action)

    async def answer(self, text: str) -> None:
        self.sent.append(text)

    async def edit_text(self, text: str, reply_markup=None) -> None:  # noqa: D401
        self.sent.append(text)

    async def answer_document(self, document, filename: str | None = None) -> None:
        resolved_filename = filename
        if resolved_filename is None:
            resolved_filename = getattr(document, "filename", "document.pdf")
        self.documents.append({"document": document, "filename": resolved_filename})


class FakeCall:
    def __init__(self, user_id: int) -> None:
        self.from_user = types.SimpleNamespace(id=user_id)
        self.message = FakeMessage()

    async def answer(self) -> None:  # noqa: D401 Dummy ack
        return None


@pytest.mark.asyncio
async def test_callback_summary_shows_guidance() -> None:
    call = FakeCall(user_id=123)
    await menu_mod.callback_summary(call)
    assert any("digest" in s.lower() for s in call.message.sent)


@pytest.mark.asyncio
async def test_callback_digest_calls_mcp_and_replies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test callback_digest falls back to text digest."""

    class FakeClient:
        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            if tool_name == "get_channel_digest":
                return {"digests": [{"channel": "news", "summary": "top story"}]}
            return {}

    monkeypatch.setattr(menu_mod, "get_mcp_client", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)
    assert any("📰" in s for s in call.message.sent)


@pytest.mark.asyncio
async def test_callback_digest_generates_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test callback_digest generates PDF successfully."""
    import base64

    tool_calls = []

    class FakeClient:
        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            tool_calls.append(tool_name)
            if tool_name == "get_posts_from_db":
                return {
                    "posts_by_channel": {
                        "channel1": [
                            {"text": "Post 1", "date": "2024-01-15", "message_id": "1"}
                        ]
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
                    "markdown": "# Digest\n\n## Channel1\nSummary",
                    "sections_count": 1,
                }
            elif tool_name == "combine_markdown_sections":
                return {
                    "combined_markdown": "# Digest\n\n## Channel1\nSummary",
                    "total_chars": 50,
                }
            elif tool_name == "convert_markdown_to_pdf":
                pdf_bytes = b"fake pdf bytes"
                return {
                    "pdf_bytes": base64.b64encode(pdf_bytes).decode(),
                    "file_size": len(pdf_bytes),
                    "pages": 1,
                }
            return {}

    monkeypatch.setattr(menu_mod, "get_mcp_client", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)

    # Check that PDF tools were called
    assert "get_posts_from_db" in tool_calls
    assert "summarize_posts" in tool_calls
    assert "convert_markdown_to_pdf" in tool_calls
    # Check that document was sent
    assert len(call.message.documents) > 0
    assert call.message.documents[0]["filename"].endswith(".pdf")


@pytest.mark.asyncio
async def test_callback_digest_handles_no_posts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test callback_digest handles no posts case."""

    class FakeClient:
        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            if tool_name == "get_posts_from_db":
                return {"posts_by_channel": {}, "total_posts": 0, "channels_count": 0}
            return {}

    monkeypatch.setattr(menu_mod, "get_mcp_client", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)
    assert any("No new posts" in s for s in call.message.sent)


@pytest.mark.asyncio
async def test_callback_digest_cache_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test callback_digest uses cache when available."""
    import base64
    from datetime import datetime

    tool_calls = []

    class FakeClient:
        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            tool_calls.append(tool_name)
            return {}

    monkeypatch.setattr(menu_mod, "get_mcp_client", lambda: FakeClient())
    # Mock cache to return cached PDF
    from src.infrastructure.cache.pdf_cache import get_pdf_cache

    cache = get_pdf_cache()
    pdf_bytes = b"cached pdf bytes"
    # Use current date_hour format
    now = datetime.utcnow()
    date_hour = now.strftime("%Y-%m-%d-%H")
    cache.set(user_id=123, date_hour=date_hour, pdf_bytes=pdf_bytes)

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)

    # Should not call any tools when cache hit
    assert len(tool_calls) == 0
    assert len(call.message.documents) > 0


@pytest.mark.asyncio
async def test_callback_digest_fallback_to_text_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test callback_digest falls back to text digest on PDF error."""

    class FakeClient:
        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            if tool_name == "get_posts_from_db":
                return {
                    "posts_by_channel": {
                        "channel1": [
                            {"text": "Post 1", "date": "2024-01-15", "message_id": "1"}
                        ]
                    },
                    "total_posts": 1,
                    "channels_count": 1,
                }
            elif tool_name == "convert_markdown_to_pdf":
                # Simulate PDF generation error
                return {"error": "PDF generation failed"}
            elif tool_name == "get_channel_digest":
                return {
                    "digests": [{"channel": "channel1", "summary": "Fallback summary"}]
                }
            return {}

    monkeypatch.setattr(menu_mod, "get_mcp_client", lambda: FakeClient())

    call = FakeCall(user_id=123)
    await menu_mod.callback_digest(call)
    # Should fallback to text digest
    assert any("📰" in s or "Fallback" in s for s in call.message.sent)
