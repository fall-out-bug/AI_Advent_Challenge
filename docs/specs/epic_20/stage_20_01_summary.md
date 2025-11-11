# Stage 20_01 Summary · Requirements & Configuration

## Status: ✅ Complete

## Deliverables

### 1. Query Set
- **File**: `queries.jsonl`
- **Count**: 17 questions
- **Categories**:
  - Architecture/Repository (3 questions)
  - MCP/CLI/Bot (2 questions)
  - Benchmarking/Fine-tuning (2 questions)
  - Indexing (1 question)
  - Lectures (7 questions: MapReduce, HDFS, CAP, Spark, Kafka, embeddings, RAG)
- **Language**: Russian (all queries)
- **Status**: ✅ Pre-existing, validated

### 2. Retrieval Configuration
- **File**: `retrieval_config.yaml`
- **Key Parameters**:
  - `top_k`: 5 chunks
  - `score_threshold`: 0.3
  - `max_context_tokens`: 3000
  - `embedding_model`: all-MiniLM-L6-v2 (from EP19)
  - `embedding_dimension`: 384
- **Index Settings**:
  - MongoDB: `document_index` database
  - Redis: `embedding:index:v1` namespace
  - FAISS fallback: `var/indices/embedding_index_v1.pkl`
- **Status**: ✅ Created

### 3. Prompt Templates
- **File**: `prompt_templates.md`
- **Templates Defined**:
  - **Non-RAG System Prompt**: Baseline mode (parametric knowledge only)
  - **RAG System Prompt**: Context-augmented mode (retrieved chunks + question)
  - **Chunk Formatting**: Ordinal, similarity score, source path, tags, text
  - **Output Format**: JSON schema for single/batch comparison results
- **Language**: Russian (matches query language)
- **Status**: ✅ Created

### 4. Evaluation Rubric (Simplified for MVP)
- **Type**: Manual human evaluation (no LLM-as-judge in MVP)
- **Dimensions**:
  - Correctness (1-5)
  - Completeness (1-5)
  - Relevance (1-5)
  - Clarity (1-5)
  - Source Accuracy (1-5, RAG only)
- **Winner Labels**: `rag_better`, `non_rag_better`, `tie`, `both_poor`
- **Template**: Markdown checklist for Stage 20_04 manual review
- **Status**: ✅ Documented in `prompt_templates.md`

## Assumptions & Constraints

### Confirmed Assumptions
1. **EP19 Index**: Build minimal index for demo (docs + mlsd/bigdata lectures)
2. **Shared Infrastructure**: MongoDB, Redis, LLM API at `http://127.0.0.1:8000`
3. **LLM Model**: Qwen (from shared infra)
4. **Language**: Russian for all prompts/queries
5. **Context Window**: ~5000 tokens total (3000 for context, 1000 for question/system, 1000 for answer)

### Constraints
1. **Token Limits**: Max 3000 tokens for retrieved context (configurable)
2. **Top-K**: Default 5 chunks (adjustable based on token budget)
3. **Score Threshold**: 0.3 (permissive to avoid empty retrievals)
4. **Fallback**: Automatic fallback to non-RAG if index unavailable
5. **No LLM-as-judge in MVP**: Manual evaluation only

## Dependencies Identified

### External Dependencies
- ✅ EP19 index (to be built in parallel task)
- ✅ Shared infra (MongoDB, Redis, LLM API) — per `operations.md`
- ✅ `all-MiniLM-L6-v2` embedding model endpoint

### Internal Dependencies
- Retrieval adapter (Stage 20_02)
- Prompt assembly logic (Stage 20_02)
- CLI commands (Stage 20_03)
- Comparison use case (Stage 20_03)

## Configuration Validation

### ✅ Retrieval Config Alignment with EP19
| Parameter | EP19 Default | EP20 Config | Notes |
|-----------|--------------|-------------|-------|
| Chunk size | 1200 tokens | 1200 tokens | ✅ Match |
| Chunk overlap | 200 tokens | 200 tokens | ✅ Match |
| Min chunk | 200 tokens | 200 tokens | ✅ Match |
| Embedding model | all-MiniLM-L6-v2 | all-MiniLM-L6-v2 | ✅ Match |
| Dimension | 384 | 384 | ✅ Match |
| Batch size | 32 | N/A (retrieval only) | ✅ OK |

### ✅ Prompt Template Validation
- [x] Russian language support
- [x] Explicit instruction to avoid hallucination
- [x] Context overflow protection (token budget)
- [x] Source citation encouraged in RAG mode
- [x] Clear differentiation between modes

## Open Questions (Resolved)

1. **Q**: LLM-as-judge required in MVP?
   **A**: No, manual evaluation in Stage 20_04, LLM-as-judge optional post-MVP.

2. **Q**: CLI commands in English or Russian?
   **A**: English (project convention), queries in Russian.

3. **Q**: EP19 index ready?
   **A**: No, build minimal index for demo (parallel task tracked in TODO).

4. **Q**: Fallback behavior if Redis unavailable?
   **A**: Use FAISS file store (`var/indices/embedding_index_v1.pkl`), per EP19 runbook.

5. **Q**: Evaluation rubric format?
   **A**: Markdown checklist for manual review (Stage 20_04).

## Next Steps → Stage 20_02

### Ready to Proceed
- [x] Query set validated
- [x] Retrieval parameters defined
- [x] Prompt templates documented
- [x] Evaluation rubric specified
- [x] Configuration files created

### Stage 20_02 Tasks
1. Design retrieval adapter (integrate with EP19 index)
2. Implement prompt assembly logic
3. Create prototype script `scripts/rag/compare_once.py`
4. Write design document with component diagram
5. Validate prototype on sample query

## Sign-off

**Stakeholder**: Tech Lead (self)
**Date**: 2025-11-11
**Status**: ✅ Approved

**Comments**:
- Configuration aligns with EP19 settings
- Prompts follow project conventions (Russian for content, English for commands)
- Evaluation rubric appropriate for MVP (manual review, LLM-as-judge deferred)
- Ready to proceed with Stage 20_02 design and prototyping
