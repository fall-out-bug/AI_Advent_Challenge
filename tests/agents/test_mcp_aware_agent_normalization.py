import pytest

from src.domain.agents.mcp_aware_agent import MCPAwareAgent


class RecordingMCPClient:
    def __init__(self):
        self.last_call = None
        self._channels = []
        self._metadata = {}

    async def call_tool(self, name: str, args: dict):
        self.last_call = (name, dict(args))
        if name == "list_channels":
            return {"channels": self._channels}
        if name == "get_channel_metadata":
            uname = args.get("channel_username", "")
            return self._metadata.get(uname, {})
        return {"status": "success"}


class DummyLLMClient:
    async def make_request(self, *args, **kwargs):
        class R:
            response = "{}"
            input_tokens = 0
            response_tokens = 0

        return R()


@pytest.mark.asyncio
async def test_days_to_hours_and_user_id_injection():
    mcp = RecordingMCPClient()
    llm = DummyLLMClient()
    agent = MCPAwareAgent(mcp_client=mcp, llm_client=llm)

    tools = [
        type(
            "T",
            (),
            {
                "name": "get_channel_digest_by_name",
                "description": "",
                "input_schema": {
                    "type": "object",
                    "properties": {"user_id": {}, "channel_username": {}, "hours": {}},
                    "required": ["user_id", "channel_username", "hours"],
                },
            },
        )()
    ]

    params = {"channel_name": "Набока", "days": 3}
    result = await agent._stage_execution(
        tool_name="get_channel_digest_by_name",
        tool_params=params,
        tools=tools,
        user_id=42,
    )

    assert result.get("status") == "success"
    assert mcp.last_call is not None
    name, args = mcp.last_call
    assert name == "get_channel_digest_by_name"
    assert args["user_id"] == 42
    assert args["hours"] == 72
    assert args["channel_username"] in {"onaboka", "Набока", "naboka", "onaboka"}


@pytest.mark.asyncio
async def test_list_channels_injects_user_id():
    mcp = RecordingMCPClient()
    llm = DummyLLMClient()
    agent = MCPAwareAgent(mcp_client=mcp, llm_client=llm)

    tools = [
        type(
            "T",
            (),
            {
                "name": "list_channels",
                "description": "",
                "input_schema": {
                    "type": "object",
                    "properties": {"user_id": {}},
                    "required": ["user_id"],
                },
            },
        )()
    ]

    result = await agent._stage_execution(
        tool_name="list_channels",
        tool_params={},
        tools=tools,
        user_id=7,
    )

    assert result.get("status") == "success"
    name, args = mcp.last_call
    assert name == "list_channels"
    assert args["user_id"] == 7


@pytest.mark.asyncio
async def test_channel_username_resolution_via_metadata_matches_title():
    mcp = RecordingMCPClient()
    # Simulate two channels; metadata title matches human query
    mcp._channels = [
        {"channel_username": "onaboka"},
        {"channel_username": "random"},
    ]
    mcp._metadata = {
        "onaboka": {"title": "Набока орет в борщ"},
        "random": {"title": "Случайный"},
    }
    llm = DummyLLMClient()
    agent = MCPAwareAgent(mcp_client=mcp, llm_client=llm)

    resolved = await agent._resolve_channel_username_via_metadata("Набоки", user_id=1)
    assert resolved == "onaboka"


@pytest.mark.asyncio
async def test_channel_username_resolution_unresolved_returns_none():
    mcp = RecordingMCPClient()
    mcp._channels = [{"channel_username": "foo"}]
    mcp._metadata = {"foo": {"title": "Бар"}}
    llm = DummyLLMClient()
    agent = MCPAwareAgent(mcp_client=mcp, llm_client=llm)

    resolved = await agent._resolve_channel_username_via_metadata(
        "Неизвестный", user_id=1
    )
    assert resolved is None
