<!-- a2e8ecd3-758b-4848-bf0f-ff3e9c264f79 f6cff12d-9f1a-4e81-b0c9-66f7a1a85495 -->
# Day 8: Token Analysis System Implementation

## Overview

Build a token counting and text compression system that:

- Counts tokens in requests and responses (simple estimation: 1.3 tokens/word)
- Demonstrates model behavior with limit-exceeding queries
- Implements text compression strategies (truncation and keyword extraction)
- Generates console-based text reports

Target model: StarCoder (8192 token limit)

## Project Structure

```
day_08/
├── core/
│   ├── __init__.py
│   ├── token_analyzer.py      # SimpleTokenCounter class
│   ├── text_compressor.py     # SimpleTextCompressor class
│   └── experiments.py          # TokenLimitExperiments class
├── models/
│   ├── __init__.py
│   └── data_models.py         # TokenInfo, ModelLimits, CompressionResult, ExperimentResult
├── utils/
│   ├── __init__.py
│   └── console_reporter.py    # ConsoleReporter class
├── tests/
│   ├── __init__.py
│   ├── test_token_analyzer.py
│   ├── test_text_compressor.py
│   └── test_experiments.py
├── main.py                     # Entry point
├── demo.py                     # Demo script
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Implementation Details

### 1. Token Analysis (core/token_analyzer.py)

Create `SimpleTokenCounter` class:

- Method `count_tokens(text, model_name)` using 1.3 tokens per word estimation
- Method `get_model_limits(model_name)` returning ModelLimits dataclass
- Method `check_limit_exceeded(text, model_name)` to validate against limits

Model limits configuration:

- starcoder: max_input=8192, max_output=2048
- mistral: max_input=32768, max_output=2048
- qwen: max_input=32768, max_output=2048
- tinyllama: max_input=2048, max_output=512

### 2. Text Compression (core/text_compressor.py)

Create `SimpleTextCompressor` class with two strategies:

**Truncation Strategy** (`compress_by_truncation`):

- Split text into sentences
- Keep first sentence + middle portion + last sentence
- Add "..." between parts
- Return CompressionResult with original/compressed tokens

**Keyword Strategy** (`compress_by_keywords`):

- Extract words longer than 4 characters
- Take first N keywords to fit token limit
- Return CompressionResult

### 3. Experiments (core/experiments.py)

Create `TokenLimitExperiments` class:

**Test query generation** (`_create_long_query`):

- Generate detailed technical query about transformers architecture
- Repeat query 3x to exceed StarCoder's 8192 token limit (~12000+ tokens)
- Include 10 detailed sections

**Experiment execution** (`run_limit_exceeded_experiment`):

1. No compression - attempt to send long query as-is
2. Truncation compression - compress using truncation strategy
3. Keyword compression - compress using keyword extraction

Each experiment should capture:

- Original vs processed query
- Token counts (input/output/total)
- Response time
- Compression metadata

### 4. Console Reporting (utils/console_reporter.py)

Create `ConsoleReporter` class with three methods:

**`print_experiment_summary`**:

- Display each experiment with name, model, timing
- Show token counts and compression status
- Format with clear separators

**`print_detailed_analysis`**:

- Calculate aggregate statistics
- Show average compression ratios
- Compare compression strategies

**`print_recommendations`**:

- Identify fastest/slowest experiments
- Highlight best compression strategy
- Provide usage recommendations

### 5. Main Entry Point (main.py)

Implement async `main()` function:

1. Initialize components (token_counter, text_compressor, model_client, reporter)
2. Check StarCoder availability using SDK's `check_availability`
3. Create TokenLimitExperiments instance
4. Run experiments with `run_limit_exceeded_experiment`
5. Generate all three report types
6. Handle errors gracefully with user-friendly messages

### 6. Data Models (models/data_models.py)

Define dataclasses:

- `TokenInfo`: count, estimated_cost, model_name
- `ModelLimits`: max_input_tokens, max_output_tokens, max_total_tokens
- `CompressionResult`: original_text, compressed_text, token counts, ratio, strategy
- `ExperimentResult`: experiment_name, queries, response, tokens, timing, compression_result

### 7. Integration

Use existing SDK:

- Import `UnifiedModelClient` from `shared.shared_package.clients.unified_client`
- Use `make_request()` method for model calls
- Leverage existing model configuration

## Dependencies

Add to requirements.txt:

```
# Existing SDK dependencies already in shared package
```

Add to pyproject.toml:

```toml
[tool.poetry.dependencies]
python = "^3.10"
# Reference shared package as dependency
```

## Testing Strategy

Create unit tests for:

- Token counting accuracy (within 10% of expected)
- Compression strategies preserve meaning
- Limit detection works correctly
- Experiment execution handles errors

Coverage target: 80%

## TODO (Future Enhancements)

- Implement accurate token counting with HuggingFace tokenizers
- Add model comparison experiments (StarCoder vs Mistral vs Qwen)
- Create visualization with matplotlib/plotly
- Build web interface with FastAPI

## Success Criteria

- Token counting works for all queries
- Both compression strategies reduce tokens below limits
- Three experiments complete successfully
- Console reports are clear and informative
- Code follows PEP8, has docstrings, and is tested

### To-dos

- [ ] Create project structure with all directories and __init__.py files
- [ ] Implement dataclasses in models/data_models.py (TokenInfo, ModelLimits, CompressionResult, ExperimentResult)
- [ ] Implement SimpleTokenCounter in core/token_analyzer.py with estimation and limit checking
- [ ] Implement SimpleTextCompressor with truncation and keyword strategies in core/text_compressor.py
- [ ] Implement TokenLimitExperiments class with long query generation and three experiment types
- [ ] Implement ConsoleReporter with summary, analysis, and recommendations methods
- [ ] Create main.py with async main function integrating all components
- [ ] Create demo.py with simple usage examples
- [ ] Write unit tests for token_analyzer, text_compressor, and experiments
- [ ] Test full workflow with StarCoder and verify reports
- [ ] Create README.md with setup instructions, usage examples, and architecture description