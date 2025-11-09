"""Schemas for MCP-aware agent.

Following Python Zen: "Explicit is better than implicit"
and "Simple is better than complex".
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    """MCP tool metadata schema.

    Purpose:
        Represents metadata for a single MCP tool.

    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for tool inputs
    """

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="Input schema")


class AgentRequest(BaseModel):
    """Request for MCP-aware agent.

    Purpose:
        Standard request format for agent processing.

    Attributes:
        user_id: Telegram user ID
        message: User message text
        session_id: Dialog session ID
        context: Additional context
    """

    user_id: int = Field(..., description="Telegram user ID")
    message: str = Field(..., description="User message text")
    session_id: str = Field(..., description="Dialog session ID")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class AgentResponse(BaseModel):
    """Response from MCP-aware agent.

    Purpose:
        Standard response format from agent.

    Attributes:
        success: Whether request was successful
        text: Response text
        tools_used: List of tools used
        tokens_used: Total tokens used
        error: Error message if failed
        reasoning: Report about agent's reasoning and tool calls
    """

    success: bool = Field(..., description="Whether request was successful")
    text: str = Field(..., description="Response text")
    tools_used: list[str] = Field(
        default_factory=list, description="List of tools used"
    )
    tokens_used: int = Field(default=0, description="Total tokens used")
    error: str | None = Field(None, description="Error message if failed")
    reasoning: str | None = Field(
        None, description="Report about agent's reasoning and tool calls"
    )
