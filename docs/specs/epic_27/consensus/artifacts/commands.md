# Implementation Commands - Epic 27

## Setup

```bash
# Activate virtual environment
cd /home/fall_out_bug/studies/AI_Challenge
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Install tiktoken for token counting
pip install tiktoken
echo "tiktoken>=0.5.0" >> requirements.txt
```

## Stage 1: Domain Layer - Core Entities

```bash
# Create directory structure
mkdir -p src/domain/test_agent/value_objects
mkdir -p src/domain/test_agent/entities
mkdir -p tests/unit/domain/test_agent/value_objects
mkdir -p tests/unit/domain/test_agent/entities

# Run tests (should fail initially)
pytest tests/unit/domain/test_agent/value_objects/test_chunking_strategy.py -v
pytest tests/unit/domain/test_agent/entities/test_code_chunk.py -v

# After implementation, verify tests pass
pytest tests/unit/domain/test_agent/ -v --cov=src/domain/test_agent --cov-report=term-missing

# Type check
mypy src/domain/test_agent/ --strict

# Lint
black --check src/domain/test_agent/
flake8 src/domain/test_agent/
```

## Stage 2: Infrastructure Layer - Token Counting

```bash
# Create directory structure
mkdir -p src/infrastructure/test_agent/services
mkdir -p tests/unit/infrastructure/test_agent/services
mkdir -p tests/integration/infrastructure/test_agent

# Run unit tests (should fail initially)
pytest tests/unit/infrastructure/test_agent/services/test_token_counter.py -v

# After implementation, run all token counter tests
pytest tests/unit/infrastructure/test_agent/services/test_token_counter.py -v
pytest tests/integration/infrastructure/test_agent/test_token_counter_integration.py -v

# Coverage check
pytest tests/unit/infrastructure/test_agent/ tests/integration/infrastructure/test_agent/ \
  --cov=src/infrastructure/test_agent --cov-report=term-missing

# Type check
mypy src/infrastructure/test_agent/services/token_counter.py --strict

# Lint
black --check src/infrastructure/test_agent/
```

## Stage 3: Application Layer - Code Chunking

```bash
# Create directory structure
mkdir -p src/application/test_agent/services
mkdir -p tests/unit/application/test_agent/services

# Run tests (should fail initially)
pytest tests/unit/application/test_agent/services/test_code_chunker.py -v -k "function_based"

# After function-based implementation
pytest tests/unit/application/test_agent/services/test_code_chunker.py -v -k "function_based"

# After all strategies implemented
pytest tests/unit/application/test_agent/services/test_code_chunker.py -v

# Coverage check
pytest tests/unit/application/test_agent/services/ \
  --cov=src/application/test_agent/services/code_chunker --cov-report=term-missing

# Type check
mypy src/application/test_agent/services/code_chunker.py --strict

# Lint
black --check src/application/test_agent/
```

## Stage 4: Infrastructure Layer - Code Summarization

```bash
# Run unit tests (should fail initially)
pytest tests/unit/infrastructure/test_agent/services/test_code_summarizer.py -v

# After implementation
pytest tests/unit/infrastructure/test_agent/services/test_code_summarizer.py -v

# Run integration tests with real LLM
pytest tests/integration/infrastructure/test_agent/test_code_summarizer_integration.py -v

# Coverage check
pytest tests/unit/infrastructure/test_agent/services/test_code_summarizer.py \
  tests/integration/infrastructure/test_agent/test_code_summarizer_integration.py \
  --cov=src/infrastructure/test_agent/services/code_summarizer --cov-report=term-missing

# Type check
mypy src/infrastructure/test_agent/services/code_summarizer.py --strict

# Lint
black --check src/infrastructure/test_agent/services/
```

## Stage 5: Application Layer - Coverage Aggregation

