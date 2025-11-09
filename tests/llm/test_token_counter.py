import os
import pytest

from src.infrastructure.llm.token_counter import TokenCounter


@pytest.mark.skipif(
    "CI" in os.environ and os.environ.get("CI") == "true",
    reason="Tokenizer download may be slow in CI",
)
def test_token_count_monotonic_growth():
    counter = TokenCounter(
        model_name=os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    )
    short = "hello"
    medium = short * 50
    long = short * 200
    assert (
        counter.count_tokens(short)
        < counter.count_tokens(medium)
        < counter.count_tokens(long)
    )


def test_batch_count_matches_individual():
    counter = TokenCounter(
        model_name=os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    )
    texts = ["a", "some text", "even longer text for counting"]
    batch = counter.batch_count_tokens(texts)
    indiv = [counter.count_tokens(t) for t in texts]
    assert batch == indiv
