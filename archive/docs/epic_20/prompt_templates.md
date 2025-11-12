# Prompt Templates · Epic 20 RAG vs Non-RAG

## 1. System Prompts

### 1.1 Non-RAG Mode (Baseline)

**Purpose**: Answer questions using only the model's parametric knowledge.

```text
Ты — помощник, отвечающий на вопросы по курсам Big Data и Machine Learning.

Инструкции:
- Отвечай на русском языке, если вопрос задан на русском.
- Если не знаешь точного ответа, честно скажи об этом.
- Будь кратким и конкретным (2-4 абзаца максимум).
- Не выдумывай факты и не галлюцинируй.

Вопрос:
{question}
```

**Variables**:
- `{question}` — user query from `queries.jsonl`

---

### 1.2 RAG Mode (With Retrieved Context)

**Purpose**: Answer questions using retrieved document chunks as context.

```text
Ты — помощник, отвечающий на вопросы по курсам Big Data и Machine Learning.

Инструкции:
- Используй ТОЛЬКО информацию из предоставленного контекста для ответа.
- Если в контексте нет ответа, скажи: "В предоставленных документах информация не найдена."
- Отвечай на русском языке, если вопрос задан на русском.
- Будь кратким и конкретным (2-4 абзаца максимум).
- Если можешь, укажи источник информации (например, "Согласно документу X...").

Контекст (релевантные фрагменты документов):

{context}

---

Вопрос:
{question}
```

**Variables**:
- `{context}` — concatenated retrieved chunks with metadata
- `{question}` — user query from `queries.jsonl`

---

## 2. Context Formatting

### 2.1 Chunk Template

Each retrieved chunk formatted as:

```text
[Фрагмент {ordinal + 1} | Релевантность: {score:.2f}]
Источник: {source_path}
Теги: {tags}

{chunk_text}

---
```

**Example**:

```text
[Фрагмент 1 | Релевантность: 0.87]
Источник: /workspace/docs/specs/architecture.md
Теги: source=docs, language=ru

Clean Architecture предусматривает четыре слоя:
- Domain (чистая бизнес-логика, без зависимостей)
- Application (use cases, оркестрация)
- Infrastructure (адаптеры для БД, API)
- Presentation (CLI, API, боты)

---
```

### 2.2 Multiple Chunks Assembly

When multiple chunks are retrieved (default `top_k=5`):

```text
{chunk_1}

{chunk_2}

{chunk_3}

...
```

**Token Budget**:
- Reserve ~1000 tokens for question + system prompt
- Reserve ~1000 tokens for answer generation
- Allocate remaining ~3000 tokens for context (configurable via `max_context_tokens`)

---

## 3. Prompt Assembly Pseudocode

### 3.1 Non-RAG Mode

```python
def build_non_rag_prompt(question: str) -> str:
    system_prompt = SYSTEM_PROMPT_NON_RAG
    return system_prompt.format(question=question)
```

### 3.2 RAG Mode

```python
def build_rag_prompt(
    question: str,
    chunks: List[RetrievedChunk],
    max_context_tokens: int = 3000,
) -> str:
    context_parts = []
    total_tokens = 0

    for idx, chunk in enumerate(chunks):
        formatted_chunk = CHUNK_TEMPLATE.format(
            ordinal=idx,
            score=chunk.similarity_score,
            source_path=chunk.metadata.get("source_path", "unknown"),
            tags=", ".join(f"{k}={v}" for k, v in chunk.metadata.items()),
            chunk_text=chunk.text,
        )

        chunk_tokens = estimate_tokens(formatted_chunk)
        if total_tokens + chunk_tokens > max_context_tokens:
            break  # Stop adding chunks to avoid overflow

        context_parts.append(formatted_chunk)
        total_tokens += chunk_tokens

    context = "\n".join(context_parts)
    system_prompt = SYSTEM_PROMPT_RAG
    return system_prompt.format(context=context, question=question)
```

---

## 4. Output Format

### 4.1 Single Comparison Result (JSON)

```json
{
  "id": "arch_001",
  "question": "Какие слои предусмотрены Clean Architecture?",
  "mode": "comparison",
  "without_rag": {
    "answer": "Clean Architecture включает четыре основных слоя...",
    "latency_ms": 1234,
    "model": "qwen",
    "tokens_generated": 150
  },
  "with_rag": {
    "answer": "Согласно architecture.md, Clean Architecture предусматривает...",
    "latency_ms": 2345,
    "model": "qwen",
    "tokens_generated": 180,
    "chunks_used": 3,
    "chunks_metadata": [
      {
        "chunk_id": "chunk-abc-0",
        "source": "docs/specs/architecture.md",
        "similarity_score": 0.87
      },
      {
        "chunk_id": "chunk-def-1",
        "source": "docs/specs/architecture.md",
        "similarity_score": 0.75
      },
      {
        "chunk_id": "chunk-ghi-2",
        "source": "docs/README.md",
        "similarity_score": 0.68
      }
    ]
  },
  "timestamp": "2025-11-11T12:34:56Z"
}
```

### 4.2 Batch Results (JSONL)

Each line contains one comparison result in the format above.

---

## 5. Evaluation Rubric (Simplified for MVP)

### 5.1 Manual Evaluation Dimensions

For each query, human evaluator compares both answers on:

| Dimension | Scale | Description |
|-----------|-------|-------------|
| **Correctness** | 1-5 | Is the answer factually correct? |
| **Completeness** | 1-5 | Does it address all parts of the question? |
| **Relevance** | 1-5 | Is the answer focused on the question? |
| **Clarity** | 1-5 | Is the answer easy to understand? |
| **Source Accuracy** (RAG only) | 1-5 | Does RAG cite correct sources? |

### 5.2 Winner Label

```text
- "rag_better": RAG answer is superior
- "non_rag_better": Non-RAG answer is superior
- "tie": Both answers are comparable
- "both_poor": Neither answer is satisfactory
```

### 5.3 Manual Review Template (Stage 20_04)

```markdown
## Query: {id}

**Question**: {question}

### Non-RAG Answer
{without_rag.answer}

**Evaluation**:
- Correctness: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5
- Completeness: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5
- Relevance: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5
- Clarity: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5

### RAG Answer
{with_rag.answer}

**Evaluation**:
- Correctness: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5
- Completeness: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5
- Relevance: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5
- Clarity: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5
- Source Accuracy: [ ] 1 [ ] 2 [ ] 3 [ ] 4 [ ] 5

**Winner**: [ ] rag_better [ ] non_rag_better [ ] tie [ ] both_poor

**Notes**: (failure modes, hallucinations, wrong retrieval, etc.)
```

---

## 6. Notes

### 6.1 Language Handling

- All queries in `queries.jsonl` are in Russian (`"lang": "ru"`)
- System prompts are in Russian to match query language
- Chunking and retrieval are language-agnostic (embeddings work cross-lingually)

### 6.2 Token Estimation

Use simple heuristic for Russian text:
- 1 token ≈ 4 characters (UTF-8)
- For precision, use `tiktoken` or model-specific tokenizer

### 6.3 Future Enhancements (Post-MVP)

- LLM-as-judge automation (EP05 integration)
- Multi-lingual prompt templates (EN/RU switching)
- Citation formatting (footnotes, inline references)
- Hybrid retrieval (keyword + semantic)
- Re-ranking retrieved chunks by relevance

---

## References

- `docs/specs/epic_19/stage_19_04_runbook.md` — EP19 index configuration
- `docs/specs/epic_05/stage_05_02_runbook.md` — LLM-as-judge automation
- `retrieval_config.yaml` — RAG retrieval parameters
