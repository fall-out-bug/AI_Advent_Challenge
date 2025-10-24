# Code Examples and Patterns

## Agent Implementation Examples

### Basic Agent Structure
```python
from agents.core.base_agent import BaseAgent
from communication.message_schema import TaskMetadata
from exceptions import CodeGenerationError

class CustomAgent(BaseAgent):
    """Custom agent implementation following project patterns."""
    
    def __init__(self, starcoder_url: str, agent_type: str = "custom"):
        super().__init__(starcoder_url, agent_type)
        self.max_tokens = 1000
        self.temperature = 0.7
    
    async def process_task(self, task_description: str) -> dict:
        """Process task with comprehensive error handling."""
        try:
            # Validate input
            if not task_description.strip():
                raise ValueError("Task description cannot be empty")
            
            # Create prompt
            prompt = self._create_prompt(task_description)
            
            # Call StarCoder
            response = await self._call_starcoder(prompt)
            
            # Parse response
            result = self._parse_response(response)
            
            return result
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise CodeGenerationError(f"Invalid input: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise CodeGenerationError("Task processing failed") from e
    
    def _create_prompt(self, task_description: str) -> str:
        """Create formatted prompt for StarCoder."""
        return f"""
        Task: {task_description}
        
        Requirements:
        - Use Python 3.11+
        - Include type hints
        - Add comprehensive docstrings
        - Handle edge cases
        - Follow PEP 8 style
        
        Generate code and tests:
        """
    
    def _parse_response(self, response: str) -> dict:
        """Parse StarCoder response into structured format."""
        # Extract code and tests
        code = self._extract_code_from_response(response)
        tests = self._extract_tests_from_response(response)
        
        # Create metadata
        metadata = TaskMetadata(
            complexity="medium",
            lines_of_code=len(code.split('\n')),
            estimated_time="5 minutes",
            dependencies=["typing", "pytest"]
        )
        
        return {
            "code": code,
            "tests": tests,
            "metadata": metadata,
            "tokens_used": len(response.split())
        }
```

### API Endpoint Examples

#### Basic Endpoint with Rate Limiting
```python
from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Custom Agent API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class TaskRequest(BaseModel):
    """Request model for task processing."""
    task_description: str = Field(max_length=2000, description="Task description")
    requirements: list[str] = Field(default=[], max_items=10, description="Additional requirements")

class TaskResponse(BaseModel):
    """Response model for task processing."""
    success: bool = Field(description="Whether task was successful")
    code: str = Field(description="Generated code")
    tests: str = Field(description="Generated tests")
    metadata: dict = Field(description="Task metadata")
    processing_time: float = Field(description="Processing time in seconds")

@app.post("/process", response_model=TaskResponse)
@limiter.limit("10/minute")
async def process_task(request: TaskRequest) -> TaskResponse:
    """Process task with rate limiting and validation."""
    try:
        # Validate request
        if not request.task_description.strip():
            raise HTTPException(status_code=400, detail="Task description is required")
        
        # Process task
        start_time = time.time()
        result = await agent.process_task(request.task_description)
        processing_time = time.time() - start_time
        
        return TaskResponse(
            success=True,
            code=result["code"],
            tests=result["tests"],
            metadata=result["metadata"].__dict__,
            processing_time=processing_time
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

#### Advanced Endpoint with Error Handling
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from exceptions import ValidationError, ProcessingError
import logging

logger = logging.getLogger(__name__)

class AdvancedEndpoint:
    """Advanced endpoint with comprehensive error handling."""
    
    def __init__(self, agent: BaseAgent):
        self.agent = agent
    
    async def process_with_retry(
        self, 
        request: TaskRequest, 
        max_retries: int = 3
    ) -> TaskResponse:
        """Process task with retry logic."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Processing attempt {attempt + 1}/{max_retries}")
                
                # Process task
                result = await self.agent.process_task(request.task_description)
                
                return TaskResponse(
                    success=True,
                    code=result["code"],
                    tests=result["tests"],
                    metadata=result["metadata"].__dict__,
                    processing_time=result.get("processing_time", 0)
                )
                
            except ValidationError as e:
                logger.warning(f"Validation error on attempt {attempt + 1}: {e}")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except ProcessingError as e:
                logger.error(f"Processing error on attempt {attempt + 1}: {e}")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                last_error = e
                break
        
        # All retries failed
        raise HTTPException(
            status_code=500, 
            detail=f"Processing failed after {max_retries} attempts: {last_error}"
        )
```

