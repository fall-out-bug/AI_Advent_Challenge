"""Pydantic models for MCP tool responses."""
from typing import List, Optional

from pydantic import BaseModel, Field


class MCPToolResponse(BaseModel):
    """Base response model for all MCP tools."""

    success: bool = Field(description="Whether the operation succeeded")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class ModelInfo(BaseModel):
    """Information about a single model."""

    name: str = Field(description="Model identifier")
    display_name: str = Field(description="Human-readable model name")
    description: str = Field(description="Model description")


class LocalModelInfo(ModelInfo):
    """Information about a local model."""

    port: Optional[int] = Field(None, description="Model server port")


class ApiModelInfo(ModelInfo):
    """Information about an API model."""

    provider: str = Field(description="API provider name")


class ModelListResponse(MCPToolResponse):
    """Response from list_models tool."""

    local_models: List[LocalModelInfo] = Field(default_factory=list)
    api_models: List[ApiModelInfo] = Field(default_factory=list)


class ModelAvailabilityResponse(MCPToolResponse):
    """Response from check_model tool."""

    available: bool = Field(description="Whether the model is available")


class Metadata(BaseModel):
    """Common metadata for agent responses."""

    model_used: str = Field(description="Model that was used")
    complexity: Optional[str] = Field(None, description="Estimated complexity")
    lines_of_code: Optional[int] = Field(None, description="Lines of code generated")


class CodeGenerationResponse(MCPToolResponse):
    """Response from generate_code tool."""

    code: str = Field(default="", description="Generated code")
    tests: str = Field(default="", description="Generated tests")
    metadata: Optional[Metadata] = Field(None, description="Generation metadata")


class CodeReviewResponse(MCPToolResponse):
    """Response from review_code tool."""

    quality_score: int = Field(0, description="Code quality score (0-10)")
    issues: List[str] = Field(default_factory=list, description="List of issues found")
    recommendations: List[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )
    review: str = Field(default="", description="Review text")
    metadata: Optional[Metadata] = Field(None, description="Review metadata")


class GenerationResult(BaseModel):
    """Result from code generation phase."""

    code: str = Field(description="Generated code")
    tests: str = Field(description="Generated tests")


class ReviewResult(BaseModel):
    """Result from code review phase."""

    score: int = Field(description="Quality score (0-10)")
    issues: List[str] = Field(default_factory=list, description="Issues found")
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations"
    )


class OrchestrationResponse(MCPToolResponse):
    """Response from generate_and_review tool."""

    generation: GenerationResult = Field(description="Code generation results")
    review: ReviewResult = Field(description="Code review results")
    workflow_time: float = Field(description="Total workflow time in seconds")


class TokenCountResponse(MCPToolResponse):
    """Response from count_tokens tool."""

    count: int = Field(description="Number of tokens")
