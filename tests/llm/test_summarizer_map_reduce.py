import asyncio
import pytest

from src.infrastructure.llm.token_counter import TokenCounter
from src.infrastructure.llm.chunker import SemanticChunker
from src.infrastructure.llm.prompts import get_map_prompt, get_reduce_prompt
from src.infrastructure.llm.summarizer import MapReduceSummarizer


class _FakeLLM:
    def __init__(self):
        self.calls = []

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 128) -> str:
        self.calls.append(prompt)
        # Return a short deterministic string based on whether it's map or reduce
        if "КЛЮЧЕВЫЕ ФАКТЫ:" in prompt or "KEY FACTS" in prompt:
            return "fact one. fact two."
        if "ИТОГОВАЯ СУММАРИЗАЦИЯ" in prompt or "FINAL SUMMARY" in prompt:
            return "final summary."
        return "unknown"


@pytest.mark.asyncio
async def test_map_reduce_runs_multiple_map_calls_when_long_text():
    llm = _FakeLLM()
    counter = TokenCounter()
    # very small max_tokens to force many chunks
    chunker = SemanticChunker(counter, max_tokens=30, overlap_tokens=10)
    summarizer = MapReduceSummarizer(llm=llm, token_counter=counter, chunker=chunker, language="en")

    long_text = " ".join([f"Sentence {i}." for i in range(40)])
    out = await summarizer.summarize_text(long_text, max_sentences=3)

    # Should call LLM multiple times (map for chunks + one reduce)
    assert out == "final summary."
    assert len(llm.calls) >= 2


