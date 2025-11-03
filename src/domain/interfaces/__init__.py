"""Domain interfaces module.

Provides protocol definitions for external dependencies.
Following Clean Architecture: domain defines interfaces,
infrastructure implements them.
"""

from src.domain.interfaces.tool_client import ToolClientProtocol
from src.domain.interfaces.llm_client import LLMClientProtocol
from src.domain.interfaces.config_provider import ConfigProviderProtocol

__all__ = [
    "ToolClientProtocol",
    "LLMClientProtocol",
    "ConfigProviderProtocol",
]

