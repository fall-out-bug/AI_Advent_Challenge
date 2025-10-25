"""
Agent module for SDK.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".

This module provides a comprehensive agentic architecture for AI-powered
code generation, review, and orchestration. All agents follow the SOLID
principles and implement clean, maintainable interfaces.

Core Components:
- BaseAgent: Abstract foundation for all agents
- CodeGeneratorAgent: Specialized code generation with intelligent prompts
- CodeReviewerAgent: Quality analysis and code review capabilities
- Schemas: Pydantic models for type-safe agent communication

Usage Example:
    from shared_package.agents import CodeGeneratorAgent, AgentRequest
    from shared_package.orchestration.adapters import DirectAdapter
    
    async with UnifiedModelClient() as client:
        agent = CodeGeneratorAgent(client, adapter=DirectAdapter())
        
        request = AgentRequest(
            task_id="gen_001",
            task_type="code_generation",
            task="Create a Python function to calculate fibonacci",
            context={"language": "python", "style": "recursive"}
        )
        
        response = await agent.process(request)
        print(f"Generated: {response.result}")
"""

from .base_agent import BaseAgent
from .code_generator import CodeGeneratorAgent
from .code_reviewer import CodeReviewerAgent
from .schemas import (
    AgentRequest,
    AgentResponse,
    TaskMetadata,
    QualityMetrics
)

# Version information
__version__ = "0.2.0"
__author__ = "AI Challenge Team"

# Public API exports
__all__ = [
    # Core agent classes
    "BaseAgent",
    "CodeGeneratorAgent", 
    "CodeReviewerAgent",
    
    # Schema models
    "AgentRequest",
    "AgentResponse",
    "TaskMetadata",
    "QualityMetrics",
    
    # Version info
    "__version__",
    "__author__",
]

# Agent registry for dynamic discovery
AGENT_REGISTRY = {
    "code_generator": CodeGeneratorAgent,
    "code_reviewer": CodeReviewerAgent,
}

def get_agent_class(agent_name: str) -> type:
    """
    Get agent class by name.
    
    Args:
        agent_name: Name of the agent (e.g., "code_generator")
        
    Returns:
        Agent class
        
    Raises:
        ValueError: If agent name is not found
        
    Example:
        >>> agent_class = get_agent_class("code_generator")
        >>> agent = agent_class(client)
    """
    if agent_name not in AGENT_REGISTRY:
        available = ", ".join(AGENT_REGISTRY.keys())
        raise ValueError(f"Unknown agent '{agent_name}'. Available: {available}")
    
    return AGENT_REGISTRY[agent_name]

def list_available_agents() -> list[str]:
    """
    List all available agent names.
    
    Returns:
        List of agent names
        
    Example:
        >>> agents = list_available_agents()
        >>> print(agents)  # ['code_generator', 'code_reviewer']
    """
    return list(AGENT_REGISTRY.keys())

# Convenience functions for common operations
def create_agent(agent_name: str, client, **kwargs):
    """
    Create an agent instance by name.
    
    Args:
        agent_name: Name of the agent to create
        client: UnifiedModelClient instance
        **kwargs: Additional arguments for agent constructor
        
    Returns:
        Agent instance
        
    Raises:
        ValueError: If agent name is not found
        
    Example:
        >>> agent = create_agent("code_generator", client)
        >>> response = await agent.process(request)
    """
    agent_class = get_agent_class(agent_name)
    return agent_class(client, **kwargs)

# Add convenience functions to __all__
__all__.extend([
    "get_agent_class",
    "list_available_agents", 
    "create_agent",
    "AGENT_REGISTRY",
])
