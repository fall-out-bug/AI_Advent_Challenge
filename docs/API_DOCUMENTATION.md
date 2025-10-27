# API Documentation

## Overview

The AI Challenge API provides REST endpoints for code generation, review, and orchestration workflows.

**Base URL**: `http://localhost:8000`

**Interactive Documentation**: `http://localhost:8000/docs`

## Authentication

Currently, no authentication is required for local development.

## Rate Limiting

No rate limiting is enforced in local development.

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

## Endpoints

### Agents

#### Generate Code

Generate Python code from a natural language description.

**POST** `/api/agents/generate`

**Request Body:**
```json
{
  "prompt": "string (required)",
  "agent_name": "string (optional, default: 'generator')",
  "model_config_id": "string (optional)",
  "model_name": "string (optional, default: 'starcoder')",
  "max_tokens": "integer (optional, default: 1000)",
  "temperature": "float (optional, default: 0.7)"
}
```

**Response:**
```json
{
  "task_id": "string",
  "status": "completed",
  "result": "def fibonacci(n): ...",
  "quality_metrics": {
    "complexity": "low|medium|high",
    "lines_of_code": 15,
    "estimated_time": "5 minutes"
  },
  "token_info": {
    "input_tokens": 50,
    "output_tokens": 150,
    "total_tokens": 200
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/agents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a function to calculate the factorial of a number",
    "model_name": "starcoder"
  }'
```

#### Review Code

Review code and provide quality feedback.

**POST** `/api/agents/review`

**Request Body:**
```json
{
  "code": "string (required)",
  "agent_name": "string (optional, default: 'reviewer')",
  "model_config_id": "string (optional)",
  "model_name": "string (optional, default: 'mistral')"
}
```

**Response:**
```json
{
  "task_id": "string",
  "status": "completed",
  "result": "Code review feedback...",
  "quality_metrics": {
    "pep8_score": 9.5,
    "complexity": "low",
    "test_coverage": "high",
    "security_score": 8.0
  },
  "token_info": {
    "input_tokens": 200,
    "output_tokens": 300,
    "total_tokens": 500
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/agents/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fibonacci(n): return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)",
    "model_name": "mistral"
  }'
```

#### Get Task Status

Get status of a previously submitted task.

**GET** `/api/agents/tasks/{task_id}`

**Parameters:**
- `task_id` (path): Task identifier

**Response:**
```json
{
  "task_id": "string",
  "status": "completed|in_progress|failed",
  "result": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:01Z",
  "metadata": {}
}
```

**Example:**
```bash
curl http://localhost:8000/api/agents/tasks/abc-123-def-456
```

#### List Tasks

List all tasks with optional filtering.

**GET** `/api/agents/tasks`

