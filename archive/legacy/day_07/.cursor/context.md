# Project Context for AI Assistant

## Overview

The StarCoder Multi-Agent System is a sophisticated AI-powered code generation and review platform that uses a local StarCoder-7B model to provide intelligent code assistance.

## Key Components

### 1. Agents
- **CodeGeneratorAgent**: Generates Python code and tests based on task descriptions
- **CodeReviewerAgent**: Reviews generated code for quality, style, and best practices
- **BaseAgent**: Abstract base class providing common functionality

### 2. Services
- **Generator API** (Port 9001): FastAPI service for code generation
- **Reviewer API** (Port 9002): FastAPI service for code review
- **StarCoder Service** (Port 8003): Local LLM service

### 3. Communication
- **Message Schemas**: Pydantic models for structured communication
- **Agent Client**: HTTP client for inter-agent communication
- **Orchestrator**: Central coordinator for workflows

### 4. Infrastructure
- **Docker**: Containerized services with health checks
- **Docker Compose**: Multi-service orchestration
- **Monitoring**: Health checks and performance metrics

## Architecture Patterns

### Clean Architecture
- **Core**: Business logic (agents)
- **API**: Interface layer (FastAPI)
- **Communication**: Data transfer objects
- **Infrastructure**: External services (StarCoder)

### SOLID Principles
- **Single Responsibility**: Each agent has one purpose
- **Open/Closed**: Extensible through inheritance
- **Liskov Substitution**: Agents are interchangeable
- **Interface Segregation**: Focused interfaces
- **Dependency Inversion**: Depend on abstractions

## Technology Stack

### Backend
- **Python 3.11+**: Main language
- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **httpx**: HTTP client
- **asyncio**: Async programming

### AI/ML
- **StarCoder-7B**: Local language model
- **Hugging Face**: Model hosting
- **CUDA**: GPU acceleration

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **NVIDIA GPU**: Hardware acceleration

### Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async testing
- **pytest-cov**: Coverage reporting

## File Structure

```
day_07/
├── agents/                 # Agent implementations
│   ├── api/               # FastAPI services
│   └── core/              # Core agent logic
├── communication/         # Inter-agent communication
├── prompts/               # Prompt templates
├── tests/                 # Test suite
├── examples/              # Usage examples
├── notebooks/             # Jupyter tutorials
├── results/               # Workflow results
├── .cursor/               # Cursor IDE configuration
├── orchestrator.py        # Main orchestrator
├── constants.py           # Configuration constants
├── exceptions.py          # Custom exceptions
└── requirements.txt      # Dependencies
```

## Configuration

### Environment Variables
- `HF_TOKEN`: Hugging Face authentication token
- `STARCODER_URL`: StarCoder service URL
- `GENERATOR_PORT`: Generator agent port
- `REVIEWER_PORT`: Reviewer agent port

### Constants
- Rate limiting: 10 requests/minute
- Code validation: 10,000 character limit
- Timeouts: 60 seconds for HTTP requests
- Retry logic: 3 attempts with exponential backoff

## Security Features

### Docker Security
- Non-root user execution
- Minimal base images
- Health checks
- Resource limits

### API Security
- Rate limiting
- Input validation
- CORS configuration
- Error message sanitization

### Code Security
- Safe code validation (ast.parse)
- Custom exception handling
- Environment variable validation
- Secure defaults

## Performance Characteristics

### Typical Performance
- Code generation: 2-5 seconds
- Code review: 1-3 seconds
- Full workflow: 3-8 seconds
- Memory usage: 8-12GB for StarCoder

### Scalability
- Horizontal scaling via Docker
- Load balancing ready
- Resource monitoring
- Performance metrics

## Development Workflow

### Local Development
1. Start StarCoder service
2. Start agent services
3. Run tests
4. Use examples for testing

### Testing
- Unit tests for individual components
- Integration tests for workflows
- Performance tests for benchmarking
- Coverage reporting

### Deployment
- Docker containerization
- Health check monitoring
- Logging configuration
- Resource management

## Common Use Cases

### Code Generation
- Generate Python functions with tests
- Create REST API endpoints
- Implement algorithms and data structures
- Build utility functions

### Code Review
- Quality assessment
- Style compliance checking
- Best practice recommendations
- Performance analysis

### Batch Processing
- Process multiple tasks in parallel
- Analyze results across tasks
- Generate comprehensive reports
- Performance benchmarking

## Troubleshooting

### Common Issues
- Service connectivity problems
- Resource exhaustion
- Rate limiting
- Model loading issues

### Debugging
- Health check endpoints
- Logging and monitoring
- Performance metrics
- Error tracking

## Future Enhancements

### Planned Features
- Multi-language support
- Advanced orchestration patterns
- Real-time collaboration
- Enterprise features

### Scalability Improvements
- Kubernetes deployment
- Advanced monitoring
- Distributed processing
- Caching strategies
