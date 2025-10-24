# API Documentation

Complete API reference for the StarCoder Multi-Agent System.

## Overview

The system provides REST APIs for two specialized agents:
- **Code Generator Agent** (Port 9001): Generates Python code and tests
- **Code Reviewer Agent** (Port 9002): Reviews code quality and provides feedback

All APIs follow OpenAPI 3.0 specification and include:
- Rate limiting (10 requests/minute)
- Input validation with Pydantic models
- Comprehensive error handling
- Health monitoring endpoints

## Base URLs

- **Generator Agent**: `http://localhost:9001`
- **Reviewer Agent**: `http://localhost:9002`
- **StarCoder Service**: `http://localhost:8003`

## Authentication

Currently, no authentication is required. Future versions may include API key authentication.

## Rate Limiting

All endpoints are rate-limited to **10 requests per minute** per IP address.

**Rate Limit Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1640995200
```

**Rate Limit Exceeded Response:**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## Code Generator Agent API

Base URL: `http://localhost:9001`

### POST /generate

Generate Python code and tests based on task description.

**Request Body:**
```json
{
  "task_description": "Create a function to calculate fibonacci numbers",
  "language": "python",
  "requirements": ["Include type hints", "Handle edge cases"],
  "max_tokens": 1000
}
```

**Request Schema:**
- `task_description` (string, required): Detailed description of the code to generate
- `language` (string, optional): Programming language (default: "python")
- `requirements` (array, optional): Additional requirements for the task
- `max_tokens` (integer, optional): Maximum tokens for generation (default: 1000)

**Response:**
```json
{
  "task_description": "Create a function to calculate fibonacci numbers",
  "generated_code": "def fibonacci(n: int) -> int:\n    \"\"\"Calculate the nth Fibonacci number.\"\"\"\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "tests": "import pytest\n\ndef test_fibonacci():\n    assert fibonacci(0) == 0\n    assert fibonacci(1) == 1\n    assert fibonacci(10) == 55",
  "metadata": {
    "complexity": "medium",
    "lines_of_code": 8,
    "estimated_time": "5 minutes",
    "dependencies": ["typing"]
  },
  "generation_time": "2025-10-23T10:30:00Z",
  "tokens_used": 450
}
```

**Response Schema:**
- `task_description` (string): Original task description
- `generated_code` (string): Generated Python code
- `tests` (string): Generated unit tests
- `metadata` (object): Code metadata
  - `complexity` (string): Complexity level (low/medium/high)
  - `lines_of_code` (integer): Estimated lines of code
  - `estimated_time` (string): Estimated development time
  - `dependencies` (array): Required dependencies
- `generation_time` (string): ISO timestamp of generation
- `tokens_used` (integer): Number of tokens consumed

**Example cURL:**
```bash
curl -X POST "http://localhost:9001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a sorting function",
    "requirements": ["Use quicksort algorithm", "Include type hints"]
  }'
```

### POST /refine

Refine existing code based on feedback.

**Request Body:**
```json
{
  "code": "def sort_list(items):\n    return sorted(items)",
  "feedback": "Add type hints and handle empty lists"
}
```

**Request Schema:**
- `code` (string, required, max 10000 chars): Code to refine
- `feedback` (string, required, max 5000 chars): Feedback to incorporate

**Response:**
```json
{
  "refined_code": "def sort_list(items: List[Any]) -> List[Any]:\n    \"\"\"Sort a list of items.\"\"\"\n    if not items:\n        return []\n    return sorted(items)"
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:9001/refine" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a, b): return a + b",
    "feedback": "Add type hints and error handling"
  }'
```

### POST /validate

Validate generated code for basic issues.

**Request Body:**
```json
{
  "code": "def example_function():\n    pass"
}
```

**Request Schema:**
- `code` (string, required, max 10000 chars): Code to validate

**Response:**
```json
{
  "valid": false,
  "issues": [
    "No docstrings found",
    "No type hints found"
  ],
  "issue_count": 2
}
```

**Response Schema:**
- `valid` (boolean): Whether code passes validation
- `issues` (array): List of validation issues
- `issue_count` (integer): Number of issues found

**Example cURL:**
```bash
curl -X POST "http://localhost:9001/validate" \
  -H "Content-Type: application/json" \
  -d '{"code": "def test(): pass"}'
```

### GET /health

Check agent health status.

**Response:**
```json
{
  "status": "healthy",
  "agent_type": "generator",
  "uptime": 3600.5
}
```

**Response Schema:**
- `status` (string): Health status (healthy/unhealthy)
- `agent_type` (string): Type of agent
- `uptime` (number): Uptime in seconds

**Example cURL:**
```bash
curl "http://localhost:9001/health"
```

