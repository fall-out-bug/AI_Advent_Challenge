# Implementation Commands

## Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify pytest is installed
pytest --version
```

## Run Tests

### Unit Tests

```bash
# Run all unit tests for test agent
pytest tests/unit/domain/test_agent/ -v
pytest tests/unit/infrastructure/test_agent/ -v
pytest tests/unit/application/test_agent/ -v

# Run with coverage
pytest tests/unit/domain/test_agent/ --cov=src/domain/test_agent --cov-report=term-missing
pytest tests/unit/infrastructure/test_agent/ --cov=src/infrastructure/test_agent --cov-report=term-missing
pytest tests/unit/application/test_agent/ --cov=src/application/test_agent --cov-report=term-missing

# Run specific test file
pytest tests/unit/domain/test_agent/entities/test_code_file.py -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/presentation/cli/test_agent/ -v

# Run with coverage
pytest tests/integration/presentation/cli/test_agent/ --cov=src/presentation/cli/test_agent --cov-report=term-missing
```

### E2E Tests

```bash
# Run E2E tests (requires Qwen model running)
pytest tests/e2e/test_agent/ -v -m e2e

# Run with coverage
pytest tests/e2e/test_agent/ --cov=src --cov-report=term-missing
```

## Type Check

```bash
# Check domain layer
mypy src/domain/test_agent/ --strict

# Check infrastructure layer
mypy src/infrastructure/test_agent/ --strict

# Check application layer
mypy src/application/test_agent/ --strict

# Check presentation layer
mypy src/presentation/cli/test_agent/ --strict

# Check all test agent code
mypy src/domain/test_agent/ src/infrastructure/test_agent/ src/application/test_agent/ src/presentation/cli/test_agent/ --strict
```

## Linting

```bash
# Format code
black src/domain/test_agent/ src/infrastructure/test_agent/ src/application/test_agent/ src/presentation/cli/test_agent/

# Check formatting
black --check src/domain/test_agent/ src/infrastructure/test_agent/ src/application/test_agent/ src/presentation/cli/test_agent/

# Run linters
ruff check src/domain/test_agent/ src/infrastructure/test_agent/ src/application/test_agent/ src/presentation/cli/test_agent/
```

## Security Scan

```bash
# Run bandit security scan
bandit -r src/domain/test_agent/ src/infrastructure/test_agent/ src/application/test_agent/ src/presentation/cli/test_agent/
```

## Local Testing

### Test CLI

```bash
# Run test agent CLI
python -m src.presentation.cli.test_agent.main --file path/to/code.py

# Run with verbose output
python -m src.presentation.cli.test_agent.main --file path/to/code.py --verbose
```

### Test Individual Components

```bash
# Test domain entities
python -c "from src.domain.test_agent.entities.code_file import CodeFile; print('OK')"

# Test infrastructure adapters
python -c "from src.infrastructure.test_agent.adapters.pytest_executor import TestExecutor; print('OK')"

# Test use cases
python -c "from src.application.test_agent.use_cases.generate_tests_use_case import GenerateTestsUseCase; print('OK')"
```

## Development Workflow

### Stage 1: Domain Layer
```bash
# Run domain tests
pytest tests/unit/domain/test_agent/ -v
mypy src/domain/test_agent/ --strict
black --check src/domain/test_agent/
```

### Stage 2: Infrastructure Layer
```bash
# Run infrastructure tests
pytest tests/unit/infrastructure/test_agent/ -v
mypy src/infrastructure/test_agent/ --strict
black --check src/infrastructure/test_agent/
```

### Stage 3: Application Layer - Use Cases
```bash
# Run application use case tests
pytest tests/unit/application/test_agent/use_cases/ -v
mypy src/application/test_agent/use_cases/ --strict
black --check src/application/test_agent/use_cases/
```

### Stage 4: Application Layer - Orchestrator
```bash
# Run orchestrator tests
pytest tests/unit/application/test_agent/orchestrators/ -v
mypy src/application/test_agent/orchestrators/ --strict
black --check src/application/test_agent/orchestrators/
```

### Stage 5: Presentation Layer
```bash
# Run CLI tests
pytest tests/integration/presentation/cli/test_agent/ -v
mypy src/presentation/cli/test_agent/ --strict
black --check src/presentation/cli/test_agent/
```

## Full Test Suite

```bash
# Run all tests with coverage
pytest tests/unit/test_agent/ tests/integration/test_agent/ --cov=src --cov-report=term-missing --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Debug Logging (Iteration 3)

### Enable Debug Logging

```bash
# Enable LLM response debugging
export TEST_AGENT_DEBUG_LLM=1

# Enable test file debugging
export TEST_AGENT_DEBUG_FILE=1

# Enable generation debugging
export TEST_AGENT_DEBUG_GENERATION=1

# Run test agent with all debug flags
TEST_AGENT_DEBUG_LLM=1 TEST_AGENT_DEBUG_FILE=1 TEST_AGENT_DEBUG_GENERATION=1 \
  python -m src.presentation.cli.test_agent.main --file path/to/code.py
```

### View Debug Output

```bash
# View LLM response debug file
cat /tmp/llm_response.txt

# View test file debug output
cat /tmp/test_agent_debug.py

# View test file before cleanup
cat /tmp/test_agent_before_cleanup.py
```

### E2E Testing with Debug Logging

```bash
# Run E2E tests with debug logging enabled
TEST_AGENT_DEBUG_LLM=1 TEST_AGENT_DEBUG_FILE=1 TEST_AGENT_DEBUG_GENERATION=1 \
  pytest tests/e2e/test_agent/test_debug_generation.py -v

# Run E2E tests and check debug output
TEST_AGENT_DEBUG_LLM=1 TEST_AGENT_DEBUG_FILE=1 \
  pytest tests/e2e/test_agent/ -v && \
  echo "=== LLM Response ===" && \
  cat /tmp/llm_response.txt && \
  echo "=== Test File ===" && \
  cat /tmp/test_agent_debug.py
```

## Troubleshooting (Iteration 3)

### Check for Function Redefinitions

```bash
# Run test agent and check debug output for redefinitions
TEST_AGENT_DEBUG_FILE=1 python -m src.presentation.cli.test_agent.main --file path/to/code.py

# Check if source code section was modified
python -c "
import ast
with open('/tmp/test_agent_debug.py', 'r') as f:
    content = f.read()
    source_marker = '# Source code being tested'
    test_marker = '# Generated test cases'
    if source_marker in content and test_marker in content:
        source_part = content.split(test_marker)[0]
        source_code = source_part.split(source_marker, 1)[1] if source_marker in source_part else ''
        print('Source code section length:', len(source_code))
        print('Source code valid:', bool(ast.parse(source_code)) if source_code else False)
"
```

### Validate AST Structure

```bash
# Check AST structure of generated test file
python -c "
import ast
with open('/tmp/test_agent_debug.py', 'r') as f:
    content = f.read()
    try:
        tree = ast.parse(content)
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        test_functions = [f for f in functions if f.startswith('test_')]
        non_test_functions = [f for f in functions if not f.startswith('test_')]
        print('Test functions:', test_functions)
        print('Non-test functions:', non_test_functions)
        print('Has redefinitions:', len(non_test_functions) > 0)
    except SyntaxError as e:
        print('Syntax error:', e)
"
```
