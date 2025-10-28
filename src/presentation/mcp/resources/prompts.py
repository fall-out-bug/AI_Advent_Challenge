"""MCP resource: Prompt templates and system prompts.

Following Python Zen: "Simple is better than complex."
"""

import json


def get_python_developer_prompt() -> str:
    """Return Python developer system prompt.
    
    Returns:
        System prompt for Python development tasks
    """
    return """You are an expert Python developer specializing in:
- Clean, Pythonic code following PEP 8
- Type hints and static typing
- Comprehensive docstrings (Google style)
- Error handling and edge cases
- Performance optimization
- Modern Python 3.10+ features
- Testing with pytest
- SOLID principles and design patterns"""


def get_architect_prompt() -> str:
    """Return software architect system prompt.
    
    Returns:
        System prompt for architectural tasks
    """
    return """You are a senior software architect focusing on:
- SOLID principles and design patterns
- Scalable system architecture
- Clean Architecture layers
- API design best practices
- Performance and security considerations
- Microservices and distributed systems
- Database design and data modeling
- Documentation and technical specifications"""


def get_technical_writer_prompt() -> str:
    """Return technical writer system prompt.
    
    Returns:
        System prompt for documentation tasks
    """
    return """You are a technical documentation specialist:
- Clear, concise technical writing
- Comprehensive API documentation
- Usage examples and tutorials
- Architecture diagrams
- Troubleshooting guides
- User guides and README files
- Code comments and inline documentation
- Markdown and documentation standards"""


def get_coding_standards() -> str:
    """Return coding standards configuration.
    
    Returns:
        JSON configuration for coding standards
    """
    return json.dumps({
        "python": {
            "style": "pep8",
            "line_length": 100,
            "type_hints": "required",
            "docstrings": "google",
            "complexity_limit": 10,
            "max_function_length": 50
        },
        "general": {
            "indentation": "spaces",
            "spaces_per_tab": 4,
            "trailing_whitespace": False,
            "max_line_length": 100
        }
    })

