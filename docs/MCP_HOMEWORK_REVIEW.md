# MCP Homework Review Tool Guide

## Overview

The `review_homework_archive` MCP tool provides automated multi-pass code review for student homework submissions. It now executes a five-stage pipeline:

1. **Pass 1: Architecture Overview** – Detects project structure and component types
2. **Pass 2: Component Deep-Dive** – Analyzes each detected component in detail
3. **Pass 3: Synthesis & Integration** – Generates final architecture/conclusion summary
4. **Static Analysis Stage** – Runs Flake8, Pylint, MyPy, Black, isort and aggregates results
5. **Pass 4: Log Analysis** – Parses runtime logs, groups issues, and provides remediation tips
6. **Publishing & Haiku** – Produces markdown + haiku and publishes via HW Checker MCP (with fallback)

## Tool Discovery

The tool is registered in the MCP server and can be discovered via the standard MCP protocol:

```python
from mcp import Client

# Connect to MCP server
client = Client("http://localhost:8004")

# List available tools
tools = await client.list_tools()

# Find homework review tool
hw_tool = next(t for t in tools if t.name == "review_homework_archive")
print(f"Found tool: {hw_tool.name}")
print(f"Description: {hw_tool.description}")
```

## Tool Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `archive_path` | str | - | ✅ Yes | Path to .zip archive containing student homework |
| `assignment_type` | str | "auto" | No | Assignment type: "HW1", "HW2", "HW3", or "auto" for auto-detection |
| `token_budget` | int | 8000 | No | Total token budget for all review passes |
| `model_name` | str | "mistral" | No | Model name to use for code review |

### Assignment Type Auto-Detection

The tool can automatically detect assignment types based on directory structure:

- **HW1**: Docker + Spark (requires both `Dockerfile` and `SparkSession` in Python code)
- **HW2**: Airflow (requires `airflow` directory or path containing "airflow")
- **HW3**: MLflow (requires `mlflow` directory or path containing "mlflow")
- **auto**: Unknown structure (will default to generic review)

## Example Usage

### Basic Usage

```python
from mcp import Client

# Connect to MCP server
client = Client("http://localhost:8004")

# Review homework archive
result = await client.call_tool(
    "review_homework_archive",
    {
        "archive_path": "/path/to/student_hw1.zip",
        "assignment_type": "auto",
        "token_budget": 8000,
        "model_name": "mistral"
    }
)

# Access results
print(f"Session ID: {result['session_id']}")
print(f"Total findings: {result['total_findings']}")
print(f"Execution time: {result['execution_time_seconds']}s")
```

### Review Results Structure

```python
{
    "success": True,
    "session_id": "uuid-string",
    "repo_name": "student_hw1",
    "assignment_type": "HW1",
    "detected_components": ["docker", "spark"],
    "total_findings": 12,
    "execution_time_seconds": 245.6,
    "pass_1_completed": True,
    "pass_2_components": ["docker", "spark"],
    "pass_3_completed": True,
"markdown_report": "# Code Review Report: Detailed Analysis\n\n...",
"static_analysis_results": [
    {
        "tool": "flake8",
        "summary": "2 issues",
        "entries": [
            "app/main.py:12 E501 line too long",
            "utils/helpers.py:45 W292 no newline at end of file"
        ]
    }
],
"pass_4_logs": {
    "status": "completed",
    "results": [
        {
            "component": "docker",
            "classification": "ERROR",
            "description": "Container exited with status 1",
            "root_cause": "Missing ENV VAR FOO",
            "recommendations": "Add FOO=... to compose file",
            "confidence": 0.82,
            "count": 3
        }
    ]
},
"haiku": "Code finds balance\nLogs whisper of hidden faults\nFix blooms in review",
"json_report": "{ ... }",
    "logs_saved": True,
    "report_saved_to_mongodb": True
}
```

## Understanding Multi-Pass Reports

### Pass 1: Architecture Overview

Analyzes overall project structure and identifies:
- Project architecture patterns
- Component types (Docker, Airflow, Spark, MLflow, etc.)
- Dependency relationships
- Architectural issues and concerns

### Pass 2: Component Deep-Dive

Performs detailed analysis for each detected component:
- Docker: Image optimization, security, multi-stage builds
- Airflow: DAG structure, task dependencies, error handling
- Spark: DataFrame operations, partitioning, performance
- MLflow: Experiment tracking, model versioning, reproducibility

### Pass 3: Synthesis & Integration

Generates final comprehensive report:
- Consolidated findings from all passes
- Prioritized recommendations
- Integration issues and patterns
- Overall project quality assessment

### Static Analysis Stage