```bash
# Create directory structure
mkdir -p tests/integration/application/test_agent

# Run unit tests (should fail initially)
pytest tests/unit/application/test_agent/services/test_coverage_aggregator.py -v

# After implementation
pytest tests/unit/application/test_agent/services/test_coverage_aggregator.py -v

# Run integration tests
pytest tests/integration/application/test_agent/test_coverage_aggregator_integration.py -v

# Coverage check
pytest tests/unit/application/test_agent/services/test_coverage_aggregator.py \
  tests/integration/application/test_agent/test_coverage_aggregator_integration.py \
  --cov=src/application/test_agent/services/coverage_aggregator --cov-report=term-missing

# Type check
mypy src/application/test_agent/services/coverage_aggregator.py --strict

# Lint
black --check src/application/test_agent/services/
```

## Stage 6: Application Layer - Enhanced Use Case

```bash
# Run unit tests (should fail initially)
pytest tests/unit/application/test_agent/use_cases/test_generate_tests_use_case_enhanced.py -v

# After implementation
pytest tests/unit/application/test_agent/use_cases/test_generate_tests_use_case_enhanced.py -v

# Run all Epic 27 tests
pytest tests/unit/application/test_agent/ tests/unit/domain/test_agent/ tests/unit/infrastructure/test_agent/ -v

# Verify backward compatibility - run Epic 26 tests
pytest tests/ -k "test_agent" -v

# Coverage check
pytest tests/unit/application/test_agent/use_cases/ \
  --cov=src/application/test_agent/use_cases/generate_tests_use_case --cov-report=term-missing

# Type check
mypy src/application/test_agent/use_cases/generate_tests_use_case.py --strict

# Lint
black --check src/application/test_agent/
```

## Stage 7: Integration and E2E Testing

```bash
# Create E2E scripts directory
mkdir -p scripts/e2e/epic_27

# Run integration tests
pytest tests/integration/application/test_agent/test_full_workflow.py -v

# Run E2E user simulation scripts
python scripts/e2e/epic_27/test_scenario_1_medium_module.py
python scripts/e2e/epic_27/test_scenario_2_cursor_comparison.py
python scripts/e2e/epic_27/test_scenario_3_large_package.py

# Or run all E2E scenarios together
for script in scripts/e2e/epic_27/test_scenario_*.py; do
  echo "Running $script..."
  python "$script" || echo "FAILED: $script"
done

# Type check E2E scripts
mypy scripts/e2e/epic_27/ --strict

# Lint E2E scripts
black --check scripts/e2e/epic_27/
```

## Full Test Suite

```bash
# Run all Epic 27 tests (unit + integration)
pytest tests/unit/domain/test_agent/ \
       tests/unit/application/test_agent/ \
       tests/unit/infrastructure/test_agent/ \
       tests/integration/application/test_agent/ \
       tests/integration/infrastructure/test_agent/ \
       -v --cov=src --cov-report=term-missing --cov-report=html

# Verify Epic 26 backward compatibility
pytest tests/ -k "test_agent" -v

# Check overall coverage
pytest tests/ --cov=src/domain/test_agent --cov=src/application/test_agent --cov=src/infrastructure/test_agent \
  --cov-report=term-missing --cov-report=html

# Open coverage report
firefox htmlcov/index.html  # or your preferred browser
```

## Quality Checks

```bash
# Type checking
mypy src/domain/test_agent/ --strict
mypy src/application/test_agent/ --strict
mypy src/infrastructure/test_agent/ --strict

# Linting
black --check src/
flake8 src/

# Security scan
bandit -r src/domain/test_agent/
bandit -r src/application/test_agent/
bandit -r src/infrastructure/test_agent/

# All quality checks together
black --check src/ && \
flake8 src/ && \
mypy src/domain/test_agent/ src/application/test_agent/ src/infrastructure/test_agent/ --strict && \
bandit -r src/domain/test_agent/ src/application/test_agent/ src/infrastructure/test_agent/
```

## Local Testing - Manual Verification

