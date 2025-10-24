# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-01-XX

### Added
- Multi-model support (StarCoder, Mistral, Qwen, TinyLlama)
- Integration with shared SDK for unified model interface
- Model selection via API parameters (`model_name`, `reviewer_model_name`)
- Model-specific configuration and settings
- ModelClientAdapter for seamless SDK integration
- Support for different models for generation and review

### Changed
- Refactored BaseAgent to use SDK instead of direct HTTP calls
- Updated API schemas with model_name parameter
- Improved error handling with SDK exceptions
- Enhanced orchestrator to support multi-model workflows

### Improved
- Applied SOLID principles and Clean Architecture
- Eliminated code duplication through SDK integration
- Better separation of concerns
- Enhanced modularity and extensibility

## [Unreleased]

### Added
- Comprehensive documentation suite
- API documentation with OpenAPI 3.0
- Contributing guidelines
- Architecture documentation
- Deployment guide
- User guide with tutorials
- Examples directory with 6+ practical examples
- Jupyter notebooks for interactive tutorials
- Security policy documentation
- Performance benchmarks and guidelines

### Changed
- Enhanced README.md with badges, table of contents, and roadmap
- Improved docstrings with Examples and Raises sections
- Better error messages and user experience

## [1.1.0] - 2025-10-23

### Security
- **BREAKING**: Docker containers now run as non-root user (`appuser`)
- Added rate limiting protection (10 requests/minute) to all API endpoints
- Implemented comprehensive input validation with Pydantic models
- Replaced unsafe `compile()` with secure `ast.parse()` for code validation
- Added environment variable validation for required `HF_TOKEN`
- Sanitized error messages to prevent information disclosure

### Added
- Custom exception hierarchy (`CodeGenerationError`, `ValidationError`, etc.)
- Constants module with all magic numbers extracted
- Docker healthcheck for all services
- Resource limits and logging configuration in docker-compose
- `.dockerignore` file for optimized build context
- `.coveragerc` with 80% threshold requirement
- CORS middleware for API security
- Comprehensive error handling with specific exception types

### Changed
- All API endpoints now use Pydantic models instead of `Dict[str, Any]`
- Improved error handling throughout the codebase
- Enhanced Docker configuration with production-ready settings
- Updated requirements.txt with security dependencies

### Fixed
- Fixed potential security vulnerabilities in Docker containers
- Fixed input validation bypass issues
- Fixed unsafe code execution in validation functions
- Fixed missing error context in exception handling

## [1.0.0] - 2025-10-22

### Added
- **Multi-Agent System**: Complete implementation of two specialized AI agents
  - Code Generator Agent for Python code and test generation
  - Code Reviewer Agent for code quality analysis and scoring
- **StarCoder Integration**: Full integration with StarCoder-7B model
- **REST API Communication**: HTTP-based inter-agent communication
- **Docker Orchestration**: Complete containerization with docker-compose
- **Comprehensive Testing**: Unit and integration test suite
- **Results Persistence**: Automatic saving of workflow results
- **Real-time Monitoring**: Health checks and performance statistics
- **Orchestrator**: Central coordination system for agent workflows
- **Prompt Engineering**: Specialized prompts for code generation and review
- **Message Schemas**: Pydantic models for structured communication
- **Demo Scripts**: End-to-end workflow demonstrations
- **Makefile**: Convenient commands for development and deployment

### Technical Details
- **Architecture**: Clean architecture with SOLID principles
- **Language**: Python 3.11+ with full type hints
- **Framework**: FastAPI for REST APIs
- **AI Model**: StarCoder-7B (bigcode/starcoder2-7b)
- **Communication**: HTTP/REST with Pydantic validation
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest with async support and mocking
- **Documentation**: Comprehensive README with examples

### Performance
- Code generation: 2-5 seconds per function
- Code review: 1-3 seconds per review
- Full workflow: 3-8 seconds end-to-end
- Memory usage: ~8-12GB for StarCoder-7B
- Concurrent requests: Supports multiple simultaneous workflows

### API Endpoints
- **Generator Agent** (Port 9001):
  - `POST /generate` - Generate Python code and tests
  - `GET /health` - Health check
  - `GET /stats` - Performance statistics
- **Reviewer Agent** (Port 9002):
  - `POST /review` - Review generated code
  - `GET /health` - Health check
  - `GET /stats` - Performance statistics
- **StarCoder Service** (Port 8003):
  - `POST /chat` - Direct model interaction

### Project Structure
```
day_07/
├── agents/                 # Agent implementations
│   ├── api/               # FastAPI services
│   └── core/              # Core agent logic
├── communication/         # Inter-agent communication
├── prompts/               # Prompt templates
├── tests/                 # Test suite
├── results/               # Workflow results
├── orchestrator.py        # Main orchestrator
├── demo.py               # Demo script
├── docker-compose.yml    # Docker orchestration
├── Dockerfile            # Container definition
└── requirements.txt      # Dependencies
```

---

## Version History

- **1.1.0**: Security improvements and production readiness
- **1.0.0**: Initial release with complete multi-agent system

## Migration Guide

### From 1.0.0 to 1.1.0

#### Breaking Changes
- **Docker Security**: Containers now run as non-root user
  - If you have custom Docker configurations, update them to use `appuser`
  - Volume mounts may need permission adjustments

#### New Features
- **Rate Limiting**: API endpoints now have rate limits
  - Default: 10 requests per minute
  - Adjust via `RATE_LIMIT_PER_MINUTE` constant if needed

- **Input Validation**: All endpoints now use Pydantic models
  - Code input limited to 10,000 characters
  - Feedback limited to 5,000 characters
  - Automatic validation and error responses

#### Environment Variables
- **Required**: `HF_TOKEN` is now mandatory
  - Add to your environment or docker-compose.yml
  - System will fail to start without it

#### API Changes
- **New Endpoints**:
  - `POST /refine` - Code refinement based on feedback
  - `POST /validate` - Code validation for basic issues

- **Enhanced Responses**: All responses now include better error handling

#### Docker Changes
- **Health Checks**: All services now have health checks
- **Resource Limits**: CPU and memory limits configured
- **Logging**: Structured logging with rotation

### Upgrade Instructions

1. **Update Environment Variables**:
   ```bash
   export HF_TOKEN="your_huggingface_token"
   ```

2. **Update Docker Compose**:
   ```bash
   docker-compose down
   docker-compose pull
   docker-compose up -d
   ```

3. **Verify Health**:
   ```bash
   curl http://localhost:9001/health
   curl http://localhost:9002/health
   ```

4. **Test New Features**:
   ```bash
   # Test rate limiting
   for i in {1..15}; do curl -X POST http://localhost:9001/generate -d '{"task_description":"test"}'; done
   
   # Test new endpoints
   curl -X POST http://localhost:9001/validate -d '{"code":"def test(): pass"}'
   ```

## Support

For questions about version upgrades or migration issues:
- Check the troubleshooting section in README.md
- Review the DEPLOYMENT.md guide
- Open an issue in the project repository

## Future Releases

### Planned for 1.2.0
- Kubernetes deployment manifests
- Advanced monitoring and metrics
- Multi-language support (JavaScript, TypeScript)
- Batch processing capabilities
- Advanced prompt customization

### Planned for 2.0.0
- Multi-model support (beyond StarCoder)
- Distributed agent deployment
- Advanced orchestration patterns
- Real-time collaboration features
- Enterprise security features