### GET /stats

Get agent performance statistics.

**Response:**
```json
{
  "total_requests": 150,
  "successful_requests": 145,
  "failed_requests": 5,
  "average_response_time": 2.3,
  "total_tokens_used": 45000
}
```

**Response Schema:**
- `total_requests` (integer): Total number of requests processed
- `successful_requests` (integer): Number of successful requests
- `failed_requests` (integer): Number of failed requests
- `average_response_time` (number): Average response time in seconds
- `total_tokens_used` (integer): Total tokens consumed

**Example cURL:**
```bash
curl "http://localhost:9001/stats"
```

---

## Code Reviewer Agent API

Base URL: `http://localhost:9002`

### POST /review

Review generated code for quality and best practices.

**Request Body:**
```json
{
  "task_description": "Create a function to calculate fibonacci numbers",
  "generated_code": "def fibonacci(n: int) -> int:\n    \"\"\"Calculate the nth Fibonacci number.\"\"\"\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "tests": "import pytest\n\ndef test_fibonacci():\n    assert fibonacci(0) == 0\n    assert fibonacci(1) == 1",
  "metadata": {
    "complexity": "medium",
    "lines_of_code": 8
  }
}
```

**Request Schema:**
- `task_description` (string, required): Original task description
- `generated_code` (string, required): Code to review
- `tests` (string, required): Tests to review
- `metadata` (object, optional): Code metadata

**Response:**
```json
{
  "code_quality_score": 8.5,
  "metrics": {
    "pep8_compliance": true,
    "pep8_score": 9.0,
    "has_docstrings": true,
    "has_type_hints": true,
    "test_coverage": "good",
    "complexity_score": 7.0
  },
  "issues": [
    "Consider adding error handling for negative numbers",
    "Missing edge case tests for large numbers"
  ],
  "recommendations": [
    "Add input validation",
    "Consider iterative implementation for better performance",
    "Add more comprehensive test cases"
  ],
  "review_time": "2025-10-23T10:30:05Z",
  "tokens_used": 320
}
```

**Response Schema:**
- `code_quality_score` (number): Overall quality score (0-10)
- `metrics` (object): Detailed metrics
  - `pep8_compliance` (boolean): PEP8 compliance status
  - `pep8_score` (number): PEP8 compliance score (0-10)
  - `has_docstrings` (boolean): Whether docstrings are present
  - `has_type_hints` (boolean): Whether type hints are present
  - `test_coverage` (string): Test coverage assessment
  - `complexity_score` (number): Code complexity score (0-10)
- `issues` (array): List of identified issues
- `recommendations` (array): List of improvement recommendations
- `review_time` (string): ISO timestamp of review
- `tokens_used` (integer): Number of tokens consumed

**Example cURL:**
```bash
curl -X POST "http://localhost:9002/review" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a sorting function",
    "generated_code": "def sort_list(items): return sorted(items)",
    "tests": "def test_sort(): assert sort_list([3,1,2]) == [1,2,3]"
  }'
```

### GET /health

Check reviewer agent health status.

**Response:**
```json
{
  "status": "healthy",
  "agent_type": "reviewer",
  "uptime": 3600.5
}
```

**Example cURL:**
```bash
curl "http://localhost:9002/health"
```

### GET /stats

Get reviewer agent performance statistics.

**Response:**
```json
{
  "total_requests": 120,
  "successful_requests": 118,
  "failed_requests": 2,
  "average_response_time": 1.8,
  "total_tokens_used": 32000
}
```

**Example cURL:**
```bash
curl "http://localhost:9002/stats"
```

---

## StarCoder Service API

Base URL: `http://localhost:8003`

### POST /chat

Direct interaction with StarCoder model (used internally by agents).

**Request Body:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant specialized in Python development."
    },
    {
      "role": "user",
      "content": "Create a function to calculate factorial"
    }
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Request Schema:**
- `messages` (array, required): Conversation messages
  - `role` (string): Message role (system/user/assistant)
  - `content` (string): Message content
- `max_tokens` (integer, optional): Maximum tokens to generate
- `temperature` (number, optional): Sampling temperature (0.0-1.0)

**Response:**
```json
{
  "response": "def factorial(n: int) -> int:\n    \"\"\"Calculate factorial of n.\"\"\"\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
  "total_tokens": 150,
  "model": "bigcode/starcoder2-7b"
}
```

**Response Schema:**
- `response` (string): Generated response
- `total_tokens` (integer): Total tokens used
- `model` (string): Model name used

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service not ready

### Error Response Format

```json
{
  "detail": "Error message description",
  "type": "ErrorType",
  "status_code": 400
}
```

### Common Error Types

