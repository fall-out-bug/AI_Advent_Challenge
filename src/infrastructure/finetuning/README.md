# Fine-tuning Infrastructure Module

This module provides infrastructure for automatic model fine-tuning using Hugging Face Transformers.

## Overview

The fine-tuning system automatically improves models by training on high-quality samples collected from the quality assessment process.

## Architecture

```
finetuning/
├── finetuning_service.py  # Main fine-tuning orchestration
└── Docker integration    # Fine-tuning runs in Docker containers
```

## Workflow

1. **Quality Assessment**: LLM-as-Judge evaluates summarization quality
2. **Dataset Collection**: High-quality samples (>0.8 average score) are stored
3. **Threshold Check**: When 100+ samples accumulated, trigger fine-tuning
4. **Fine-tuning**: Runs in Docker container with Hugging Face Transformers
5. **Model Integration**: New model version saved and integrated

## Components

### Fine-tuning Service

The `FinetuningService` orchestrates the fine-tuning process:

```python
from src.infrastructure.finetuning.finetuning_service import FinetuningService

service = FinetuningService()
result = await service.finetune_model(
    task_type="summarization",
    dataset_path="data/finetuning_dataset.jsonl",
    base_model="mistral-7b",
    output_dir="models/mistral-7b-finetuned"
)
```

### Dataset Format

Fine-tuning datasets are stored as JSONL:

```json
{"input": "Original text...", "output": "Summary text..."}
{"input": "Another text...", "output": "Another summary..."}
```

### Supported Tasks

- **Summarization**: Text summarization fine-tuning
- **Classification**: Text classification (future)
- **Q&A**: Question-answering (future)

## Configuration

Fine-tuning settings are configured in `config/models.yml`:

```yaml
finetuning:
  enabled: true
  threshold: 100  # Minimum samples to trigger
  base_model: "mistral-7b"
  output_dir: "models/finetuned"
  batch_size: 4
  learning_rate: 2e-5
  num_epochs: 3
```

## Docker Integration

Fine-tuning runs in isolated Docker containers:

```bash
docker run -it \
  --gpus all \
  -v $(pwd)/data:/data \
  -v $(pwd)/models:/models \
  fine-tuning:latest \
  python finetune.py --task summarization
```

## Monitoring

Fine-tuning progress is tracked via:
- Prometheus metrics (`finetuning_runs_total`, `finetuning_duration_seconds`)
- Grafana dashboards (Quality Assessment Metrics)
- Logs in `logs/finetuning.log`

## Related Documentation

- [Quality Assessment & Fine-tuning Guide](../../../docs/day15/README.md)
- [Fine-tuning API](../../../docs/day15/api.md#fine-tuning-api)
- [LLM Infrastructure](../llm/README.md)

