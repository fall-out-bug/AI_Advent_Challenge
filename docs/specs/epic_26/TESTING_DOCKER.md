# Testing Test Agent in Docker

This guide explains how to test the Test Agent when it's running in a Docker container.

## Prerequisites

1. Test Agent container is running:
   ```bash
   docker ps | grep test-agent
   ```

2. LLM service is accessible (Qwen model):
   ```bash
   docker ps | grep llm
   ```

3. Sample test files are available in `docs/specs/epic_26/test_samples/`

## Quick Start

### Method 1: Direct CLI Execution (Recommended)

Execute Test Agent CLI directly in the container:

```bash
# Test with simple functions (Level 1)
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/01_simple_functions.py

# Test with calculator (Level 1)
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/02_calculator.py

# Test with shopping cart (Level 2)
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/03_shopping_cart.py

# Test with data processor (Level 3)
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/04_data_processor.py
```

**Note**: Files must be accessible inside the container. Use the mounted `workspace` volume or copy files into the container.

### Method 2: Copy Files to Container

If files are not in the mounted volume:

```bash
# Copy sample file to container
docker cp docs/specs/epic_26/test_samples/01_simple_functions.py \
  test-agent:/tmp/test_file.py

# Run Test Agent
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /tmp/test_file.py
```

### Method 3: Use Mounted Workspace

Ensure sample files are in the workspace directory:

```bash
# Copy samples to workspace (if not already there)
cp -r docs/specs/epic_26/test_samples workspace/

# Run Test Agent
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/01_simple_functions.py
```

## Verification Script

Use the automated verification script to test all samples:

```bash
# Run verification script (from host)
python scripts/verify_test_agent.py

# Or run inside container (if script is available)
docker exec test-agent python scripts/verify_test_agent.py
```

The verification script will:
1. Process all 4 sample files
2. Verify coverage ≥80% for each
3. Verify all tests pass
4. Generate a JSON report at `docs/specs/epic_26/verification_report.json`

## Testing Workflow

### Step 1: Check Container Status

```bash
# Check if container is running
docker ps | grep test-agent

# Check container logs
docker logs test-agent

# Check container health
docker inspect test-agent | grep -A 10 Health
```

### Step 2: Verify LLM Connection

```bash
# Test LLM connectivity from container
docker exec test-agent python -c "
from src.infrastructure.clients.llm_client import HTTPLLMClient
import os
client = HTTPLLMClient(base_url=os.getenv('LLM_URL', 'http://llm-api:8000'))
print('LLM client initialized')
"
```

### Step 3: Run Test on Simple File

```bash
# Start with simplest test case
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/01_simple_functions.py
```

**Expected Output:**
```
✓ Test Status: PASSED
Tests: X total, X passed, 0 failed
Coverage: XX.X%
```

### Step 4: Run All Samples

```bash
# Test all sample files
for file in 01_simple_functions.py 02_calculator.py 03_shopping_cart.py 04_data_processor.py; do
  echo "Testing $file..."
  docker exec test-agent python -m src.presentation.cli.test_agent.main \
    /app/test_samples/$file
  echo "---"
done
```

### Step 5: Verify Results

```bash
# Check generated test files (if saved to workspace)
docker exec test-agent ls -la /app/workspace/

# Check test results
docker exec test-agent find /app/workspace -name "test_*.py" -type f
```

## Advanced Testing

### Test with Verbose Output

```bash
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  --verbose \
  /app/test_samples/01_simple_functions.py
```

### Test with Custom Output Directory

```bash
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  --output-dir /app/workspace/generated_tests \
  /app/test_samples/01_simple_functions.py
```

### Interactive Shell Testing

```bash
# Open interactive shell in container
docker exec -it test-agent /bin/bash

# Inside container, run:
python -m src.presentation.cli.test_agent.main \
  /app/test_samples/01_simple_functions.py
```

## Troubleshooting

### Issue: Container Not Running

```bash
# Start container
docker-compose -f docker-compose.test-agent.yml up -d

# Check status
docker-compose -f docker-compose.test-agent.yml ps
```

### Issue: Files Not Found

```bash
# Check mounted volumes
docker inspect test-agent | grep -A 20 Mounts

# Verify workspace directory exists
docker exec test-agent ls -la /app/workspace/
```

### Issue: LLM Connection Failed

```bash
# Check LLM service
docker ps | grep llm

# Test LLM URL from container
docker exec test-agent curl -s http://llm-api:8000/health || echo "LLM not accessible"

# Check environment variables
docker exec test-agent env | grep LLM
```

### Issue: Permission Denied

```bash
# Check container user
docker exec test-agent whoami

# Check file permissions
docker exec test-agent ls -la /app/workspace/
```

## Sample Test Files

All sample files are located in `docs/specs/epic_26/test_samples/`:

1. **01_simple_functions.py** (Level 1 - Easy)
   - Simple functions: `add()`, `subtract()`
   - Expected: Basic test cases

2. **02_calculator.py** (Level 1 - Easy)
   - Calculator functions with error handling
   - Expected: Edge case tests (division by zero)

3. **03_shopping_cart.py** (Level 2 - Medium)
   - Class with multiple methods
   - Expected: Tests for all methods, edge cases

4. **04_data_processor.py** (Level 3 - Hard)
   - Complex logic with list operations
   - Expected: Edge case tests (empty lists, None values)

## Success Criteria

Test Agent is working correctly if:

- ✅ Generates valid pytest code (no syntax errors)
- ✅ Tests execute successfully
- ✅ Coverage ≥80% for each sample
- ✅ All tests pass
- ✅ Reports are generated correctly

## Expected Results

For each sample file, you should see:

```
Processing: 01_simple_functions.py...
✓ Test Status: PASSED
Tests: 5 total, 5 passed, 0 failed
Coverage: 85.5%
```

## Next Steps

After successful testing:

1. Review generated test files
2. Check coverage reports
3. Verify test quality
4. Run verification script for comprehensive validation
