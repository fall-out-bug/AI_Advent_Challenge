# Test Fixtures for Multi-Pass Code Review

This directory contains test fixtures for the multi-pass code review system.

## Structure

### Real Student Projects

#### `student_hw1/`
- **Source**: HW1 Гаврись Александр (MLSD Homework 1)
- **Components**: Docker + Spark
- **Expected**: `docker,spark`
- **Description**: Simple Docker setup with Spark job processing MovieLens dataset
- **Files**: Dockerfile, job.py, entrypoint.sh, run.sh

#### `student_hw2/`
- **Source**: HW2 Гаврись Александр (MLSD Homework 2)
- **Components**: Docker Compose + Spark + Airflow
- **Expected**: `docker,spark,airflow`
- **Description**: Feature engineering pipeline with Docker Compose, Spark jobs, Airflow DAGs
- **Structure**:
  - `docker-compose.yml` with minio, redis, airflow, spark-master, spark-worker
  - `airflow/dags/` with DAG tasks
  - `spark-jobs/` with feature engineering scripts

#### `student_hw3/`
- **Source**: HW3 Гаврись Александр (MLSD Homework 3)
- **Components**: Docker Compose + Spark + Airflow + MLflow
- **Expected**: `docker,spark,airflow,mlflow`
- **Description**: Complete ML pipeline with model training, tracking, and serving
- **Structure**:
  - All from HW2 plus
  - `mlflow/` directory with training scripts
  - MLflow model serving on port 6000

### Synthetic Fixtures

#### `docker_only/`
- **Components**: Docker only
- **Expected**: `docker`
- **Description**: Simple Docker Compose with postgres and redis services

#### `airflow_only/`
- **Components**: Airflow only
- **Expected**: `airflow`
- **Description**: Single Airflow DAG without Docker Compose

#### `mixed_project/`
- **Components**: All 4 types
- **Expected**: `docker,airflow,spark,mlflow`
- **Description**: Complete example with all component types in one project

#### `large_project/`
- **Components**: Generic
- **Expected**: `generic`
- **Description**: Large project for stress testing (100 files × 100 lines = 10K lines)
- **Purpose**: Test token budget limits and context compression

#### `edge_cases/`
- **Components**: Generic (detection should handle errors)
- **Expected**: `generic`
- **Description**: Edge cases for robustness testing:
  - `empty_file.py` - empty file
  - `broken_yaml.yml` - invalid YAML syntax
  - `mixed_syntax_errors.py` - incomplete Python code with mixed imports

## Usage in Tests

```python
from pathlib import Path

# Load fixture
fixture_path = Path("tests/fixtures/student_hw2")
code = load_all_files_as_string(fixture_path)

# Check expected components
expected_file = fixture_path / "expected_components.txt"
expected = expected_file.read_text().strip().split(",")

# Run multi-pass review
report = await agent.process_multi_pass(code, "student_hw2")
assert set(report.detected_components) == set(expected)
```

## expected_components.txt Format

Each fixture directory contains `expected_components.txt` with comma-separated list of expected component types:

```
docker,spark,airflow,mlflow
```

Valid component types:
- `docker` - Docker/Docker Compose detected
- `airflow` - Apache Airflow DAGs detected
- `spark` - Apache Spark jobs detected
- `mlflow` - MLflow tracking detected
- `generic` - No specific components detected

## Validation Patterns

Based on `hw_checker` validation logic:

### Docker Detection
- Look for `docker-compose.yml` or `Dockerfile`
- Check for service definitions (`services:` key)

### Airflow Detection
- Look for `DAG(` or `@dag` decorators
- Check for `airflow/dags/` directory
- Validate required DAG tasks exist

### Spark Detection
- Look for `SparkSession`, `pyspark` imports
- Check for `spark-jobs/` directory
- Validate Spark operations

### MLflow Detection
- Look for `mlflow` imports
- Check for `log_metric`, `log_param` calls
- Check for `mlflow/` directory