Runs linting and formatting tools to surface style, type, and formatting issues:
- Flake8, Pylint, MyPy, Black, isort executed inside the review workspace.
- Results are grouped by tool with severity and snippet context.
- Findings appear in both markdown and JSON reports under `static_analysis_results`.

### Pass 4: Log Analysis

Analyzes runtime logs to uncover execution issues:
- `LogParserImpl` ingests checker logs, Docker stdout/stderr, compose logs.
- `LogNormalizer` filters by severity and groups recurring messages.
- `LLMLogAnalyzer` classifies groups, identifies root causes, and suggests remediation.
- Output stored in `pass_4_logs` with counts, classifications, and recommendations.

### Publishing & Haiku

- Every review concludes with an LLM-generated haiku summarising tone and key risks.
- Results are published via the external HW Checker MCP tool (`submit_review_result`).
- When MCP is unavailable or disabled, publishing falls back to the HTTP API (`ExternalAPIClient`).

## Accessing Review Reports

### Markdown Report

The `markdown_report` field contains a comprehensive human-readable report:

```python
result = await client.call_tool("review_homework_archive", {...})
markdown = result["markdown_report"]

# Save to file
with open("review_report.md", "w") as f:
    f.write(markdown)
```

### MongoDB Storage

All reviews are automatically saved to MongoDB with:
- Full execution logs
- Model interactions and reasoning
- Work steps and status
- Complete report (markdown + JSON)

Access via MongoDB:

```python
from src.infrastructure.database.mongo import get_db
from src.infrastructure.repositories.homework_review_repository import HomeworkReviewRepository

db = await get_db()
repository = HomeworkReviewRepository(db)

session = await repository.get_review_session(result["session_id"])
print(f"Report: {session['report']['markdown'][:500]}...")
```

## Error Handling

### Common Errors

**FileNotFoundError**: Archive path doesn't exist
```python
try:
    result = await client.call_tool("review_homework_archive", {...})
except FileNotFoundError as e:
    print(f"Archive not found: {e}")
```

**ValueError**: Invalid archive format
```python
# Using .txt instead of .zip
try:
    result = await client.call_tool("review_homework_archive", {
        "archive_path": "/path/to/archive.txt"
    })
except ValueError as e:
    print(f"Invalid archive: {e}")
```

**RuntimeError**: No code files in archive
```python
try:
    result = await client.call_tool("review_homework_archive", {...})
except ValueError as e:
    if "No code files found" in str(e):
        print("Archive is empty or contains no code files")
```

## Best Practices

### Token Budget

Adjust `token_budget` based on project size:
- Small projects (<10 files): 4000-6000 tokens
- Medium projects (10-30 files): 8000-12000 tokens
- Large projects (30+ files): 12000-20000 tokens

### Assignment Type

Use manual assignment type when auto-detection fails:
```python
result = await client.call_tool("review_homework_archive", {
    "archive_path": "/path/to/archive.zip",
    "assignment_type": "HW1"  # Force specific type
})
```

### Model Selection

- `"mistral"`: Best quality, slower (recommended for production)
- Other models available via UnifiedModelClient configuration

### Static Analysis & Logs

- Добавляйте `logs_zip`, чтобы Pass 4 мог диагностировать рантайм-проблемы.
- Используйте поля `static_analysis_results` и `pass_4_logs` для обратной связи студентам.
- Сохраняйте `haiku` в интерфейсе как краткое резюме ревью.

## Troubleshooting

### Tool Not Found

If `review_homework_archive` doesn't appear in tool list:
```python
# Check MCP server is running
tools = await client.list_tools()
print(f"Available tools: {[t.name for t in tools]}")

# Verify tool registration
assert "review_homework_archive" in [t.name for t in tools]
```

### Review Takes Too Long

For faster reviews:
1. Reduce `token_budget` (smaller prompts)
2. Use faster model
3. Focus on specific assignment type

### MongoDB Connection Issues

Reviews still complete but logs won't be saved:
```python
result = await client.call_tool("review_homework_archive", {...})
# result["logs_saved"] will be False if MongoDB unavailable
# result["report_saved_to_mongodb"] will be False
# But report is still returned in result
```

## Integration Examples

### Via HTTP API

```bash
curl -X POST http://localhost:8004/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "review_homework_archive",
    "arguments": {
      "archive_path": "/path/to/archive.zip",
      "assignment_type": "auto",
      "token_budget": 8000
    }
  }'
```

### Via MCP SDK

See example usage above in "Example Usage" section.

## References

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Multi-Pass Architecture](tasks/day_14/ARCHITECTURE_DECISIONS.md)
- [Implementation Review](tasks/day_14/IMPLEMENTATION_REVIEW.md)

