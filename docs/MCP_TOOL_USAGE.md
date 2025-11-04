# MCP Tool: Homework Review

## Overview

The `review_homework_archive` MCP tool provides multi-pass code review for student homework archives. It automatically detects project components (Docker, Airflow, Spark, MLflow) and performs deep analysis.

## Tool Signature

```python
@mcp.tool()
async def review_homework_archive(
    archive_path: str,
    assignment_type: str = "auto",
    token_budget: int = 8000,
    model_name: str = "mistral",
) -> Dict[str, Any]
```

## Parameters

- **archive_path** (str, required): Path to `.zip` archive with student homework
- **assignment_type** (str, default: "auto"): Type of assignment:
  - `"HW1"` - Docker + Spark project
  - `"HW2"` - Docker + Spark + Airflow project
  - `"HW3"` - Docker + Spark + Airflow + MLflow project
  - `"auto"` - Auto-detect from project structure
- **token_budget** (int, default: 8000): Token budget for review
- **model_name** (str, default: "mistral"): Model to use for review

## Return Value

Returns dictionary with:
- `success` (bool): Whether review completed successfully
- `session_id` (str): Session ID for review
- `repo_name` (str): Repository name
- `assignment_type` (str): Detected/used assignment type
- `detected_components` (List[str]): List of detected components
- `total_findings` (int): Total number of findings
- `execution_time_seconds` (float): Time taken for review
- `pass_1_completed` (bool): Whether Pass 1 completed
- `pass_2_components` (List[str]): List of components analyzed in Pass 2
- `pass_3_completed` (bool): Whether Pass 3 completed
- `markdown_report` (str): Full report in Markdown format
- `json_report` (str): Full report in JSON format

## Usage Examples

### Via MCP Client

```python
from src.presentation.mcp.client import MCPClient

client = MCPClient()
tools = await client.discover_tools()

result = await client.call_tool(
    "review_homework_archive",
    {
        "archive_path": "/path/to/hw1.zip",
        "assignment_type": "auto",
        "token_budget": 8000
    }
)

print(result["markdown_report"])
```

### Via Python Script

```python
from src.presentation.mcp.tools.homework_review_tool import review_homework_archive

result = await review_homework_archive(
    archive_path="/path/to/hw2.zip",
    assignment_type="HW2",
    token_budget=8000
)

print(f"Detected: {result['detected_components']}")
print(f"Findings: {result['total_findings']}")
```

### Via Command Line Script

```bash
python scripts/test_homework_review.py /path/to/archive.zip --model mistral --token-budget 8000
```

## Auto-Detection Logic

The tool automatically detects assignment type by checking:

1. **HW3**: Presence of `mlflow/` directory or MLflow-related files
2. **HW2**: Presence of `airflow/` directory or Airflow DAGs
3. **HW1**: Presence of `Dockerfile` and Spark code (`SparkSession`)

If detection fails, returns `"auto"` and proceeds with generic component detection.

## Error Handling

The tool handles:
- **FileNotFoundError**: Archive doesn't exist
- **ValueError**: Invalid archive format or no code files found
- **Model errors**: Automatic retry with exponential backoff
- **Token budget overflow**: Automatic truncation
- **Pass failures**: Graceful degradation with partial reports

## Integration in MCP Server

The tool is automatically registered when MCP server starts:

```python
# In src/presentation/mcp/server.py
tool_modules = [
    ...
    ("homework_review_tool", "src.presentation.mcp.tools.homework_review_tool"),
]
```

## Requirements

- Mistral model container running on `localhost:8001` (or configure via MODEL_CONFIGS)
- UnifiedModelClient configured for local models
- Multi-pass review system initialized

## Setup

1. Start Mistral container:
   ```bash
   cd local_models
   docker-compose up -d mistral-chat
   ```

2. Verify model is available:
   ```bash
   curl http://localhost:8001/health
   ```

3. Use tool via MCP or direct Python call

## Example Output

```json
{
  "success": true,
  "session_id": "session_abc123",
  "repo_name": "student_hw2",
  "assignment_type": "HW2",
  "detected_components": ["docker", "spark", "airflow"],
  "total_findings": 15,
  "execution_time_seconds": 45.2,
  "pass_1_completed": true,
  "pass_2_components": ["docker", "spark", "airflow"],
  "pass_3_completed": true,
  "markdown_report": "# Multi-Pass Code Review Report\n\n...",
  "json_report": "{...}"
}
```