**Query Parameters:**
- `status` (optional): Filter by status
- `agent_name` (optional): Filter by agent name
- `limit` (optional): Maximum number of results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "tasks": [
    {
      "task_id": "string",
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "limit": 10,
  "offset": 0
}
```

**Example:**
```bash
curl "http://localhost:8000/api/agents/tasks?status=completed&limit=10"
```

### Health

#### Health Check

Simple health status check.

**GET** `/health/`

**Response:**
```json
{
  "status": "ok"
}
```

#### Readiness Check

Detailed readiness check for all components.

**GET** `/health/ready`

**Response:**
```json
{
  "overall": "ready|degraded",
  "checks": {
    "storage": {
      "status": "healthy",
      "message": "Storage is accessible",
      "response_time_ms": 2.5,
      "details": {}
    },
    "models": {
      "status": "healthy",
      "message": "All models available",
      "response_time_ms": 45.2,
      "details": {
        "starcoder": "available",
        "mistral": "available"
      }
    }
  }
}
```

#### Model Health

Check health status of individual models.

**GET** `/health/models`

**Response:**
```json
{
  "overall": "healthy",
  "models": {
    "starcoder": {
      "status": "available",
      "response_time_ms": 45.2
    },
    "mistral": {
      "status": "available",
      "response_time_ms": 38.7
    },
    "qwen": {
      "status": "unavailable",
      "response_time_ms": null,
      "error": "Connection timeout"
    }
  }
}
```

#### Storage Health

Check storage accessibility and status.

**GET** `/health/storage`

**Response:**
```json
{
  "status": "healthy",
  "message": "Storage is accessible",
  "response_time_ms": 2.5,
  "details": {
    "data_directory": "/path/to/data",
    "writable": true,
    "disk_usage_percent": 45.2
  }
}
```

### Dashboard

#### Get Dashboard HTML

Retrieve the dashboard HTML page.

**GET** `/dashboard/`

**Response:** HTML page

**Example:**
```bash
curl http://localhost:8000/dashboard/
```

#### Get Dashboard Data

Get metrics data for the dashboard.

**GET** `/dashboard/data`

**Response:**
```json
{
  "metrics": {
    "total_requests": 1000,
    "successful_requests": 950,
    "failed_requests": 50,
    "average_response_time_ms": 123.45,
    "models": {
      "starcoder": {
        "requests": 500,
        "success_rate": 0.95,
        "avg_response_time_ms": 125.0
      }
    }
  },
  "recent_operations": [
    {
      "task_id": "abc-123",
      "agent": "generator",
      "status": "completed",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Experiments (Deprecated)

**Note**: These endpoints are deprecated. Use the agent endpoints instead.

#### Run Experiment

**POST** `/api/experiments/run`

**Status**: Deprecated (returns 501)

**Response:**
```json
{
  "detail": "Legacy adapter-based experiments are deprecated. Please use the new Phase 2 API endpoints."
}
```

#### Get Experiment Status

**GET** `/api/experiments/status`

**Response:**
```json
{
  "status": "deprecated",
  "message": "Legacy adapter-based experiments are deprecated. Please use the new Phase 2 API endpoints."
}
```

## Data Models

### Task Status

Enum values:
- `pending`: Task is pending
- `in_progress`: Task is being processed
- `completed`: Task completed successfully
- `failed`: Task failed
- `cancelled`: Task was cancelled

### Task Type

Enum values:
- `code_generation`: Code generation task
- `code_review`: Code review task
- `token_analysis`: Token analysis task

### Quality Metrics

```json
{
  "complexity": "string (low|medium|high)",
  "lines_of_code": "integer",
  "estimated_time": "string",
  "dependencies": ["string"],
  "pep8_score": "float (0-10)",
  "test_coverage": "string (low|medium|high)",
  "security_score": "float (0-10)",
  "overall_score": "float (0-10)"
}
```

### Token Info

```json
{
  "input_tokens": "integer",
  "output_tokens": "integer",
  "total_tokens": "integer",
  "model_name": "string",
  "compression_applied": "boolean",
  "compression_ratio": "float (optional)"
}
```

## SDK Usage

### Python SDK

```python
from src.infrastructure.clients.simple_model_client import SimpleModelClient

# Create client
client = SimpleModelClient()

# Generate code
result = await client.generate(
    prompt="Create a fibonacci function",
    config=None
)
```

### TypeScript SDK

```typescript
import { ModelClient } from '@ai-challenge/sdk';

const client = new ModelClient('http://localhost:8000');

const result = await client.generate({
  prompt: 'Create a fibonacci function',
  modelName: 'starcoder'
});
```

## Webhooks

Webhooks are not currently supported but planned for future releases.

## Rate Limits

Rate limiting is not enforced in local development. For production deployments, configure appropriate rate limiting.

## Best Practices

1. **Use Appropriate Models**: Use StarCoder for code generation, Mistral for review
2. **Handle Errors**: Always check status codes and handle errors appropriately
3. **Monitor Health**: Use health endpoints before critical operations
4. **Optimize Prompts**: Provide clear, specific prompts for better results
5. **Monitor Tokens**: Use token info to optimize model selection

## Support

For API issues:
1. Check health endpoints: `GET /health/ready`
2. Review logs: `docker-compose logs api`
3. See [Troubleshooting Guide](OPERATIONS.md)

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for API changes.

