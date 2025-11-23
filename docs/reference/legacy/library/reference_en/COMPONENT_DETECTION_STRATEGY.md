# Component Detection Strategy

## Overview

This document describes the strategy for detecting technology components (Docker, Airflow, Spark, MLflow) in student projects for the multi-pass code review system.

## Detection Philosophy

Based on analysis of `hw_checker` validation patterns and real student projects:

1. **Multi-layered Detection**: Combine file structure, code patterns, and configuration files
2. **False Positive Tolerance**: Better to detect too many than miss components
3. **Graceful Degradation**: Handle edge cases (broken files, mixed formats) gracefully
4. **Pattern-based**: Use regex and keyword matching as primary detection method

## Detection Patterns

### Docker Detection

**Primary Indicators**:
- File: `docker-compose.yml` or `Dockerfile`
- Content: `services:` key (docker-compose)
- Content: `FROM ` directive (Dockerfile)

**Confidence Levels**:
- **High**: `docker-compose.yml` exists with `services:` section
- **Medium**: `Dockerfile` exists
- **Low**: Only `FROM` keyword in code comments

**Implementation**:
```python
def _detect_docker(code: str, files: List[str]) -> bool:
    # Check for docker-compose.yml
    if "docker-compose.yml" in files or "docker-compose.yaml" in files:
        return True

    # Check for Dockerfile
    if "Dockerfile" in files:
        return True

    # Check content patterns
    if "services:" in code.lower() or "FROM " in code:
        return True

    return False
```

**Validation Patterns** (from hw_checker):
- HW2/HW3 require `docker-compose.yml` with specific services:
  - `minio`, `redis`, `airflow`, `spark-master`, `spark-worker`
  - Alternative service names allowed: `airflow-webserver`/`airflow-scheduler`

### Airflow Detection

**Primary Indicators**:
- File: `airflow/dags/` directory
- Content: `DAG(` or `@dag` decorator
- Content: `from airflow import DAG`

**Confidence Levels**:
- **High**: `airflow/dags/` directory exists + DAG definition in code
- **Medium**: DAG definition found in code
- **Low**: Only `airflow` keyword in comments/imports

**Implementation**:
```python
def _detect_airflow(code: str, files: List[str]) -> bool:
    # Check directory structure
    if any("airflow/dags" in f or "/dags/" in f for f in files):
        return True

    # Check for DAG definitions
    if "DAG(" in code or "@dag" in code.lower():
        return True

    # Check imports
    if "from airflow import DAG" in code or "from airflow" in code:
        return True

    return False
```

**Validation Patterns** (from hw_checker):
- HW2 requires DAG tasks: `get_dataset`, `put_dataset`, `features_engineering`, `load_features`
- HW3 requires additional: `split_dataset`, `features_engineering_train`, `features_engineering_test`, `train_and_save_model`

### Spark Detection

**Primary Indicators**:
- File: `spark-jobs/` or `spark/` directory
- Content: `SparkSession` usage
- Content: `pyspark` imports

**Confidence Levels**:
- **High**: `spark-jobs/` directory + `SparkSession` in code
- **Medium**: `SparkSession` or `pyspark` imports found
- **Low**: Only `spark` keyword in comments

**Implementation**:
```python
def _detect_spark(code: str, files: List[str]) -> bool:
    # Check directory structure
    if any("spark-jobs" in f or "/spark/" in f for f in files):
        return True

    # Check for SparkSession
    if "SparkSession" in code or "spark." in code:
        return True

    # Check imports
    if "from pyspark" in code or "import pyspark" in code:
        return True

    return False
```

**Validation Patterns** (from hw_checker):
- HW1: Simple Spark job processing MovieLens dataset
- HW2/HW3: Feature engineering with Spark jobs in `spark-jobs/` directory

### MLflow Detection

**Primary Indicators**:
- File: `mlflow/` directory
- Content: `mlflow.log_metric()` or `mlflow.log_param()` calls
- Content: `import mlflow`

**Confidence Levels**:
- **High**: `mlflow/` directory + MLflow API calls
- **Medium**: MLflow API calls found (`log_metric`, `log_param`, `start_run`)
- **Low**: Only `mlflow` keyword in comments

