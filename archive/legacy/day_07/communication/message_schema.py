"""Pydantic schemas for agent communication."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskMetadata(BaseModel):
    """Metadata about the generated code."""

    complexity: str = Field(description="Complexity level (low/medium/high)")
    lines_of_code: int = Field(description="Number of lines in generated code")
    estimated_time: Optional[str] = Field(None, description="Estimated execution time")
    dependencies: List[str] = Field(
        default_factory=list, description="Required dependencies"
    )


class CodeGenerationRequest(BaseModel):
    """Request for code generation."""

    task_description: str = Field(description="Description of the task to implement")
    language: str = Field(default="python", description="Programming language")
    requirements: List[str] = Field(
        default_factory=list, description="Additional requirements"
    )
    max_tokens: int = Field(default=1000, description="Maximum tokens for generation")
    model_name: str = Field(default="starcoder", description="Model to use")


class CodeGenerationResponse(BaseModel):
    """Response from code generator agent."""

    task_description: str = Field(description="Original task description")
    generated_code: str = Field(description="Generated Python code")
    tests: str = Field(description="Generated unit tests")
    metadata: TaskMetadata = Field(description="Code metadata")
    generation_time: datetime = Field(default_factory=datetime.now)
    tokens_used: int = Field(description="Number of tokens used")


class CodeReviewRequest(BaseModel):
    """Request for code review."""

    task_description: str = Field(description="Original task description")
    generated_code: str = Field(description="Code to review")
    tests: str = Field(description="Tests to review")
    metadata: TaskMetadata = Field(description="Code metadata")


class CodeQualityMetrics(BaseModel):
    """Code quality assessment metrics."""

    pep8_compliance: bool = Field(description="Whether code follows PEP8")
    pep8_score: float = Field(ge=0, le=10, description="PEP8 compliance score (0-10)")
    has_docstrings: bool = Field(description="Whether code has docstrings")
    has_type_hints: bool = Field(description="Whether code has type hints")
    test_coverage: str = Field(description="Test coverage assessment")
    complexity_score: float = Field(ge=0, le=10, description="Code complexity score")


class CodeReviewResponse(BaseModel):
    """Response from code reviewer agent."""

    code_quality_score: float = Field(
        ge=0, le=10, description="Overall code quality score"
    )
    metrics: CodeQualityMetrics = Field(description="Detailed quality metrics")
    issues: List[str] = Field(description="List of identified issues")
    recommendations: List[str] = Field(
        description="List of improvement recommendations"
    )
    review_time: datetime = Field(default_factory=datetime.now)
    tokens_used: int = Field(description="Number of tokens used")


class AgentHealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Agent status (healthy/unhealthy)")
    agent_type: str = Field(description="Type of agent (generator/reviewer)")
    uptime: float = Field(description="Agent uptime in seconds")
    last_request: Optional[datetime] = Field(None, description="Last request timestamp")


class AgentStatsResponse(BaseModel):
    """Agent statistics response."""

    total_requests: int = Field(description="Total number of requests processed")
    successful_requests: int = Field(description="Number of successful requests")
    failed_requests: int = Field(description="Number of failed requests")
    average_response_time: float = Field(description="Average response time in seconds")
    total_tokens_used: int = Field(description="Total tokens consumed")


class OrchestratorRequest(BaseModel):
    """Request to orchestrator for full workflow."""

    task_description: str = Field(description="Task to implement")
    language: str = Field(default="python", description="Programming language")
    requirements: List[str] = Field(
        default_factory=list, description="Additional requirements"
    )
    model_name: str = Field(
        default="starcoder", description="Model to use for generation"
    )
    reviewer_model_name: Optional[str] = Field(
        default=None,
        description="Model to use for review (defaults to same as generation)",
    )


class RefineRequest(BaseModel):
    """Request for code refinement."""

    code: str = Field(max_length=10000, description="Code to refine")
    feedback: str = Field(max_length=5000, description="Feedback to incorporate")


class ValidateRequest(BaseModel):
    """Request for code validation."""

    code: str = Field(max_length=10000, description="Code to validate")


class RefineResponse(BaseModel):
    """Response from code refinement."""

    refined_code: str = Field(description="Refined code")


class ValidateResponse(BaseModel):
    """Response from code validation."""

    valid: bool = Field(description="Whether code is valid")
    issues: List[str] = Field(description="List of validation issues")
    issue_count: int = Field(description="Number of issues found")


class OrchestratorResponse(BaseModel):
    """Response from orchestrator with complete workflow results."""

    task_description: str = Field(description="Original task")
    generation_result: Optional[CodeGenerationResponse] = Field(
        None, description="Code generation results"
    )
    review_result: Optional[CodeReviewResponse] = Field(
        None, description="Code review results"
    )
    workflow_time: float = Field(description="Total workflow time in seconds")
    success: bool = Field(description="Whether workflow completed successfully")
    error_message: Optional[str] = Field(None, description="Error message if failed")
