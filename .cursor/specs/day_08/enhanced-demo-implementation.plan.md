<!-- 790a71aa-56a8-4c96-9bc9-bdded005c525 14ba13d2-7f1b-478f-8105-c6523750ba19 -->
# Enhanced Model Switching Demo with Comprehensive Testing

## Overview

Transform the demo to test each model independently with queries that significantly exceed token limits, test all compression strategies on all queries (short/medium/long), display detailed outputs including query content and model responses, and add human-readable pacing with delays.

## Implementation Steps

### 1. Update Configuration for Larger Queries

**File:** `day_08/config/demo_config.py`

Update token stages to generate much larger queries that exceed model limits:

```python
# Replace token_stages configuration
"token_stages": {
    "short": {"min": 500, "max": 1000},      # Still within limits but substantial
    "medium": {"min": 5000, "max": 8000},    # Exceeds StarCoder, within Mistral
    "long": {"min": 15000, "max": 25000}     # Exceeds all current models
},
```

Add all models to the configuration:

```python
"models": ["starcoder", "mistral", "qwen", "tinyllama"],
```

Add demo display configuration:

```python
"demo_display": {
    "step_delay": 2.0,              # Delay between major steps in seconds
    "show_query_preview": 200,      # Characters of query to show
    "show_response_preview": 500,   # Characters of response to show
    "show_full_compression": True,  # Show all compression details
    "pause_between_models": 3.0,    # Delay when switching models
    "verbose_output": True          # Show all details
}
```

### 2. Enhance Token Limit Tester for Larger Queries

**File:** `day_08/core/token_limit_tester.py`

Update query generation methods to create much larger queries:

In `generate_short_query()` around line 150:

- Expand the query template with more detailed requirements
- Add multiple examples and edge cases
- Target 500-1000 tokens

In `generate_medium_query()` around line 180:

- Add comprehensive architecture descriptions
- Include detailed implementation requirements
- Add multiple code examples
- Target 5000-8000 tokens

In `generate_long_query()` around line 210:

- Create extensive multi-component system description
- Include detailed requirements for all CRUD operations
- Add authentication, authorization, caching, testing requirements
- Include deployment and monitoring specifications
- Target 15000-25000 tokens

### 3. Create Enhanced Demo Script

**File:** `day_08/demo_enhanced.py` (new file)

Create a new comprehensive demo script:

```python
import asyncio
import time
from typing import Any, Dict
from demo_model_switching import ModelSwitchingDemo
from config.demo_config import get_config

class EnhancedModelSwitchingDemo(ModelSwitchingDemo):
    """Enhanced demo with detailed output and human-readable pacing."""
    
    async def run_enhanced_demo(self) -> Dict[str, Any]:
        """Run enhanced demo with detailed output."""
        config = get_config()
        display_config = config.get("demo_display", {})
        
        print("=" * 80)
        print("ENHANCED MODEL SWITCHING DEMO")
        print("Testing models with large queries exceeding token limits")
        print("=" * 80)
        
        await self._pause("Initializing...", 1.0)
        
        # Check ALL models availability
        await self._check_all_models_with_details()
        
        # Test each model independently
        for model_name in self.config["models"]:
            await self._test_model_enhanced(model_name)
            await self._pause(f"Completed testing {model_name}", 
                            display_config.get("pause_between_models", 3.0))
        
        # Generate comprehensive summary
        self._generate_enhanced_summary()
        
        return self.results
    
    async def _pause(self, message: str, seconds: float):
        """Add human-readable pause."""
        print(f"\n{message}")
        print(f"⏳ Pausing for {seconds}s...")
        await asyncio.sleep(seconds)
    
    async def _test_model_enhanced(self, model_name: str):
        """Test model with detailed output and compression on all queries."""
        print(f"\n{'='*80}")
        print(f"MODEL: {model_name.upper()}")
        print(f"{'='*80}")
        
        # Show model configuration
        model_config = get_model_config(model_name)
        print(f"Max Tokens: {model_config.get('max_tokens', 'Unknown')}")
        print(f"Recommended Input: {model_config.get('recommended_input', 'Unknown')}")
        
        await self._pause("Switching to model...", 1.0)
        
        # Switch to model
        success = await self.orchestrator.switch_to_model(model_name)
        if not success:
            print(f"❌ Failed to switch to {model_name}")
            return
        
        # Run three-stage tests with detailed output
        await self._run_three_stage_detailed(model_name)
        
        # Test compression on ALL queries
        await self._test_all_compressions_detailed(model_name)
    
    async def _run_three_stage_detailed(self, model_name: str):
        """Run three-stage test with detailed query and response output."""
        print(f"\n📊 THREE-STAGE TOKEN LIMIT TESTING")
        print("-" * 80)
        
        result = await self.token_tester.run_three_stage_test(model_name)
        
        for stage in ["short", "medium", "long"]:
            await self._show_stage_details(stage, result, model_name)
            await self._pause(f"Completed {stage} stage", 1.5)
    
    async def _show_stage_details(self, stage: str, result, model_name: str):
        """Show detailed information for each stage."""
        print(f"\n🔍 {stage.upper()} QUERY TEST")
        
        query = getattr(result, f"{stage}_query")
        tokens = getattr(result, f"{stage}_query_tokens")
        exceeds = getattr(result, f"{stage}_exceeds_limit")
        
        print(f"Token Count: {tokens}")
        print(f"Exceeds Limit: {'YES' if exceeds else 'NO'}")
        print(f"\nQuery Preview (first 200 chars):")
        print(f"{query[:200]}...")
        print(f"\nFull query length: {len(query)} characters")
    
    async def _test_all_compressions_detailed(self, model_name: str):
        """Test all compression strategies on all queries with detailed output."""
        print(f"\n🗜️  COMPRESSION TESTING ON ALL QUERIES")
        print("-" * 80)
        
        result = self.results["three_stage_results"][model_name]
        
        for stage in ["short", "medium", "long"]:
            query = getattr(result, f"{stage}_query")
            print(f"\n📦 Testing compressions on {stage.upper()} query")
            
            # Test all 5 compression strategies
            for strategy in ["truncation", "keywords", "extractive", "semantic", "summarization"]:
                await self._test_single_compression_detailed(query, model_name, strategy, stage)
                await self._pause(f"Completed {strategy} compression", 1.0)
    
    async def _test_single_compression_detailed(self, query: str, model_name: str, 
                                               strategy: str, stage: str):
        """Test single compression with full output."""
        print(f"\n  Strategy: {strategy}")
        
        # Perform compression
        compression_result = await self.compression_evaluator.compress_and_test(
            query, model_name, strategy
        )
        
        if compression_result.success:
            print(f"  ✅ Success")
            print(f"  Original tokens: {compression_result.original_tokens}")
            print(f"  Compressed tokens: {compression_result.compressed_tokens}")
            print(f"  Compression ratio: {compression_result.compression_ratio:.2%}")
            print(f"  Response time: {compression_result.response_time:.2f}s")
            
            print(f"\n  Compressed query preview:")
            print(f"  {compression_result.compressed_query[:200]}...")
            
            print(f"\n  Model response preview:")
            print(f"  {compression_result.response[:500]}...")
        else:
            print(f"  ❌ Failed: {compression_result.error_message}")
```

