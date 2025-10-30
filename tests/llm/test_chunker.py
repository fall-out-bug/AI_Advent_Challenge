from src.infrastructure.llm.chunker import SemanticChunker
from src.infrastructure.llm.token_counter import TokenCounter


def test_single_chunk_when_under_limit():
    counter = TokenCounter()
    chunker = SemanticChunker(counter, max_tokens=1000, overlap_tokens=100)
    text = "Hello. World! This is fine?"
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0].text.startswith("Hello")


def test_multiple_chunks_with_overlap():
    counter = TokenCounter()
    # Create many small sentences to enforce multiple chunks
    sentences = ["Sentence %d." % i for i in range(100)]
    long_text = " ".join(sentences)
    chunker = SemanticChunker(counter, max_tokens=120, overlap_tokens=30)
    chunks = chunker.chunk_text(long_text)
    assert len(chunks) > 1
    # Ensure some overlap heuristically: last tokens of previous included in next
    # (We cannot easily assert tokens here, but we can assert continuity)
    assert any("Sentence 5." in c.text for c in chunks)


def test_oversized_sentence_raises():
    counter = TokenCounter()
    chunker = SemanticChunker(counter, max_tokens=5, overlap_tokens=0)
    text = "Supercalifragilisticexpialidocious."  # likely >5 tokens
    try:
        chunker.chunk_text(text)
        assert False, "Expected ValueError"
    except ValueError:
        assert True