```bash
# Test Token Counter manually
python -c "
from src.infrastructure.test_agent.services.token_counter import TokenCounter
tc = TokenCounter()
code = 'def hello(): print(\"world\")'
print(f'Tokens: {tc.count_tokens(code)}')
"

# Test Code Chunker manually
python -c "
from src.application.test_agent.services.code_chunker import CodeChunker
from src.infrastructure.test_agent.services.token_counter import TokenCounter
from src.domain.test_agent.value_objects.chunking_strategy import ChunkingStrategy

chunker = CodeChunker(TokenCounter())
code = open('src/domain/some_module.py').read()
strategy = ChunkingStrategy('function_based')
chunks = chunker.chunk_module(code, 4000)
print(f'Chunks: {len(chunks)}')
for chunk in chunks:
    print(f'  - {chunk.location}: {len(chunk.code)} chars')
"

# Test full workflow manually
python -m src.presentation.cli test-agent generate --path src/domain/test_agent/entities/code_chunk.py

# Verify generated tests
pytest tests/generated/test_code_chunk.py -v --cov=src/domain/test_agent/entities/code_chunk
```

## User Testing Scripts (E2E with Action Simulation)

```bash
# Scenario 1: Medium-sized module
python scripts/e2e/epic_27/test_scenario_1_medium_module.py
# Expected: Tests generated, pytest passes, coverage ≥80%

# Scenario 2: Compare with Cursor-agent tests
python scripts/e2e/epic_27/test_scenario_2_cursor_comparison.py
# Expected: Local coverage comparable to Cursor coverage

# Scenario 3: Large package (multiple modules)
python scripts/e2e/epic_27/test_scenario_3_large_package.py
# Expected: All modules processed, no context errors, meaningful coverage

# Run all scenarios with detailed output
for scenario in 1 2 3; do
  echo "==== Scenario $scenario ===="
  python scripts/e2e/epic_27/test_scenario_${scenario}_*.py 2>&1 | tee logs/scenario_${scenario}.log
done
```

## Rollback Procedure

```bash
# If tests fail at any stage, rollback:

# 1. Check current git status
git status

# 2. Identify last passing commit
git log --oneline -10

# 3. Revert to last passing stage (example: after Stage 3)
git reset --hard <commit-hash-after-stage-3>

# 4. Verify Epic 26 still works
pytest tests/ -k "test_agent" -v

# 5. Document failure
echo "Stage X failed: <reason>" >> docs/specs/epic_27/rollback_log.txt

# 6. Notify team
echo "Epic 27 rollback needed" | mail -s "Epic 27 Rollback" team@example.com
```

## Deployment Verification

```bash
# After all stages complete, verify deployment readiness:

# 1. Run full test suite
make test

# 2. Check coverage
make coverage
# Verify: ≥80% coverage for Epic 27 components

# 3. Run linters
make lint

# 4. Run E2E scenarios
python scripts/e2e/epic_27/test_scenario_1_medium_module.py
python scripts/e2e/epic_27/test_scenario_2_cursor_comparison.py
python scripts/e2e/epic_27/test_scenario_3_large_package.py

# 5. Check performance (should not degrade >50% vs Epic 26)
time python -m src.presentation.cli test-agent generate --path src/domain/test_module.py

# 6. Verify Clean Architecture boundaries
python scripts/architecture_checker.py  # If available

# All checks pass? Ready to commit!
git add -A
git commit -m "feat(epic_27): Enhanced Test Agent for large modules with chunking and summarization"
```

## Continuous Monitoring

```bash
# Monitor test execution times
pytest tests/ --durations=10

# Monitor coverage trends
pytest tests/ --cov=src --cov-report=term-missing | tee coverage_report.txt

# Monitor LLM token usage (if instrumented)
grep "token_count" logs/test_agent.log | awk '{sum+=$NF} END {print "Total tokens:", sum}'
```
