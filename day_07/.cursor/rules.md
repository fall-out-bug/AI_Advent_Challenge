# Cursor Rules for StarCoder Multi-Agent System

## Project Context

This is a multi-agent AI system using StarCoder-7B for code generation and review. The system consists of:

- **Code Generator Agent**: Generates Python code and tests
- **Code Reviewer Agent**: Reviews code quality and provides feedback
- **Orchestrator**: Coordinates agent workflows
- **StarCoder Service**: Local LLM for AI processing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Generator     │    │    Reviewer     │    │   StarCoder     │
│   Agent         │◄──►│    Agent        │◄──►│   Service       │
│   (Port 9001)   │    │   (Port 9002)   │    │   (Port 8003)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │   (Coordinator) │
                    └─────────────────┘
```

## Code Standards

### Python Style
- Follow PEP 8 with 100-character line limit
- Use type hints for all functions
- Write comprehensive docstrings (Google style)
- Use meaningful variable names
- Keep functions under 15 lines when possible

### Error Handling
- Use custom exceptions from `exceptions.py`
- Always handle specific exception types
- Provide meaningful error messages
- Log errors for debugging

### Testing
- Write unit tests for all functions
- Use pytest with async support
- Mock external dependencies
- Aim for 80%+ test coverage

## AI Assistant Guidelines

### Code Generation
- Generate production-ready code
- Include comprehensive error handling
- Add type hints and docstrings
- Write corresponding unit tests
- Follow the project's architecture patterns

### Code Review
- Check for PEP 8 compliance
- Verify error handling
- Ensure type hints are present
- Validate test coverage
- Suggest improvements

### Documentation
- Write clear, comprehensive docstrings
- Include examples in documentation
- Update API documentation
- Create user guides and tutorials

## Common Patterns

### Agent Implementation
```python
class CustomAgent(BaseAgent):
    """Custom agent implementation."""
    
    def __init__(self, starcoder_url: str, agent_type: str):
        super().__init__(starcoder_url, agent_type)
    
    async def process(self, request: Request) -> Response:
        """Process request with proper error handling."""
        try:
            # Implementation
            pass
        except SpecificError as e:
            logger.error(f"Specific error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise CustomError("Unexpected error occurred") from e
```

### API Endpoints
```python
@app.post("/endpoint", response_model=ResponseModel)
@limiter.limit("10/minute")
async def endpoint(request: RequestModel) -> ResponseModel:
    """Endpoint with rate limiting and validation."""
    try:
        # Implementation
        pass
    except ValidationError as e:
        raise HTTPException(status_code=400, detail="Invalid input")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")
```

### Docker Configuration
```dockerfile
FROM python:3.11-slim

# Security: non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code and set ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1
```

## Security Considerations

- Always use non-root users in Docker
- Validate all inputs with Pydantic
- Implement rate limiting
- Sanitize error messages
- Use environment variables for secrets
- Enable CORS properly

## Performance Guidelines

- Use async/await for I/O operations
- Implement connection pooling
- Cache frequently used data
- Monitor resource usage
- Optimize database queries
- Use appropriate data structures

## Testing Standards

- Write unit tests for all functions
- Use integration tests for workflows
- Mock external dependencies
- Test error conditions
- Verify performance requirements
- Maintain test coverage above 80%

## Documentation Requirements

- Write comprehensive docstrings
- Include examples in documentation
- Update API documentation
- Create user guides
- Document configuration options
- Provide troubleshooting guides