#### ValidationError
```json
{
  "detail": "Invalid input provided",
  "type": "ValidationError",
  "status_code": 400
}
```

#### RateLimitError
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "type": "RateLimitError",
  "status_code": 429
}
```

#### CodeGenerationError
```json
{
  "detail": "An internal error occurred. Please try again.",
  "type": "CodeGenerationError",
  "status_code": 500
}
```

#### ConfigurationError
```json
{
  "detail": "Agent not initialized",
  "type": "ConfigurationError",
  "status_code": 503
}
```

---

## Request/Response Examples

### Complete Workflow Example

1. **Generate Code:**
```bash
curl -X POST "http://localhost:9001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a binary search function",
    "requirements": ["Handle edge cases", "Include type hints"]
  }'
```

2. **Review Generated Code:**
```bash
curl -X POST "http://localhost:9002/review" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a binary search function",
    "generated_code": "def binary_search(arr, target): ...",
    "tests": "def test_binary_search(): ..."
  }'
```

3. **Refine Based on Review:**
```bash
curl -X POST "http://localhost:9001/refine" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def binary_search(arr, target): ...",
    "feedback": "Add type hints and handle empty array case"
  }'
```

### Batch Processing Example

```python
import asyncio
import httpx

async def process_multiple_tasks():
    tasks = [
        "Create a sorting algorithm",
        "Implement a hash table",
        "Write a graph traversal function"
    ]
    
    async with httpx.AsyncClient() as client:
        for task in tasks:
            # Generate code
            gen_response = await client.post(
                "http://localhost:9001/generate",
                json={"task_description": task}
            )
            
            # Review code
            review_response = await client.post(
                "http://localhost:9002/review",
                json={
                    "task_description": task,
                    "generated_code": gen_response.json()["generated_code"],
                    "tests": gen_response.json()["tests"]
                }
            )
            
            print(f"Task: {task}")
            print(f"Quality Score: {review_response.json()['code_quality_score']}")

# Run the example
asyncio.run(process_multiple_tasks())
```

---

## SDK Examples

### Python SDK

```python
from day_07.communication.agent_client import AgentClient
from day_07.communication.message_schema import CodeGenerationRequest

async def generate_and_review():
    async with AgentClient() as client:
        # Generate code
        request = CodeGenerationRequest(
            task_description="Create a REST API client",
            requirements=["Use httpx", "Add retry logic"]
        )
        
        generation_result = await client.generate_code(
            "http://localhost:9001",
            request
        )
        
        # Review code
        review_result = await client.review_code(
            "http://localhost:9002",
            {
                "task_description": request.task_description,
                "generated_code": generation_result.generated_code,
                "tests": generation_result.tests
            }
        )
        
        return generation_result, review_result
```

### JavaScript SDK

```javascript
class StarCoderClient {
  constructor(baseUrl = 'http://localhost:9001') {
    this.baseUrl = baseUrl;
  }
  
  async generateCode(taskDescription, requirements = []) {
    const response = await fetch(`${this.baseUrl}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_description: taskDescription,
        requirements: requirements
      })
    });
    
    return await response.json();
  }
  
  async reviewCode(taskDescription, generatedCode, tests) {
    const response = await fetch('http://localhost:9002/review', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_description: taskDescription,
        generated_code: generatedCode,
        tests: tests
      })
    });
    
    return await response.json();
  }
}

// Usage
const client = new StarCoderClient();
const result = await client.generateCode('Create a sorting function');
console.log(result.generated_code);
```

---

## Performance Guidelines

### Request Limits
- **Code Length**: Maximum 10,000 characters per request
- **Feedback Length**: Maximum 5,000 characters per request
- **Requirements**: Maximum 10 requirements per request

### Response Times
- **Code Generation**: 2-5 seconds typical
- **Code Review**: 1-3 seconds typical
- **Health Checks**: <100ms typical

### Best Practices
1. **Batch Requests**: Process multiple tasks in parallel
2. **Error Handling**: Always check response status codes
3. **Rate Limiting**: Respect the 10 requests/minute limit
4. **Input Validation**: Validate inputs before sending requests
5. **Monitoring**: Use health and stats endpoints for monitoring

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- Generator Agent: `http://localhost:9001/docs`
- Reviewer Agent: `http://localhost:9002/docs`

You can also access the ReDoc documentation at:
- Generator Agent: `http://localhost:9001/redoc`
- Reviewer Agent: `http://localhost:9002/redoc`

---

## Support

For API-related questions or issues:
1. Check the troubleshooting section in README.md
2. Review the error messages and status codes
3. Use the health endpoints to verify service status
4. Open an issue in the project repository

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for API changes and version history.