### Docker Configuration Examples

#### Optimized Dockerfile
```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create results directory
RUN mkdir -p results && chown -R appuser:appuser results

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# Expose port
EXPOSE 9001

# Default command
CMD ["python", "-m", "uvicorn", "agents.api.generator_api:app", "--host", "0.0.0.0", "--port", "9001"]
```

#### Docker Compose with Monitoring
```yaml
version: '3.8'

services:
  generator-agent:
    build: .
    ports:
      - "9001:9001"
    environment:
      - STARCODER_URL=http://starcoder-chat:8000/chat
      - AGENT_TYPE=generator
      - PORT=9001
      - HF_TOKEN=${HF_TOKEN}
    command: ["python", "-m", "uvicorn", "agents.api.generator_api:app", "--host", "0.0.0.0", "--port", "9001"]
    depends_on:
      - starcoder-chat
    restart: unless-stopped
    volumes:
      - ./results:/app/results
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  reviewer-agent:
    build: .
    ports:
      - "9002:9002"
    environment:
      - STARCODER_URL=http://starcoder-chat:8000/chat
      - AGENT_TYPE=reviewer
      - PORT=9002
      - HF_TOKEN=${HF_TOKEN}
    command: ["python", "-m", "uvicorn", "agents.api.reviewer_api:app", "--host", "0.0.0.0", "--port", "9002"]
    depends_on:
      - starcoder-chat
    restart: unless-stopped
    volumes:
      - ./results:/app/results
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Testing Examples

#### Unit Test Pattern
```python
import pytest
from unittest.mock import AsyncMock, patch
from agents.core.custom_agent import CustomAgent
from exceptions import CodeGenerationError

@pytest.fixture
def agent():
    """Create agent instance for testing."""
    return CustomAgent("http://localhost:8000/chat", "test")