### 4. Add Make Target for Enhanced Demo

**File:** `day_08/Makefile`

Add new target after `demo-working`:

```makefile
demo-enhanced:
	@echo "Running enhanced comprehensive demo..."
	@if [ ! -f "demo_enhanced.py" ]; then \
		echo "❌ demo_enhanced.py not found!"; \
		exit 1; \
	fi
	@echo "🚀 Enhanced Demo - Comprehensive Testing with Large Queries"
	@echo "This demo tests all models with queries exceeding limits"
	@echo "Tests all compression strategies with detailed output"
	poetry run python demo_enhanced.py
```

Update help section to include:

```makefile
@echo "  demo-enhanced  Run comprehensive demo with large queries and all compressions"
```

### 5. Update Sequential Container Management

**File:** `day_08/core/model_switcher.py`

Ensure `switch_to_model()` properly stops previous container before starting next around line 290:

Already implemented correctly - stops previous model container if `use_container_management` is enabled and current_model is different.

### 6. Add Compression Testing Method

**File:** `day_08/core/compression_evaluator.py`

Add method to test single compression strategy (if not exists):

```python
async def compress_and_test(self, query: str, model_name: str, 
                            strategy: str) -> CompressionTestResult:
    """Test single compression strategy and return detailed results."""
    try:
        # Compress the text
        compressed = await self.text_compressor.compress_text(
            query, strategy=strategy, target_tokens=2000
        )
        
        # Make request with compressed text
        response = await self.model_client.make_request(
            model_name=model_name,
            prompt=compressed.compressed_text,
            max_tokens=1000
        )
        
        return CompressionTestResult(
            strategy=strategy,
            original_query=query,
            compressed_query=compressed.compressed_text,
            original_tokens=compressed.original_tokens,
            compressed_tokens=compressed.compressed_tokens,
            compression_ratio=compressed.compression_ratio,
            response=response.response,
            response_tokens=response.total_tokens,
            response_time=response.response_time,
            success=True
        )
    except Exception as e:
        return CompressionTestResult(
            strategy=strategy,
            original_query=query,
            compressed_query="",
            original_tokens=0,
            compressed_tokens=0,
            compression_ratio=0,
            response="",
            response_tokens=0,
            response_time=0,
            success=False,
            error_message=str(e)
        )
```

### 7. Testing

Run the enhanced demo:

```bash
cd day_08
make demo-enhanced
```

Verify:

- All models (starcoder, mistral, qwen, tinyllama) are tested independently
- Previous model container stops before next starts
- Large queries (15K-25K tokens) are generated
- All 5 compression strategies tested on all 3 query sizes (15 tests per model)
- Detailed output shows query previews, compression ratios, and response previews
- Human-readable pacing with 1-3 second delays between steps
- Total runtime approximately 10-15 minutes for comprehensive testing

## Summary

This implementation creates a production-quality comprehensive demo that:

1. Tests each model independently (sequential container management)
2. Uses large queries that significantly exceed model limits (up to 25K tokens)
3. Tests ALL 5 compression strategies on ALL 3 query sizes (15 compressions per model)
4. Shows detailed output including query content, compression details, and model responses
5. Provides human-readable pacing with delays between steps
6. Generates comprehensive reports with all test results