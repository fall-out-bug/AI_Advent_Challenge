<!-- 83622742-1085-48fc-9b56-66d6eb2469a5 102a87b0-2bfb-4d0f-ad80-c4dfceaf5df9 -->
# Fix Enhanced Demo Issues

## Overview

Fix three critical issues in the enhanced demo: sequential model execution, compression testing errors, and optimize compression testing to only run on heavy queries.

## Issues Identified

### Issue 1: All Models Starting at Once

- `check_all_models_availability()` in `model_switcher.py` line 179 starts ALL model containers
- This defeats the purpose of sequential testing
- Need to check availability without starting containers

### Issue 2: Missing `make_request` Method

- `compression_evaluator.py` line 221 calls `self.model_client.make_request()`
- `TokenAnalysisClient` doesn't have this method
- Need to add method to make actual inference requests to models

### Issue 3: Compression Testing on All Queries

- Currently tests compression on short, medium, and long queries
- Should only test on "long" queries that are heavy
- Lines 253-264 in `demo_enhanced.py` loop through all stages

## Implementation Plan

### 1. Fix Sequential Model Testing

**File: `day_08/core/model_switcher.py`**

Modify `check_all_models_availability()` to NOT start containers:

- Add parameter `start_containers: bool = False` to the method
- Only check if containers are already running, don't start them
- Let `switch_to_model()` handle starting the specific model needed

**File: `day_08/demo_model_switching.py`**

Update `_check_model_availability()` at line 179:

- Pass `start_containers=False` to avoid starting all models
- Remove logic that updates available models list
- Keep all configured models in the list

### 2. Add `make_request` Method to TokenAnalysisClient

**File: `day_08/core/ml_client.py`**

Add new method after line 433:

```python
async def make_request(
    self,
    model_name: str,
    prompt: str,
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> ModelResponse:
    """Make inference request to model via UnifiedModelClient."""
```

This method will:

- Use `UnifiedModelClient` to make actual model inference requests
- Return a `ModelResponse` object with response text, tokens, and timing
- Handle errors gracefully

**File: `day_08/models/data_models.py`**

Add new `ModelResponse` data class:

```python
@dataclass
class ModelResponse:
    response: str
    total_tokens: int
    response_time: float
    model_name: str
```

### 3. Restrict Compression Testing to Heavy Queries Only

**File: `day_08/demo_enhanced.py`**

Modify `_test_all_compressions_detailed()` at line 241:

- Remove loop through all stages
- Only test compression on "long" query
- Update display messages accordingly

**File: `day_08/demo_model_switching.py`**

Already correctly tests compression only when `long_exceeds_limit` is True (line 233)

- No changes needed for this file

### 4. Fix Unsupported Compression Strategies

**File: `day_08/core/text_compressor.py`**

Check if only "truncation" and "keywords" are implemented:

- If missing, add basic implementations for "extractive", "semantic", "summarization"
- Or update config to only use supported strategies

**File: `day_08/config/demo_config.py`**

Update compression algorithms list to only include supported ones:

```python
"compression_algorithms": ["truncation", "keywords"]
```

## Files to Modify

1. `day_08/core/model_switcher.py` - Add `start_containers` parameter
2. `day_08/core/ml_client.py` - Add `make_request` method
3. `day_08/models/data_models.py` - Add `ModelResponse` class
4. `day_08/demo_enhanced.py` - Test compression only on long queries
5. `day_08/demo_model_switching.py` - Pass `start_containers=False`
6. `day_08/config/demo_config.py` - Update compression algorithms list

## Testing Strategy

After implementation:

1. Run demo and verify only one model container runs at a time
2. Verify compression testing works without `make_request` errors
3. Verify compression only runs on long queries
4. Check logs to confirm sequential model execution

### To-dos

- [ ] Modify check_all_models_availability to not start containers by default
- [ ] Add make_request method to TokenAnalysisClient for model inference
- [ ] Add ModelResponse data class to data_models.py
- [ ] Modify demo to only test compression on long/heavy queries
- [ ] Update config to only include supported compression strategies
- [ ] Update demo files to pass start_containers=False