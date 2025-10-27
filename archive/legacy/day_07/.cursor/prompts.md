# Cursor AI Prompts and Examples

## Code Generation Prompts

### Basic Code Generation
```
Generate a Python function that [description] with the following requirements:
- Include type hints
- Add comprehensive docstring
- Handle edge cases
- Write unit tests
- Follow PEP 8 style
```

### API Endpoint Generation
```
Create a FastAPI endpoint for [functionality] with:
- Pydantic request/response models
- Proper error handling
- Rate limiting
- Input validation
- Comprehensive documentation
```

### Algorithm Implementation
```
Implement [algorithm name] in Python with:
- Efficient time complexity
- Clear variable names
- Type hints
- Docstring with complexity analysis
- Unit tests covering edge cases
```

## Code Review Prompts

### Quality Review
```
Review this code for:
- PEP 8 compliance
- Type hint usage
- Error handling
- Performance optimization
- Security considerations
- Test coverage
```

### Refactoring Suggestions
```
Analyze this code and suggest improvements for:
- Code readability
- Performance optimization
- Error handling
- Type safety
- Test coverage
- Documentation
```

## Architecture Prompts

### Design Patterns
```
Design a [component] using [pattern] that:
- Follows SOLID principles
- Is easily testable
- Has clear separation of concerns
- Includes proper error handling
- Is extensible for future changes
```

### System Integration
```
Integrate [component A] with [component B] ensuring:
- Proper error handling
- Async communication
- Rate limiting
- Monitoring and logging
- Graceful degradation
```

## Documentation Prompts

### API Documentation
```
Create comprehensive API documentation for [endpoint] including:
- Request/response schemas
- Error codes and messages
- Usage examples
- Rate limiting information
- Authentication requirements
```

### User Guide
```
Write a user guide for [feature] covering:
- Prerequisites
- Step-by-step instructions
- Code examples
- Troubleshooting
- Best practices
```

## Testing Prompts

### Unit Test Generation
```
Generate comprehensive unit tests for [function] covering:
- Happy path scenarios
- Edge cases
- Error conditions
- Type validation
- Performance requirements
```

### Integration Test Creation
```
Create integration tests for [workflow] that:
- Test end-to-end functionality
- Mock external dependencies
- Verify error handling
- Check performance requirements
- Validate data flow
```

## Performance Optimization Prompts

### Code Optimization
```
Optimize this code for:
- Better performance
- Lower memory usage
- Improved readability
- Better error handling
- Enhanced maintainability
```

### System Performance
```
Analyze and improve system performance by:
- Identifying bottlenecks
- Optimizing database queries
- Implementing caching
- Improving async handling
- Adding monitoring
```

## Security Prompts

### Security Review
```
Review this code for security issues:
- Input validation
- Authentication/authorization
- Data sanitization
- Error message security
- Dependency vulnerabilities
```

### Security Implementation
```
Implement security measures for [component]:
- Input validation
- Rate limiting
- Error handling
- Logging security events
- Secure defaults
```

## Docker and Deployment Prompts

### Container Configuration
```
Create a Dockerfile for [service] with:
- Minimal base image
- Non-root user
- Health checks
- Security best practices
- Optimized layers
```

### Deployment Configuration
```
Create deployment configuration with:
- Resource limits
- Health checks
- Logging configuration
- Environment variables
- Scaling policies
```

## Examples and Patterns

### Agent Implementation Pattern
```python
class CustomAgent(BaseAgent):
    """Custom agent for specific functionality."""
    
    def __init__(self, starcoder_url: str, agent_type: str):
        super().__init__(starcoder_url, agent_type)
    
    async def process(self, request: Request) -> Response:
        """Process request with proper error handling."""
        try:
            # Validate input
            self._validate_request(request)
            
            # Process with StarCoder
            result = await self._call_starcoder(request.prompt)
            
            # Parse and validate result
            return self._parse_response(result)
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise
        except StarCoderError as e:
            logger.error(f"StarCoder error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise CustomError("Processing failed") from e
```

### API Endpoint Pattern
```python
@app.post("/endpoint", response_model=ResponseModel)
@limiter.limit("10/minute")
async def endpoint(request: RequestModel) -> ResponseModel:
    """Endpoint with comprehensive error handling."""
    try:
        # Validate request
        if not request.is_valid():
            raise ValidationError("Invalid request data")
        
        # Process request
        result = await process_request(request)
        
        # Return response
        return ResponseModel(
            success=True,
            data=result,
            timestamp=datetime.now()
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ProcessingError as e:
        raise HTTPException(status_code=500, detail="Processing failed")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
```

### Test Pattern
```python
@pytest.mark.asyncio
async def test_function():
    """Test function with comprehensive coverage."""
    # Arrange
    test_data = create_test_data()
    expected_result = create_expected_result()
    
    # Act
    result = await function_under_test(test_data)
    
    # Assert
    assert result == expected_result
    assert isinstance(result, ExpectedType)
    assert result.is_valid()
```

## Best Practices

### Prompt Engineering
1. **Be specific**: Include detailed requirements
2. **Provide context**: Use `@context.md` for project information
3. **Include examples**: Reference `@examples.md` for patterns
4. **Iterate**: Refine prompts based on results
5. **Test**: Always test AI-generated code

### Code Quality
1. **Follow standards**: Use `@rules.md` for consistency
2. **Write tests**: Generate tests for all code
3. **Document**: Include comprehensive docstrings
4. **Review**: Use `@ai-reviewer.mdc` for quality checks
5. **Optimize**: Consider performance and security

### Collaboration
1. **Share context**: Use project context files
2. **Document decisions**: Explain architectural choices
3. **Review changes**: Use AI for code review
4. **Maintain standards**: Follow established patterns
5. **Iterate**: Continuously improve based on feedback
