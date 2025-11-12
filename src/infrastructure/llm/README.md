# LLM Infrastructure Module

This module provides infrastructure for Language Model (LLM) operations including summarization, evaluation, chunking, and prompt management.

## Structure

```
llm/
├── clients/              # LLM client implementations
│   ├── llm_client.py     # Base LLM client interface
│   └── resilient_client.py  # Resilient client with retry logic
├── evaluation/           # Quality assessment (LLM-as-Judge)
│   ├── summarization_evaluator.py  # Summarization quality evaluation
│   └── prompts/          # Evaluation prompts
├── chunking/             # Text chunking strategies
│   ├── semantic_chunker.py  # Semantic-aware chunking
│   └── chunk_strategy.py    # Chunking interface
├── summarizers/          # Summarization strategies
│   ├── map_reduce_summarizer.py  # Map-reduce for long texts
│   ├── adaptive_summarizer.py    # Adaptive single-pass
│   └── llm_summarizer.py         # Base LLM summarizer
└── prompts/              # Prompt builders and templates
    ├── summarization_prompts.py  # Summarization prompts
    ├── evaluation_prompts.py     # Evaluation prompts
    └── prompt_builder.py         # Prompt construction utilities
```

## Key Components

### Summarization Strategies

- **Map-Reduce**: For texts >4000 tokens, uses hierarchical summarization
- **Adaptive**: For medium texts (1000-4000 tokens), single-pass with optimized prompts
- **LLM Summarizer**: Base implementation for simple summarization

### Quality Assessment (LLM-as-Judge)

Automatic evaluation of summarization quality using LLM:
- **Coverage**: Information completeness
- **Accuracy**: Factual correctness
- **Coherence**: Logical flow
- **Informativeness**: Usefulness

### Semantic Chunking

Smart text splitting that preserves semantic boundaries:
- Avoids splitting sentences/paragraphs
- Maintains context across chunks
- Configurable chunk size and overlap

## Usage Examples

### Summarization

```python
from src.infrastructure.llm.summarizers.adaptive_summarizer import AdaptiveSummarizer
from src.infrastructure.llm.clients.resilient_client import ResilientLLMClient

client = ResilientLLMClient()
summarizer = AdaptiveSummarizer(client=client)

summary = await summarizer.summarize(
    text="Long text here...",
    max_tokens=500
)
```

### Quality Evaluation

```python
from src.infrastructure.llm.evaluation.summarization_evaluator import SummarizationEvaluator

evaluator = SummarizationEvaluator(client=client)
evaluation = await evaluator.evaluate(
    original_text="Original text...",
    summary="Summary text...",
    model="mistral"
)
```

### Semantic Chunking

```python
from src.infrastructure.llm.chunking.semantic_chunker import SemanticChunker

chunker = SemanticChunker(
    max_chunk_size=2000,
    overlap=200
)
chunks = chunker.chunk("Long text to split...")
```

## Related Documentation

- [Summarization Architecture](../../../docs/architecture/SUMMARIZATION_CURRENT_STATE.md)
- [Quality Assessment Guide](../../../docs/day15/README.md#quality-assessment)
- [Fine-tuning Documentation](../../finetuning/README.md)
