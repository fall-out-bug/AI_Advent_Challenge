<!-- ee9dd864-effe-413c-b00a-73bae1e5400e e20b07a9-1044-47a7-bf8c-c040fa3bf1f9 -->
# Improve Enhanced Demo Output and Logging

## Overview

Enhance the demo to show both code generator and reviewer agent outputs, and reduce log noise by setting WARNING as default log level.

## Changes Required

### 1. Set Default Log Level to WARNING

**File**: `day_08/utils/logging.py`

Update the `LoggerFactory` methods to default to WARNING instead of INFO:

```python
# Line 209
def create_logger(
    name: str, level: str = "WARNING", format_type: str = "json"
) -> StructuredLogger:

# Line 216
def create_request_logger(
    name: str, level: str = "WARNING", format_type: str = "json"
) -> RequestLogger:

# Line 223
def setup_root_logger(level: str = "WARNING", format_type: str = "json") -> None:
```

**File**: `day_08/config/settings.py`

Update the default LOG_LEVEL from INFO to WARNING:

```python
# Line 25
self.log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
```

### 2. Display Generator Agent Output

**File**: `day_08/demo_enhanced.py`

Add method to display generator output after compression tests (around line 331):

```python
async def _display_generator_output(self, result, stage: str) -> None:
    """Display code generator agent output."""
    print(f"\n  🤖 GENERATOR OUTPUT:")
    response_preview = self.display_config.get("show_response_preview", 500)
    print(f"  Generated code (first {response_preview} chars):")
    print(f"  {result.response[:response_preview]}...")
    if len(result.response) > response_preview:
        print(f"  (Total length: {len(result.response)} characters)")
```

### 3. Display Reviewer Agent Output

**File**: `day_08/demo_enhanced.py`

Add method to display reviewer analysis after generator output (around line 340):

```python
async def _display_reviewer_output(self, code: str, query: str, model: str, strategy: str) -> None:
    """Display code reviewer agent analysis."""
    print(f"\n  🔍 REVIEWER ANALYSIS:")
    
    try:
        quality = await self.reviewer_adapter.review_code_quality(
            code, query, strategy
        )
        
        if quality:
            print(f"  Code Quality Score: {quality.get('quality_score', 'N/A')}")
            print(f"  Completeness: {quality.get('completeness', 'N/A')}")
            print(f"  Correctness: {quality.get('correctness', 'N/A')}")
            print(f"  Best Practices: {quality.get('best_practices', 'N/A')}")
            
            if 'issues' in quality and quality['issues']:
                print(f"  Issues Found: {len(quality['issues'])}")
                for issue in quality['issues'][:3]:  # Show first 3 issues
                    print(f"    - {issue}")
        else:
            print(f"  Reviewer not available")
    except Exception as e:
        print(f"  Error getting review: {str(e)}")
```

### 4. Integrate Agent Outputs in Compression Testing

**File**: `day_08/demo_enhanced.py`

Update `_test_single_compression_detailed` method (around line 316) to call the new display methods:

```python
# After line 316 (Model response preview)
print(f"  {compression_result.response[:response_preview_length]}...")

# Add these calls:
await self._display_generator_output(compression_result, stage)
await self._display_reviewer_output(
    compression_result.response, 
    query, 
    model_name, 
    strategy
)
```

### 5. Update Demo Description

**File**: `day_08/demo_enhanced.py`

Update the intro text (around line 440) to reflect the new features:

```python
print("4. Show detailed output with query, response, and agent analysis")
print("5. Display both generator and reviewer agent outputs")
print("6. Provide human-readable pacing with delays")
print("7. Generate comprehensive reports")
```

## Testing

Run the enhanced demo to verify:

- Log output shows only WARNING level and above
- Generator agent output is displayed for each compression test
- Reviewer agent analysis is shown with quality metrics
- Output is clear and well-formatted
```bash
cd day_08
make demo-enhanced
```


## Expected Outcome

The demo will now:

1. Show cleaner logs (WARNING level only)
2. Display generated code from the generator agent
3. Show quality analysis and metrics from the reviewer agent
4. Provide comprehensive feedback on both code generation and review

### To-dos

- [ ] Update default log level to WARNING in logging utilities and config
- [ ] Create method to display generator agent output with formatted code preview
- [ ] Create method to display reviewer agent analysis with quality metrics
- [ ] Integrate agent output displays into compression testing flow
- [ ] Update demo introduction text to reflect new features
- [ ] Run demo and verify agent outputs and logging levels work correctly