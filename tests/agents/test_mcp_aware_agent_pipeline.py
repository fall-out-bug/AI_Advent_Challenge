import asyncio
import types
import pytest

from src.domain.agents.mcp_aware_agent import MCPAwareAgent
from src.domain.agents.schemas import AgentRequest, ToolMetadata


class FakeMCPClient:
    async def call_tool(self, name: str, args: dict):
        if name == "list_channels":
            return {
                "channels": [{"channel_username": "python"}, {"channel_username": "ml"}]
            }
        if name == "get_channel_digest_by_name":
            ch = args.get("channel_name", "unknown")
            days = args.get("days", 3)
            return {
                "channel": ch,
                "digests": [
                    {"channel": ch, "summary": f"Summary {ch}", "post_count": 2},
                ],
                "days": days,
            }
        return {"status": "success"}


class FakeUnifiedModelClient:
    def __init__(self):
        self._response_queue: list[str] = []

    def queue_response(self, text: str) -> None:
        self._response_queue.append(text)

    async def make_request(
        self, model_name: str, prompt: str, max_tokens: int, temperature: float
    ):
        # Return queued responses in FIFO order
        text = self._response_queue.pop(0) if self._response_queue else "{}"

        class R:
            response = text
            input_tokens = 0
            response_tokens = len(text)

        return R()


@pytest.mark.asyncio
async def test_decision_json_direct_and_execution_formatting():
    mcp_client = FakeMCPClient()
    llm_client = FakeUnifiedModelClient()
    agent = MCPAwareAgent(mcp_client=mcp_client, llm_client=llm_client)

    # Decision: direct JSON tool call
    llm_client.queue_response('{"tool": "list_channels", "params": {}}')

    req = AgentRequest(user_id=1, message="Какие каналы у меня?", session_id="s1")
    resp = await agent.process(req)
    assert resp.success is True
    assert "python" in resp.text
    assert resp.tools_used == ["list_channels"]


@pytest.mark.asyncio
async def test_decision_buried_in_text_then_parsed():
    mcp_client = FakeMCPClient()
    llm_client = FakeUnifiedModelClient()
    agent = MCPAwareAgent(mcp_client=mcp_client, llm_client=llm_client)

    llm_client.queue_response(
        """
Сейчас я получу список ваших каналов...

```json
{"tool": "list_channels", "params": {}}
```
Это поможет...
"""
    )

    req = AgentRequest(user_id=1, message="Покажи список каналов", session_id="s2")
    resp = await agent.process(req)
    assert resp.success is True
    assert "каналов" in resp.text or "подписки" in resp.text
    assert resp.tools_used == ["list_channels"]


@pytest.mark.asyncio
async def test_heuristic_when_no_json():
    mcp_client = FakeMCPClient()
    llm_client = FakeUnifiedModelClient()
    agent = MCPAwareAgent(mcp_client=mcp_client, llm_client=llm_client)

    # No JSON, heuristic should pick digest_by_name with days
    llm_client.queue_response("Хочу дайджест по каналу Набока за 3 дня")

    req = AgentRequest(
        user_id=1, message="Хочу дайджест по каналу Набока за 3 дня", session_id="s3"
    )
    resp = await agent.process(req)
    assert resp.success is True
    assert resp.tools_used[0] in ["get_channel_digest_by_name", "get_channel_digest"]