@pytest.mark.asyncio
async def test_process_task_success(agent):
    """Test successful task processing."""
    # Arrange
    task_description = "Create a simple function"
    expected_code = "def simple_function(): pass"
    expected_tests = "def test_simple_function(): pass"
    
    with patch.object(agent, '_call_starcoder', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = f"```python\n{expected_code}\n```\n\n```python\n{expected_tests}\n```"
        
        # Act
        result = await agent.process_task(task_description)
        
        # Assert
        assert result["code"] == expected_code
        assert result["tests"] == expected_tests
        assert result["metadata"].complexity == "medium"
        mock_call.assert_called_once()

@pytest.mark.asyncio
async def test_process_task_validation_error(agent):
    """Test validation error handling."""
    # Act & Assert
    with pytest.raises(CodeGenerationError, match="Invalid input"):
        await agent.process_task("")

@pytest.mark.asyncio
async def test_process_task_starcoder_error(agent):
    """Test StarCoder error handling."""
    # Arrange
    with patch.object(agent, '_call_starcoder', new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = Exception("StarCoder error")
        
        # Act & Assert
        with pytest.raises(CodeGenerationError, match="Task processing failed"):
            await agent.process_task("Create a function")
```

#### Integration Test Pattern
```python
import pytest
import httpx
from fastapi.testclient import TestClient
from agents.api.generator_api import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

def test_generate_endpoint_success(client):
    """Test successful code generation."""
    # Arrange
    request_data = {
        "task_description": "Create a fibonacci function",
        "requirements": ["Include type hints", "Handle edge cases"]
    }
    
    # Act
    response = client.post("/generate", json=request_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "generated_code" in data
    assert "tests" in data
    assert "metadata" in data

def test_generate_endpoint_validation_error(client):
    """Test validation error handling."""
    # Arrange
    request_data = {
        "task_description": "",  # Invalid empty description
        "requirements": []
    }
    
    # Act
    response = client.post("/generate", json=request_data)
    
    # Assert
    assert response.status_code == 400
    assert "detail" in response.json()

def test_rate_limiting(client):
    """Test rate limiting functionality."""
    # Arrange
    request_data = {
        "task_description": "Create a function",
        "requirements": []
    }
    
    # Act - Make multiple requests
    responses = []
    for _ in range(15):  # Exceed rate limit
        response = client.post("/generate", json=request_data)
        responses.append(response)
    
    # Assert - Some requests should be rate limited
    rate_limited_responses = [r for r in responses if r.status_code == 429]
    assert len(rate_limited_responses) > 0
```

### Error Handling Examples

#### Custom Exception Hierarchy
```python
from exceptions import AgentError, ValidationError, ProcessingError

class CustomValidationError(ValidationError):
    """Custom validation error for specific use cases."""
    pass

class CustomProcessingError(ProcessingError):
    """Custom processing error with additional context."""
    
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}

# Usage in code
async def process_with_context(data: dict) -> dict:
    """Process data with context-aware error handling."""
    try:
        # Validate data
        if not data.get("required_field"):
            raise CustomValidationError(
                "Required field is missing",
                context={"field": "required_field", "data": data}
            )
        
        # Process data
        result = await complex_processing(data)
        
        return result
        
    except CustomValidationError as e:
        logger.error(f"Validation failed: {e}, context: {e.context}")
        raise
    except CustomProcessingError as e:
        logger.error(f"Processing failed: {e}, context: {e.context}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise CustomProcessingError(
            "Unexpected processing error",
            context={"original_error": str(e), "data": data}
        ) from e
```

### Performance Optimization Examples

#### Async Processing with Semaphores
```python
import asyncio
from typing import List, Dict, Any

class BatchProcessor:
    """Batch processor with concurrency control."""
    
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process batch of tasks with concurrency control."""
        async def process_single_task(task: Dict[str, Any]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    result = await self._process_task(task)
                    return {"success": True, "result": result, "task": task}
                except Exception as e:
                    return {"success": False, "error": str(e), "task": task}
        
        # Process all tasks concurrently
        results = await asyncio.gather(
            *[process_single_task(task) for task in tasks],
            return_exceptions=True
        )
        
        return results
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual task."""
        # Implementation here
        await asyncio.sleep(0.1)  # Simulate processing
        return {"processed": True, "task_id": task.get("id")}
```

#### Caching Example
```python
from functools import lru_cache
from typing import Dict, Any
import hashlib
import json

class ResultCache:
    """Simple in-memory cache for results."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
    
    def _generate_key(self, task_description: str, requirements: List[str]) -> str:
        """Generate cache key from task parameters."""
        content = f"{task_description}:{':'.join(requirements)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, task_description: str, requirements: List[str]) -> Any:
        """Get cached result."""
        key = self._generate_key(task_description, requirements)
        return self.cache.get(key)
    
    def set(self, task_description: str, requirements: List[str], result: Any) -> None:
        """Cache result."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self._generate_key(task_description, requirements)
        self.cache[key] = result
    
    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()
```

## Best Practices Summary

1. **Always use type hints** for better code clarity
2. **Implement comprehensive error handling** with custom exceptions
3. **Write tests for all functionality** including edge cases
4. **Use async/await** for I/O operations
5. **Follow security best practices** (non-root users, input validation)
6. **Implement proper logging** for debugging and monitoring
7. **Use rate limiting** to prevent abuse
8. **Cache frequently used data** for performance
9. **Monitor resource usage** and implement health checks
10. **Document everything** with clear docstrings and examples
