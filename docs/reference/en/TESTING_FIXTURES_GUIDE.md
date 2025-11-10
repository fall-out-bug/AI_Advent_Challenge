# Testing Fixtures Guide

## Overview

This guide describes the test fixtures used for the multi-pass code review system. Fixtures include both real student projects and synthetic examples.

## Fixture Structure

```
tests/fixtures/
├── student_hw1/          # Real: Docker + Spark
├── student_hw2/          # Real: Docker + Spark + Airflow
├── student_hw3/          # Real: Docker + Spark + Airflow + MLflow
├── docker_only/          # Synthetic: Docker only
├── airflow_only/         # Synthetic: Airflow only
├── mixed_project/        # Synthetic: All 4 components
├── large_project/        # Synthetic: Stress test (10K lines)
└── edge_cases/           # Synthetic: Error scenarios
```

## Real Student Projects

### student_hw1/ - Docker + Spark

**Source**: MLSD Homework 1 by Гаврись Александр

**Components Detected**: `docker, spark`

**Structure**:
```
student_hw1/
├── Dockerfile            # Docker image definition
├── entrypoint.sh         # Entry script
├── job.py               # Spark job (MovieLens processing)
└── run.sh               # Build and run script
```

**Detection Patterns**:
- `Dockerfile` → Docker detected
- `SparkSession` in `job.py` → Spark detected
- No `docker-compose.yml` → Single container setup

### student_hw2/ - Docker + Spark + Airflow

**Source**: MLSD Homework 2 by Гаврись Александр

**Components Detected**: `docker, spark, airflow`

**Structure**:
```
student_hw2/
├── docker-compose.yml    # Multi-service setup
├── run.sh
├── airflow/
│   └── dags/            # Airflow DAGs
├── spark/
│   ├── Dockerfile
│   └── ...
├── spark-jobs/          # Spark processing scripts
├── minio/               # Object storage
└── README.md
```

**Detection Patterns**:
- `docker-compose.yml` with `services:` → Docker Compose detected
- `airflow/dags/` directory → Airflow detected
- `spark-jobs/` directory + SparkSession usage → Spark detected
- Services: `minio`, `redis`, `airflow`, `spark-master`, `spark-worker`

**Expected DAG Tasks** (based on HW2 requirements):
- `get_dataset` - Download dataset
- `put_dataset` - Upload to Minio
- `features_engineering` - Spark processing
- `load_features` - Load to Redis

### student_hw3/ - Docker + Spark + Airflow + MLflow

**Source**: MLSD Homework 3 by Гаврись Александр

**Components Detected**: `docker, spark, airflow, mlflow`

**Structure**:
```
student_hw3/
├── docker-compose.yml
├── run.sh
├── airflow/
│   └── dags/
├── spark/
├── spark-jobs/
├── mlflow/              # MLflow tracking
│   ├── train_model.py
│   └── ...
├── minio/
└── README.md
```

**Detection Patterns**:
- All from HW2 plus:
- `mlflow/` directory → MLflow detected
- `mlflow.log_metric()` or `mlflow.log_param()` → MLflow tracking
- Service `mlflow` in docker-compose.yml

**Expected DAG Tasks** (based on HW3 requirements):
- `get_dataset`
- `put_dataset`
- `split_dataset`
- `features_engineering_train`
- `features_engineering_test`
- `load_features`
- `train_and_save_model`

## Synthetic Fixtures

### docker_only/

Simple Docker Compose setup:

```yaml
services:
  postgres: ...
  redis: ...
```

**Purpose**: Test Docker-only detection
**Expected**: `docker`

### airflow_only/

Single Airflow DAG without Docker:

```python
from airflow import DAG
with DAG(dag_id="test_dag", ...):
    ...
```

**Purpose**: Test Airflow-only detection
**Expected**: `airflow`

### mixed_project/

Complete example with all component types:

```
mixed_project/
├── docker-compose.yml    # All services
├── dags/ml_dag.py        # Airflow DAG
├── spark_jobs/train.py   # Spark job
└── mlflow/train_mlflow.py # MLflow script
```

**Purpose**: Test detection of all 4 components in one project
**Expected**: `docker,airflow,spark,mlflow`

### large_project/

100 Python files, each with 100 lines = 10,000 total lines.

**Purpose**:
- Stress test token budget limits
- Test context compression in Pass 3
- Verify system handles large codebases

**Expected**: `generic` (no specific patterns, just code)

### edge_cases/

Error scenarios:

- `empty_file.py` - Empty file
- `broken_yaml.yml` - Invalid YAML syntax
- `mixed_syntax_errors.py` - Incomplete Python with mixed imports

**Purpose**:
- Test robustness of component detection
- Verify graceful handling of syntax errors
- Ensure system doesn't crash on invalid input