**Implementation**:
```python
def _detect_mlflow(code: str, files: List[str]) -> bool:
    # Check directory structure
    if any("mlflow" in f.lower() for f in files):
        return True

    # Check for MLflow API calls
    mlflow_patterns = [
        "mlflow.log_metric",
        "mlflow.log_param",
        "mlflow.start_run",
        "mlflow.log_model",
    ]
    if any(pattern in code for pattern in mlflow_patterns):
        return True

    # Check imports
    if "import mlflow" in code or "from mlflow" in code:
        return True

    return False
```

**Validation Patterns** (from hw_checker):
- HW3 requires MLflow service in docker-compose.yml
- MLflow serving on port 6000 for inference
- Metrics tracked: `accuracy`, `roc_auc`, `precision`, `recall`, `f1_score`

## Detection Algorithm

### Current Implementation (ArchitectureReviewPass)

```python
def _detect_components(self, code: str) -> List[str]:
    """Detect components using simple pattern matching."""
    components = []

    # Docker detection
    if "docker-compose" in code.lower() or "services:" in code:
        components.append("docker")

    # Airflow detection
    if "DAG(" in code or "@dag" in code.lower() or "airflow" in code.lower():
        components.append("airflow")

    # Spark detection
    if "spark" in code.lower() or "SparkSession" in code:
        components.append("spark")

    # MLflow detection
    if "mlflow" in code.lower() or "log_metric" in code:
        components.append("mlflow")

    return components if components else ["generic"]
```

### Enhanced Detection (Recommended)

**Multi-stage Detection**:

1. **File Structure Analysis**:
   - Parse file tree
   - Check for known directories (`airflow/dags/`, `spark-jobs/`, `mlflow/`)
   - Check for configuration files (`docker-compose.yml`, `Dockerfile`)

2. **Content Pattern Matching**:
   - Scan files for keywords and patterns
   - Use regex for precise matching
   - Avoid false positives from comments

3. **Configuration Parsing**:
   - Parse YAML/JSON configs
   - Extract service definitions
   - Validate against expected structure

4. **Confidence Scoring**:
   - Assign confidence scores (0-1) for each component
   - Higher confidence for multiple indicators
   - Lower threshold for "generic" fallback

## Edge Cases Handling

### Empty Files
- **Detection**: Skip empty files
- **Result**: May reduce detection accuracy

### Broken YAML/Syntax
- **Detection**: Use pattern matching as fallback
- **Result**: Still detect if patterns exist

### Mixed Projects
- **Detection**: Detect all present components
- **Result**: Multi-component projects handled correctly

### False Positives
- **Mitigation**: Require multiple indicators (file + content)
- **Acceptance**: Better to over-detect than under-detect

## Improvements for Phase 2+

1. **AST Parsing**: Use Python AST for more accurate code analysis
2. **Docker Compose Parsing**: Parse YAML to extract service names
3. **Confidence Scores**: Return confidence levels with detections
4. **Machine Learning**: Train classifier on labeled projects
5. **Incremental Detection**: Detect as files are processed

## Testing Strategy

### Unit Tests

```python
def test_docker_detection():
    """Test Docker detection patterns."""
    code = "version: '3.8'\nservices:\n  postgres:\n    image: postgres"
    components = detect_components(code)
    assert "docker" in components

def test_all_components():
    """Test detection of all 4 components."""
    code = load_fixture("mixed_project")
    components = detect_components(code)
    assert set(components) == {"docker", "airflow", "spark", "mlflow"}
```

### Integration Tests

Test with real student projects:
- `student_hw1/` → should detect `docker, spark`
- `student_hw2/` → should detect `docker, spark, airflow`
- `student_hw3/` → should detect `docker, spark, airflow, mlflow`

### Validation Against hw_checker

Compare detection results with hw_checker validation:
- If hw_checker validates HW2 structure → our detection should find `docker, spark, airflow`
- If hw_checker validates HW3 structure → our detection should find all 4 components

## References

- hw_checker validation: `/home/fall_out_bug/msu_ai_masters/mlsd/hw_checker/`
- Assignment configs: `hw_checker/src/hw_checker/validators/assignment_configs.py`
- Real student projects: `tests/fixtures/student_hw{1,2,3}/`
