<!-- 5e7ca8d7-5d82-44cc-8738-2852c21828a6 354df1c3-f87b-4883-a97a-e11367a7bd91 -->
# Day 11 — Summarizer v2 (Map-Reduce, vLLM, Infra)

## Scope

- Backend: switch to vLLM OpenAI-compatible API, fix parsing, add retries.
- Summarization: Map-Reduce with sentence-aware chunking, prompts, token counting.
- Infra: docker-compose with vLLM service, app service, metrics hooks; CI for lint/tests.
- Tests: unit tests for chunking, summarizer, LLM client parsing; ≥80% coverage.

## File-by-file changes

### LLM client (vLLM API and parsing)

- Edit `src/infrastructure/clients/llm_client.py`
  - Change endpoint to `/v1/chat/completions` and include `model`.
  - Add `top_p` and Mistral stop tokens `["</s>", "[/INST]"]`.
  - Parse `choices[0].message.content`; raise on empty/invalid.
  - Optional: `tenacity`-based retry, connection pooling (`httpx.Limits`).

Snippet (essential):

```python
url = f"{self.url}/v1/chat/completions"
payload = {
  "model": os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"),
  "messages": [{"role": "user", "content": prompt}],
  "max_tokens": max_tokens, "temperature": temperature, "top_p": 0.95,
  "stop": ["</s>", "[/INST]"]
}
resp = response.json()
content = resp["choices"][0]["message"].get("content", "").strip()
```

### New: token counting

- Add `src/infrastructure/llm/token_counter.py`
  - `TokenCounter` using `transformers.AutoTokenizer` for the model in env `LLM_MODEL`.

### New: sentence-aware chunker

- Add `src/infrastructure/llm/chunker.py`
  - `SemanticChunker.chunk_text(text) -> List[TextChunk]` with overlap (tokens), sentence boundaries.
  - Config via `get_settings()`: `chunk_size_tokens`, `chunk_overlap_tokens`.

### New: summarization prompts

- Add `src/infrastructure/llm/prompts.py`
  - `get_map_prompt(text, language, max_sentences)`
  - `get_reduce_prompt(summaries, language, max_sentences)`

### Map-Reduce summarizer

- Edit `src/infrastructure/llm/summarizer.py`
  - Keep current `summarize_posts` for shorter inputs, but add a new class `MapReduceSummarizer` used under the hood when token count exceeds `chunk_size_tokens`.
  - Map: parallel `llm.generate` per chunk; Reduce: combine chunk summaries and generate final.
  - Respect settings: language, sentences per chunk, max tokens for map/reduce results.
  - Add Prometheus metrics (optional but scoped): duration histogram per phase, chunks counter.

### Settings

- Edit `src/infrastructure/config/settings.py`
  - Add: `LLM_MODEL`, `SUMMARIZER_SENTENCES_PER_CHUNK`, `SUMMARIZER_CHUNK_SIZE_TOKENS`, `SUMMARIZER_CHUNK_OVERLAP_TOKENS`, `SUMMARIZER_FINAL_MAX_TOKENS`, `SUMMARIZER_SUMMARY_MAX_TOKENS` with sensible defaults.

### Digest tool integration

- Edit `src/presentation/mcp/tools/digest_tools.py`
  - No API changes; it will benefit from improved summaries. Optionally allow `DIGEST_MAX_CHANNELS` and char limits already in settings.

## Tests (TDD)

- Add `tests/llm/test_llm_client.py`: parse `choices[0].message.content`, error cases, retry behavior with mocked httpx.
- Add `tests/llm/test_token_counter.py`: counts increasing with text length.
- Add `tests/llm/test_chunker.py`: sentence-preserving chunks, overlap, single-chunk path, oversize sentence error.
- Add `tests/llm/test_prompts.py`: language variants and formatting.
- Add `tests/llm/test_summarizer_map_reduce.py`: map calls parallelized (use asyncio gather spy), reduce prompt produced, final result length and uniqueness constraints.

## Infra

- Add `docker-compose.yml` (root): vLLM service (`vllm/vllm-openai` port 8080->8000) and app service; wire `LLM_URL=http://llm-server:8000`.
- Add `docker/Dockerfile.app`: minimal python image with project deps.
- CI: ensure `pytest -q --cov=src --cov-report=term` and lint (flake8/black/isort/mypy) stages.

## Rollout

1) Implement tests first (red).

2) Implement client API fix; make tests pass (green).

3) Add token counter, chunker, prompts with tests.

4) Implement Map-Reduce summarizer; integrate into `summarize_posts` based on token length.

5) Wire metrics (Prometheus) and minimal docs in README.

6) Add docker compose and run locally; adjust env.

## Config defaults

- `LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2`
- `SUMMARIZER_LANGUAGE=ru`
- `SUMMARIZER_TEMPERATURE=0.2`
- `SUMMARIZER_SUMMARY_MAX_TOKENS=400`
- `SUMMARIZER_FINAL_MAX_TOKENS=800`
- `SUMMARIZER_SENTENCES_PER_CHUNK=5`
- `SUMMARIZER_CHUNK_SIZE_TOKENS=3000`
- `SUMMARIZER_CHUNK_OVERLAP_TOKENS=200`

### To-dos

- [ ] Fix LLM client to use vLLM /v1/chat/completions and parse choices[0].message.content
- [ ] Create TokenCounter with transformers tokenizer for configured model
- [ ] Implement SemanticChunker with sentence boundaries and overlap
- [ ] Add map/reduce prompt templates for ru/en
- [ ] Implement MapReduceSummarizer and integrate into summarize_posts when long
- [ ] Expose Prometheus metrics for map/reduce duration and chunks processed
- [ ] Write unit tests for client, counter, chunker, prompts, summarizer
- [ ] Ensure lint, mypy, pytest with coverage ≥80% in CI pipeline
- [ ] Add docker-compose with vLLM server and app; Dockerfile.app
- [ ] Update README with configuration, run instructions, and model notes