**Expected**: `generic` (errors prevent specific detection)

## Using Fixtures in Tests

### Example: Unit Test

```python
import pytest
from pathlib import Path

def test_component_detection_hw2():
    """Test component detection for HW2."""
    fixture_path = Path("tests/fixtures/student_hw2")
    code = load_all_files_as_string(fixture_path)

    pass_obj = ArchitectureReviewPass(mock_client, mock_session)
    components = pass_obj._detect_components(code)

    expected_file = fixture_path / "expected_components.txt"
    expected = set(expected_file.read_text().strip().split(","))

    assert set(components) == expected
```

### Example: Integration Test

```python
@pytest.mark.asyncio
async def test_full_review_hw3():
    """Test full multi-pass review on real HW3."""
    fixture_path = Path("tests/fixtures/student_hw3")
    code = load_all_files_as_string(fixture_path)

    agent = MultiPassReviewerAgent(mock_client)
    report = await agent.process_multi_pass(code, "student_hw3")

    # Verify all components detected
    expected_file = fixture_path / "expected_components.txt"
    expected = set(expected_file.read_text().strip().split(","))
    assert set(report.detected_components) == expected

    # Verify Pass 2 ran for each component
    for component in expected:
        if component != "generic":
            assert component in report.pass_2_results

    # Verify Pass 3 completed
    assert report.pass_3 is not None
```

### Example: E2E Test

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_real_hw2():
    """E2E test with real Mistral client."""
    fixture_path = Path("tests/fixtures/student_hw2")
    code = load_all_files_as_string(fixture_path)

    client = UnifiedModelClient()  # Real client
    agent = MultiPassReviewerAgent(client)
    report = await agent.process_multi_pass(code, "student_hw2")

    assert report.pass_1 is not None
    assert len(report.detected_components) >= 2
    assert report.pass_3 is not None
    assert report.execution_time_seconds < 180  # < 3 minutes
```

## Helper Functions

### Load All Files as String

```python
from pathlib import Path

def load_all_files_as_string(directory: Path, extensions: List[str] = None) -> str:
    """Load all files from directory as single string.

    Args:
        directory: Path to fixture directory
        extensions: File extensions to include (None = all)

    Returns:
        Concatenated file contents
    """
    if extensions is None:
        extensions = [".py", ".yml", ".yaml", ".sh", ".txt", ".md"]

    content_parts = []
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if any(file_path.suffix == ext for ext in extensions):
                try:
                    content_parts.append(f"# File: {file_path.relative_to(directory)}\n")
                    content_parts.append(file_path.read_text())
                    content_parts.append("\n\n")
                except Exception as e:
                    content_parts.append(f"# Error reading {file_path}: {e}\n\n")

    return "".join(content_parts)
```

### Load Expected Components

```python
def load_expected_components(fixture_path: Path) -> List[str]:
    """Load expected components from expected_components.txt."""
    expected_file = fixture_path / "expected_components.txt"
    if expected_file.exists():
        return expected_file.read_text().strip().split(",")
    return []
```

## Validation Patterns Reference

Based on `hw_checker` validation logic:

### Docker Detection
```python
# Look for docker-compose.yml
if "docker-compose.yml" in files or "services:" in code.lower():
    components.append("docker")

# Or Dockerfile
if "Dockerfile" in files or "FROM " in code:
    components.append("docker")
```

### Airflow Detection
```python
# DAG definitions
if "DAG(" in code or "@dag" in code.lower():
    components.append("airflow")

# Directory structure
if "airflow/dags/" in files or "dags/" in files:
    components.append("airflow")
```

### Spark Detection
```python
# SparkSession usage
if "SparkSession" in code or "pyspark" in code.lower():
    components.append("spark")

# Directory structure
if "spark-jobs/" in files or "spark/" in files:
    components.append("spark")
```

### MLflow Detection
```python
# MLflow imports/usage
if "mlflow" in code.lower() or "log_metric" in code:
    components.append("mlflow")

# Directory structure
if "mlflow/" in files:
    components.append("mlflow")
```

## Maintenance

### Adding New Fixtures

1. Create new directory under `tests/fixtures/`
2. Add fixture files
3. Create `expected_components.txt` with expected detection
4. Update this guide
5. Add test cases using the fixture

### Updating Student Projects

When updating real student projects:
1. Extract new archive
2. Verify structure matches expected
3. Update `expected_components.txt` if detection changed
4. Test that existing tests still pass

## References

- `hw_checker` validation logic: `/home/fall_out_bug/msu_ai_masters/mlsd/hw_checker/`
- Assignment configs: `hw_checker/src/hw_checker/validators/assignment_configs.py`
- Validation patterns: `hw_checker/src/hw_checker/validators/common.py`
