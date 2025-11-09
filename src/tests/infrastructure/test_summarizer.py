import pytest


class MockLLM:
    async def generate(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 256
    ) -> str:
        return "Summary: Important news from tech channel."


@pytest.mark.asyncio
async def test_summarize_posts_returns_text():
    from src.infrastructure.clients.llm_client import FallbackLLMClient
    from src.infrastructure.llm.summarizer import summarize_posts

    posts = [{"text": "Post 1"}, {"text": "Post 2"}]
    summary = await summarize_posts(posts, max_sentences=3, llm=FallbackLLMClient())
    assert isinstance(summary, str)
    assert len(summary) > 0


@pytest.mark.asyncio
async def test_summarize_posts_empty_list():
    from src.infrastructure.clients.llm_client import FallbackLLMClient
    from src.infrastructure.llm.summarizer import summarize_posts

    summary = await summarize_posts([], max_sentences=3, llm=FallbackLLMClient())
    assert summary == "No posts to summarize."
