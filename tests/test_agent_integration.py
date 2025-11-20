import json

import pytest

from src.domain.agents.mcp_aware_agent import MCPAwareAgent
from src.domain.agents.schemas import AgentRequest


class MockMCPClient:
    async def discover_tools(self):
        # Minimal tool schemas used by agent validation
        return [
            {
                "name": "get_channel_digest_by_name",
                "description": "Get digest",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "channel_username": {"type": "string"},
                        "hours": {"type": "integer"},
                        "user_id": {"type": "integer"},
                    },
                    "required": ["channel_username", "hours", "user_id"],
                },
            },
            {
                "name": "list_channels",
                "description": "List",
                "input_schema": {
                    "type": "object",
                    "properties": {"user_id": {"type": "integer"}},
                    "required": ["user_id"],
                },
            },
            {
                "name": "get_channel_metadata",
                "description": "Meta",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "channel_username": {"type": "string"},
                        "user_id": {"type": "integer"},
                    },
                    "required": ["channel_username", "user_id"],
                },
            },
        ]

    async def call_tool(self, tool_name, arguments):
        if tool_name == "get_channel_digest_by_name":
            return {
                "channel": arguments.get("channel_username", "onaboka"),
                "digests": [
                    {
                        "channel": arguments.get("channel_username", "onaboka"),
                        "summary": "Short summary",
                        "post_count": 3,
                    }
                ],
            }
        if tool_name == "list_channels":
            return {"channels": [{"channel_username": "onaboka"}]}
        if tool_name == "get_channel_metadata":
            return {"success": True, "title": "Onaboka", "username": "onaboka"}
        return {"status": "success"}


class MockUnifiedModelClient:
    async def make_request(
        self, model_name: str, prompt: str, max_tokens: int, temperature: float
    ):
        # Legacy fallback path not used in primary flow; return simple text
        class R:
            response = "ok"
            response_tokens = 2
            input_tokens = 5

        return R()


class MockChatClient:
    async def create_completion(self, **kwargs):
        # Return a structured tool call matching OpenAI format
        return {
            "id": "test",
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "get_channel_digest_by_name",
                            "arguments": json.dumps(
                                {"channel_name": "onaboka", "days": 2}
                            ),
                        },
                    }
                ],
            },
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_channel_digest_by_name",
                        "arguments": json.dumps({"channel_name": "onaboka", "days": 2}),
                    },
                }
            ],
        }


@pytest.mark.asyncio
async def test_agent_digest_workflow_monkeypatch(monkeypatch):
    agent = MCPAwareAgent(
        mcp_client=MockMCPClient(), llm_client=MockUnifiedModelClient()
    )
    # Inject mock chat client
    agent.chat_client = MockChatClient()

    req = AgentRequest(
        user_id=123, message="Создай дайджест по Набока за 2 дня", session_id="s1"
    )
    result = await agent.process(req)

    assert result.success is True
    assert "Дайджест" in result.text or "📌" in result.text or "постов" in result.text
    assert result.tools_used == ["get_channel_digest_by_name"]
