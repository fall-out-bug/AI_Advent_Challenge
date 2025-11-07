# Log Archive Format Specification

## Overview

The log archive is a ZIP file containing runtime logs from student submissions. The archive is processed during Pass 4 (Runtime Analysis) of the code review pipeline.

## Archive Structure

```
logs.zip
└── logs/
    ├── checker.log              # Main checker application logs
    ├── run_stdout.txt           # Docker stdout logs
    ├── run_stderr.txt           # Docker stderr logs
    ├── container-{name}.log     # Container-specific logs (e.g., container-airflow.log)
    └── ...                      # Additional log files
```

## Directory Structure

- **Root directory**: `logs/` (required)
- All log files must be placed inside the `logs/` directory
- Files outside `logs/` are ignored

## Supported Log Formats

### 1. Checker Log Format

**File**: `logs/checker.log`

**Format**: Structured log with timestamp, level, component, and message

```
YYYY-MM-DD HH:MM:SS | LEVEL | component.name | message
```

**Example**:
```
2025-01-15 10:30:45 | INFO | hw_checker.sandbox.dind | Starting Docker container
2025-01-15 10:30:46 | WARNING | hw_checker.sandbox.dind | Container health check failed
2025-01-15 10:30:47 | ERROR | hw_checker.sandbox.dind | Container exited with code 1
```

**Fields**:
- `timestamp`: ISO-like format `YYYY-MM-DD HH:MM:SS`
- `level`: One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `component`: Dot-separated component name (e.g., `hw_checker.sandbox.dind`)
- `message`: Free-form log message

### 2. Docker stdout/stderr Format

**Files**: `logs/run_stdout.txt`, `logs/run_stderr.txt`

**Format**: Raw output from Docker containers

**Example** (stdout):
```
Starting application...
Database connection established
Processing 100 records
```

**Example** (stderr):
```
WARNING: Deprecated API usage detected
ERROR: Failed to connect to database
```

**Note**: These logs may not have structured timestamps or levels. The parser attempts to extract severity from keywords (ERROR, WARNING, etc.).

### 3. Container Logs Format

**Files**: `logs/container-{name}.log`

**Format**: Container-specific logs (e.g., Airflow, PostgreSQL, etc.)

**Example** (container-airflow.log):
```
[2025-01-15 10:30:45,123] {scheduler_job.py:1234} INFO - Starting scheduler
[2025-01-15 10:30:46,456] {dagbag.py:567} ERROR - Failed to load DAG: syntax error
```

**Note**: Format varies by container type. The parser attempts to extract timestamps and severity levels.

## File Size Limits

- **Individual file**: Maximum 10 MB per log file
- **Total archive**: Maximum 100 MB (configurable via `ARCHIVE_MAX_TOTAL_SIZE_MB`)
- Files exceeding limits are skipped with a warning

## Log Processing

### Parsing

1. **Checker logs**: Parsed using structured format regex
2. **Docker stdout/stderr**: Parsed for severity keywords (ERROR, WARNING, etc.)
3. **Container logs**: Attempted parsing with flexible regex patterns

### Normalization

- Logs are grouped by component and severity level
- Duplicate entries are deduplicated
- Timestamps are normalized to UTC

### Filtering

- Only logs with severity >= `LOG_ANALYSIS_MIN_SEVERITY` are analyzed
- Default minimum severity: `WARNING`
- Configurable via `LOG_ANALYSIS_MIN_SEVERITY` environment variable

### Analysis

- Maximum `LOG_ANALYSIS_MAX_GROUPS` groups are analyzed per submission
- Default: 20 groups
- Each group is analyzed by LLM to identify:
  - Classification (bug, configuration, performance, security, usability, other)
  - Root cause
  - Recommendations
  - Confidence score

## Example Archive Creation

### Using Python

```python
import zipfile
from pathlib import Path

def create_log_archive(logs_dir: Path, output_path: Path):
    """Create log archive from directory."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for log_file in logs_dir.rglob('*.log'):
            # Add file with logs/ prefix
            arcname = f"logs/{log_file.name}"
            zf.write(log_file, arcname)
```

### Using Command Line

```bash
# Create archive from logs directory
cd /path/to/logs
zip -r ../logs.zip logs/

# Or using tar (then convert to zip)
tar -czf logs.tar.gz logs/
```

## Validation

The archive is validated on upload:

1. **Format**: Must be a valid ZIP file
2. **Structure**: Must contain `logs/` directory
3. **Size**: Must not exceed `ARCHIVE_MAX_TOTAL_SIZE_MB`
4. **Content**: At least one log file must be present

## Error Handling

- **Invalid ZIP**: Returns 400 Bad Request
- **Missing logs/ directory**: Returns warning, skips log analysis
- **No log files**: Returns warning, skips log analysis
- **Size exceeded**: Returns 413 Request Entity Too Large

## Integration Notes

- Log archives are optional (can be `null` in API request)
- If not provided, Pass 4 (log analysis) is skipped
- If provided but empty, Pass 4 returns "skipped" status
- Log analysis can be disabled via `ENABLE_LOG_ANALYSIS=false`

